"""
LangChain integration layer with multi-provider support.

This module provides both the legacy LangChainGeminiClient for backward compatibility
and the new UnifiedLLMClient that supports multiple LLM providers.
"""

import asyncio
import time
from typing import List, Optional, Dict, Any
from enum import Enum
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.schema.output_parser import StrOutputParser

from .llm_integration import UnifiedLLMClient
from ..utils.config import Config
from ..utils.exceptions import (
    APIConnectionError,
    ContentGenerationError,
    ConfigurationError,
    RetryExhaustedError
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


# Export the new unified client as the primary interface
LLMClient = UnifiedLLMClient


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascade failures.
    
    The circuit breaker monitors API failures and opens when failure
    threshold is exceeded, preventing further API calls for a timeout period.
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time in seconds to wait before trying again
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = CircuitBreakerState.CLOSED
        
    def can_execute(self) -> bool:
        """Check if operation can be executed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker transitioning to HALF_OPEN state")
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self) -> None:
        """Record successful operation."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            logger.info("Circuit breaker transitioning to CLOSED state")
        self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitBreakerState.OPEN:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
        
    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self.state
    
    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        logger.info("Circuit breaker manually reset to CLOSED state")


class LangChainGeminiClient:
    """
    Client for interacting with Gemini AI through LangChain.
    
    This class handles API connections, content generation, and error recovery
    for all AI-powered operations in the presentation generator.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the LangChain Gemini client.
        
        Args:
            config: Configuration object containing API settings
            
        Raises:
            ConfigurationError: If configuration is invalid
            APIConnectionError: If initial connection fails
        """
        self.config = config
        self._client: Optional[ChatGoogleGenerativeAI] = None
        self._output_parser = StrOutputParser()
        self._last_request_time = 0.0
        
        # Initialize circuit breaker
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,  # Open after 5 consecutive failures
            timeout=60.0  # Wait 60 seconds before trying again
        )
        
        # Validate configuration
        self._validate_config()
        
        # Initialize the client
        self._initialize_client()
        
        logger.info("LangChain Gemini client initialized successfully")
    
    def _validate_config(self) -> None:
        """Validate the configuration for API usage."""
        if not self.config.google_api_key:
            raise ConfigurationError("Google API key is required", "google_api_key")
        
        if not self.config.gemini_model:
            raise ConfigurationError("Gemini model name is required", "gemini_model")
        
        if self.config.max_retries < 0:
            raise ConfigurationError("Max retries must be non-negative", "max_retries")
        
        if self.config.rate_limit_delay < 0:
            raise ConfigurationError("Rate limit delay must be non-negative", "rate_limit_delay")
    
    def _initialize_client(self) -> None:
        """Initialize the ChatGoogleGenerativeAI client."""
        try:
            self._client = ChatGoogleGenerativeAI(
                model=self.config.gemini_model,
                google_api_key=self.config.google_api_key,
                temperature=0.7,  # Balanced creativity and consistency
                max_tokens=2048,  # Sufficient for slide content and scripts
                timeout=30.0,     # 30 second timeout
            )
            logger.debug(f"Initialized Gemini client with model: {self.config.gemini_model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise APIConnectionError(f"Failed to initialize Gemini client: {e}")
    
    def test_connection(self) -> bool:
        """
        Test the connection to Gemini API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            test_message = [HumanMessage(content="Hello, can you respond with 'Connection successful'?")]
            response = self._client.invoke(test_message)
            
            if response and "successful" in response.content.lower():
                logger.info("API connection test successful")
                return True
            else:
                logger.warning("API connection test returned unexpected response")
                return False
                
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False
    
    def _respect_rate_limit(self) -> None:
        """Implement rate limiting to respect API constraints."""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self.config.rate_limit_delay:
            sleep_time = self.config.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _make_api_call(self, messages: List[Any], operation: str) -> str:
        """
        Make an API call with retry logic, circuit breaker, and error handling.
        
        Args:
            messages: List of messages to send to the API
            operation: Description of the operation for logging
            
        Returns:
            Response content from the API
            
        Raises:
            RetryExhaustedError: If all retry attempts fail
            ContentGenerationError: If API returns invalid content
            APIConnectionError: If circuit breaker is open
        """
        # Check circuit breaker before attempting
        if not self._circuit_breaker.can_execute():
            raise APIConnectionError(
                f"Circuit breaker is OPEN for {operation}. Service temporarily unavailable.",
                api_name="Gemini"
            )
        
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Respect rate limiting
                self._respect_rate_limit()
                
                logger.debug(f"Making API call for {operation}, attempt {attempt + 1}")
                
                # Make the API call
                response = self._client.invoke(messages)
                
                if not response or not response.content:
                    raise ContentGenerationError(
                        f"Empty response from API for {operation}",
                        generation_step=operation,
                        retry_count=attempt
                    )
                
                content = response.content.strip()
                if not content:
                    raise ContentGenerationError(
                        f"Empty content in API response for {operation}",
                        generation_step=operation,
                        retry_count=attempt
                    )
                
                # Record success in circuit breaker
                self._circuit_breaker.record_success()
                
                logger.debug(f"API call successful for {operation}")
                return content
                
            except Exception as e:
                last_error = e
                logger.warning(f"API call failed for {operation}, attempt {attempt + 1}: {e}")
                
                # Record failure in circuit breaker
                self._circuit_breaker.record_failure()
                
                # Check if we should retry this error
                if self._should_retry_error(e, attempt) and attempt < self.config.max_retries:
                    # Check if circuit breaker opened during retries
                    if not self._circuit_breaker.can_execute():
                        logger.warning(f"Circuit breaker opened during retries for {operation}")
                        break
                    
                    # Calculate backoff time based on error type
                    backoff_time = self._calculate_backoff_time(e, attempt)
                    
                    logger.debug(f"Retrying in {backoff_time:.2f} seconds (error category: {self._categorize_error(e)})")
                    time.sleep(backoff_time)
                else:
                    break
        
        # All retries exhausted
        raise RetryExhaustedError(
            f"Failed to complete {operation} after {self.config.max_retries + 1} attempts",
            operation=operation,
            max_retries=self.config.max_retries,
            last_error=last_error
        )
    
    def generate_sub_subjects(self, subject: str) -> List[str]:
        """
        Generate a list of sub-subjects for the given main subject.
        
        Args:
            subject: The main presentation subject
            
        Returns:
            List of sub-subjects (3-8 items based on complexity)
            
        Raises:
            ContentGenerationError: If generation fails or produces invalid results
        """
        if not subject or not subject.strip():
            raise ContentGenerationError(
                "Subject cannot be empty for sub-subject generation",
                generation_step="sub_subject_generation"
            )
        
        logger.info(f"Generating sub-subjects for: {subject}")
        
        system_prompt = """You are an expert presentation designer. Your task is to break down a main subject into logical sub-subjects for a presentation.

Requirements:
- Generate between 3-8 sub-subjects based on topic complexity
- Each sub-subject should be distinct and relevant to the main topic
- Sub-subjects should follow a logical flow for presentation
- Use clear, concise titles (2-8 words each)
- Ensure comprehensive coverage of the main topic

Format your response as a numbered list, one sub-subject per line."""
        
        human_prompt = f"""Please generate sub-subjects for a presentation about: "{subject}"

Consider the complexity and scope of this topic to determine the appropriate number of sub-subjects (between 3-8). Make sure each sub-subject is:
1. Directly related to the main topic
2. Distinct from other sub-subjects
3. Suitable for a presentation slide
4. Logically ordered for flow

Provide only the numbered list of sub-subjects, nothing else."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self._make_api_call(messages, "sub_subject_generation")
            sub_subjects = self._parse_sub_subjects(response)
            
            # Validate the results
            self._validate_sub_subjects(sub_subjects, subject)
            
            logger.info(f"Generated {len(sub_subjects)} sub-subjects successfully")
            return sub_subjects
            
        except Exception as e:
            logger.error(f"Failed to generate sub-subjects: {e}")
            raise ContentGenerationError(
                f"Failed to generate sub-subjects: {e}",
                generation_step="sub_subject_generation"
            )
    
    def _parse_sub_subjects(self, response: str) -> List[str]:
        """Parse sub-subjects from API response."""
        lines = response.strip().split('\n')
        sub_subjects = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering (1., 2., etc.) and clean up
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                # Find the first space or period after numbering
                for i, char in enumerate(line):
                    if char in ['.', ')', ' '] and i > 0:
                        line = line[i+1:].strip()
                        break
            
            if line:
                sub_subjects.append(line)
        
        return sub_subjects
    
    def _validate_sub_subjects(self, sub_subjects: List[str], original_subject: str) -> None:
        """Validate generated sub-subjects."""
        if not sub_subjects:
            raise ContentGenerationError(
                "No sub-subjects were generated",
                generation_step="sub_subject_generation"
            )
        
        if len(sub_subjects) < self.config.min_sub_subjects:
            raise ContentGenerationError(
                f"Too few sub-subjects generated: {len(sub_subjects)} < {self.config.min_sub_subjects}",
                generation_step="sub_subject_generation"
            )
        
        if len(sub_subjects) > self.config.max_sub_subjects:
            raise ContentGenerationError(
                f"Too many sub-subjects generated: {len(sub_subjects)} > {self.config.max_sub_subjects}",
                generation_step="sub_subject_generation"
            )
        
        # Check for empty or very short sub-subjects
        for i, sub_subject in enumerate(sub_subjects):
            if not sub_subject.strip():
                raise ContentGenerationError(
                    f"Sub-subject {i+1} is empty",
                    generation_step="sub_subject_generation"
                )
            
            if len(sub_subject.strip()) < 3:
                raise ContentGenerationError(
                    f"Sub-subject {i+1} is too short: '{sub_subject}'",
                    generation_step="sub_subject_generation"
                )
    
    def generate_slide_content(self, sub_subject: str, context: str) -> str:
        """
        Generate slide content for a specific sub-subject.
        
        Args:
            sub_subject: The sub-subject for this slide
            context: Context about the main presentation topic
            
        Returns:
            Slide content text
            
        Raises:
            ContentGenerationError: If generation fails
        """
        if not sub_subject or not sub_subject.strip():
            raise ContentGenerationError(
                "Sub-subject cannot be empty for slide content generation",
                generation_step="slide_content_generation"
            )
        
        logger.info(f"Generating slide content for: {sub_subject}")
        
        system_prompt = f"""You are an expert presentation content creator. Your task is to create concise, engaging slide content.

Requirements:
- Keep content under {self.config.slide_text_max_length} characters
- Use bullet points or short paragraphs
- Make content presentation-appropriate (not too dense)
- Focus on key points that can be easily read and understood
- Ensure content is engaging and informative

The slide content should be suitable for visual presentation and complement a talking script."""
        
        human_prompt = f"""Create slide content for the sub-subject: "{sub_subject}"

Context: This is part of a presentation about "{context}"

Generate clear, concise slide content that:
1. Covers the key points of this sub-subject
2. Is appropriate for a presentation slide (not too text-heavy)
3. Uses bullet points or short paragraphs
4. Stays under {self.config.slide_text_max_length} characters
5. Is engaging and informative

Provide only the slide content, no additional formatting or explanations."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self._make_api_call(messages, "slide_content_generation")
            slide_content = response.strip()
            
            # Validate the content
            self._validate_slide_content(slide_content, sub_subject)
            
            logger.info(f"Generated slide content successfully for: {sub_subject}")
            return slide_content
            
        except Exception as e:
            logger.error(f"Failed to generate slide content: {e}")
            raise ContentGenerationError(
                f"Failed to generate slide content: {e}",
                generation_step="slide_content_generation"
            )
    
    def _validate_slide_content(self, content: str, sub_subject: str) -> None:
        """Validate generated slide content."""
        if not content or not content.strip():
            raise ContentGenerationError(
                "Generated slide content is empty",
                generation_step="slide_content_generation"
            )
        
        if len(content) > self.config.slide_text_max_length:
            raise ContentGenerationError(
                f"Slide content too long: {len(content)} > {self.config.slide_text_max_length}",
                generation_step="slide_content_generation"
            )
        
        # Basic content quality checks
        if len(content.strip()) < 20:
            raise ContentGenerationError(
                f"Slide content too short: '{content[:50]}...'",
                generation_step="slide_content_generation"
            )
    
    def generate_talking_script(self, slide_content: str, sub_subject: str, context: str,
                              slide_number: int = None, total_slides: int = None,
                              previous_subject: str = None, next_subject: str = None,
                              presentation_tone: str = None, previous_scripts: List[str] = None) -> str:
        """
        Generate a detailed talking script for a slide with enhanced validation and consistency.
        
        Args:
            slide_content: The content of the slide
            sub_subject: The sub-subject of the slide
            context: Context about the main presentation topic
            slide_number: Position of this slide in the presentation
            total_slides: Total number of slides in presentation
            previous_subject: Previous sub-subject for transitions
            next_subject: Next sub-subject for transitions
            presentation_tone: Overall tone to maintain consistency
            previous_scripts: List of previous scripts for style consistency
            
        Returns:
            Detailed talking script
            
        Raises:
            ContentGenerationError: If generation fails or validation fails
        """
        if not slide_content or not slide_content.strip():
            raise ContentGenerationError(
                "Slide content cannot be empty for script generation",
                generation_step="talking_script_generation"
            )
        
        if not sub_subject or not sub_subject.strip():
            raise ContentGenerationError(
                "Sub-subject cannot be empty for script generation",
                generation_step="talking_script_generation"
            )
        
        logger.info(f"Generating talking script for: {sub_subject}")
        
        # Import prompts here to avoid circular imports
        from ..prompts.script_prompts import ScriptPrompts
        
        # Determine which prompt to use based on available context
        if slide_number and total_slides and (previous_subject or next_subject):
            prompt_data = ScriptPrompts.get_generation_prompt(
                main_subject=context,
                sub_subject=sub_subject,
                slide_content=slide_content,
                slide_number=slide_number,
                total_slides=total_slides,
                previous_subject=previous_subject,
                next_subject=next_subject
            )
        elif presentation_tone and previous_scripts:
            # Analyze previous scripts for style consistency
            previous_style = self._analyze_script_style(previous_scripts) if previous_scripts else "professional"
            prompt_data = ScriptPrompts.get_consistency_prompt(
                main_subject=context,
                sub_subject=sub_subject,
                slide_content=slide_content,
                tone=presentation_tone,
                previous_style=previous_style
            )
        else:
            prompt_data = ScriptPrompts.get_generation_prompt(
                main_subject=context,
                sub_subject=sub_subject,
                slide_content=slide_content
            )
        
        messages = [
            SystemMessage(content=prompt_data["system_prompt"]),
            HumanMessage(content=prompt_data["user_prompt"])
        ]
        
        try:
            response = self._make_api_call(messages, "talking_script_generation")
            script = response.strip()
            
            # Enhanced validation with quality checks
            self._validate_talking_script_enhanced(script, sub_subject, slide_content, context)
            
            # Additional quality validation if we have context for consistency
            if previous_scripts:
                self._validate_script_consistency(script, previous_scripts, presentation_tone)
            
            logger.info(f"Generated talking script successfully for: {sub_subject}")
            return script
            
        except ContentGenerationError:
            # Re-raise content generation errors as-is
            raise
        except Exception as e:
            logger.error(f"Failed to generate talking script: {e}")
            raise ContentGenerationError(
                f"Failed to generate talking script: {e}",
                generation_step="talking_script_generation"
            )
    
    def _validate_talking_script(self, script: str, sub_subject: str) -> None:
        """Validate generated talking script (basic validation)."""
        if not script or not script.strip():
            raise ContentGenerationError(
                "Generated talking script is empty",
                generation_step="talking_script_generation"
            )
        
        if len(script) < self.config.script_min_length:
            raise ContentGenerationError(
                f"Talking script too short: {len(script)} < {self.config.script_min_length}",
                generation_step="talking_script_generation"
            )
        
        # Basic quality checks
        if script.count('.') < 2:
            raise ContentGenerationError(
                "Talking script appears to lack proper sentence structure",
                generation_step="talking_script_generation"
            )
    
    def _validate_talking_script_enhanced(self, script: str, sub_subject: str, 
                                        slide_content: str, context: str) -> None:
        """Enhanced validation for talking script quality and content."""
        # Basic validation first
        self._validate_talking_script(script, sub_subject)
        
        # Enhanced quality checks
        word_count = len(script.split())
        if word_count < 50:
            raise ContentGenerationError(
                f"Talking script too brief: {word_count} words (minimum 50 expected)",
                generation_step="talking_script_generation"
            )
        
        # Check for conversational elements
        conversational_indicators = [
            "we", "you", "let's", "now", "today", "here", "this", "that",
            "first", "next", "finally", "important", "notice", "see"
        ]
        script_lower = script.lower()
        conversational_count = sum(1 for indicator in conversational_indicators 
                                 if indicator in script_lower)
        
        if conversational_count < 3:
            raise ContentGenerationError(
                "Talking script lacks conversational tone and engagement",
                generation_step="talking_script_generation"
            )
        
        # Check for proper sentence structure
        sentences = [s.strip() for s in script.split('.') if s.strip()]
        if len(sentences) < 3:
            raise ContentGenerationError(
                "Talking script needs more detailed explanation (minimum 3 sentences)",
                generation_step="talking_script_generation"
            )
        
        # Check average sentence length (should be reasonable for speaking)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_sentence_length > 25:
            raise ContentGenerationError(
                "Talking script sentences are too long for natural speech",
                generation_step="talking_script_generation"
            )
        
        # Check for content relevance (sub-subject should be mentioned)
        if sub_subject.lower() not in script_lower and not any(
            word in script_lower for word in sub_subject.lower().split()
        ):
            raise ContentGenerationError(
                f"Talking script doesn't adequately address the sub-subject: {sub_subject}",
                generation_step="talking_script_generation"
            )
        
        # Check for expansion beyond slide content
        slide_words = set(slide_content.lower().split())
        script_words = set(script_lower.split())
        unique_script_words = script_words - slide_words
        
        if len(unique_script_words) < len(slide_words) * 0.5:
            raise ContentGenerationError(
                "Talking script doesn't sufficiently expand on slide content",
                generation_step="talking_script_generation"
            )
    
    def _validate_script_consistency(self, script: str, previous_scripts: List[str], 
                                   presentation_tone: str = None) -> None:
        """Validate script consistency with previous scripts."""
        if not previous_scripts:
            return
        
        script_lower = script.lower()
        
        # Analyze tone consistency
        formal_indicators = ["furthermore", "therefore", "consequently", "moreover", "thus"]
        casual_indicators = ["so", "well", "now", "okay", "right", "you know"]
        
        script_formal_count = sum(1 for indicator in formal_indicators if indicator in script_lower)
        script_casual_count = sum(1 for indicator in casual_indicators if indicator in script_lower)
        
        # Check previous scripts for tone
        prev_formal_total = 0
        prev_casual_total = 0
        
        for prev_script in previous_scripts[-3:]:  # Check last 3 scripts for consistency
            prev_lower = prev_script.lower()
            prev_formal_total += sum(1 for indicator in formal_indicators if indicator in prev_lower)
            prev_casual_total += sum(1 for indicator in casual_indicators if indicator in prev_lower)
        
        # Determine if there's a significant tone mismatch
        if prev_formal_total > prev_casual_total * 2 and script_casual_count > script_formal_count * 2:
            raise ContentGenerationError(
                "Talking script tone is too casual compared to previous scripts",
                generation_step="talking_script_generation"
            )
        
        if prev_casual_total > prev_formal_total * 2 and script_formal_count > script_casual_count * 2:
            raise ContentGenerationError(
                "Talking script tone is too formal compared to previous scripts",
                generation_step="talking_script_generation"
            )
    
    def _analyze_script_style(self, scripts: List[str]) -> str:
        """Analyze the style characteristics of previous scripts."""
        if not scripts:
            return "professional"
        
        combined_text = " ".join(scripts).lower()
        
        # Count style indicators
        formal_indicators = ["furthermore", "therefore", "consequently", "moreover", "thus", "indeed"]
        casual_indicators = ["so", "well", "now", "okay", "right", "you know", "let's"]
        technical_indicators = ["system", "process", "method", "approach", "implementation"]
        engaging_indicators = ["imagine", "consider", "think about", "picture", "remember"]
        
        formal_count = sum(1 for indicator in formal_indicators if indicator in combined_text)
        casual_count = sum(1 for indicator in casual_indicators if indicator in combined_text)
        technical_count = sum(1 for indicator in technical_indicators if indicator in combined_text)
        engaging_count = sum(1 for indicator in engaging_indicators if indicator in combined_text)
        
        # Determine dominant style
        style_scores = {
            "formal": formal_count,
            "casual": casual_count,
            "technical": technical_count,
            "engaging": engaging_count
        }
        
        dominant_style = max(style_scores, key=style_scores.get)
        
        # Create style description
        if style_scores[dominant_style] == 0:
            return "professional"
        
        style_descriptions = {
            "formal": "formal and structured with academic language",
            "casual": "conversational and approachable with informal language",
            "technical": "technical and detailed with specialized terminology",
            "engaging": "engaging and interactive with audience-focused language"
        }
        
        return style_descriptions.get(dominant_style, "professional")
    
    def validate_script_with_prompts(self, script: str, sub_subject: str, 
                                   slide_content: str, context: str) -> bool:
        """
        Use AI to validate script quality and provide feedback.
        
        Args:
            script: Generated script to validate
            sub_subject: The sub-subject of the slide
            slide_content: The slide content
            context: Main presentation context
            
        Returns:
            True if script is valid, False otherwise
            
        Raises:
            ContentGenerationError: If validation fails with specific issues
        """
        from ..prompts.script_prompts import ScriptPrompts
        
        try:
            validation_prompt = ScriptPrompts.get_validation_prompt(
                main_subject=context,
                sub_subject=sub_subject,
                slide_content=slide_content,
                script=script
            )
            
            messages = [
                SystemMessage(content=validation_prompt["system_prompt"]),
                HumanMessage(content=validation_prompt["user_prompt"])
            ]
            
            response = self._make_api_call(messages, "script_validation")
            response = response.strip()
            
            if response.startswith("VALID"):
                return True
            elif response.startswith("INVALID"):
                issues = response.replace("INVALID:", "").strip()
                raise ContentGenerationError(
                    f"Script validation failed: {issues}",
                    generation_step="talking_script_validation"
                )
            else:
                # Unexpected response format
                logger.warning(f"Unexpected validation response: {response}")
                return True  # Default to valid if response is unclear
                
        except ContentGenerationError:
            raise
        except Exception as e:
            logger.warning(f"Script validation failed with error: {e}")
            return True  # Default to valid if validation itself fails
    
    def validate_presentation_flow(self, all_scripts: List[Dict[str, str]], context: str) -> bool:
        """
        Validate narrative flow and consistency across all scripts.
        
        Args:
            all_scripts: List of dictionaries with 'sub_subject' and 'script' keys
            context: Main presentation context
            
        Returns:
            True if flow is coherent, False otherwise
            
        Raises:
            ContentGenerationError: If flow validation fails with specific issues
        """
        if not all_scripts or len(all_scripts) < 2:
            return True  # Can't validate flow with less than 2 scripts
        
        from ..prompts.script_prompts import ScriptPrompts
        
        try:
            flow_prompt = ScriptPrompts.get_flow_check_prompt(
                main_subject=context,
                all_scripts=all_scripts
            )
            
            messages = [
                SystemMessage(content=flow_prompt["system_prompt"]),
                HumanMessage(content=flow_prompt["user_prompt"])
            ]
            
            response = self._make_api_call(messages, "presentation_flow_validation")
            response = response.strip()
            
            if response.startswith("COHERENT"):
                return True
            elif response.startswith("INCOHERENT"):
                issues = response.replace("INCOHERENT:", "").strip()
                raise ContentGenerationError(
                    f"Presentation flow validation failed: {issues}",
                    generation_step="presentation_flow_validation"
                )
            else:
                logger.warning(f"Unexpected flow validation response: {response}")
                return True  # Default to coherent if response is unclear
                
        except ContentGenerationError:
            raise
        except Exception as e:
            logger.warning(f"Flow validation failed with error: {e}")
            return True  # Default to coherent if validation itself fails
    
    def regenerate_script_with_feedback(self, slide_content: str, sub_subject: str, 
                                      context: str, current_script: str, 
                                      issues: str) -> str:
        """
        Regenerate a talking script based on feedback about issues.
        
        Args:
            slide_content: The content of the slide
            sub_subject: The sub-subject of the slide
            context: Context about the main presentation topic
            current_script: Current script that needs improvement
            issues: Description of issues to address
            
        Returns:
            Improved talking script
            
        Raises:
            ContentGenerationError: If regeneration fails
        """
        logger.info(f"Regenerating talking script for: {sub_subject} with feedback: {issues}")
        
        from ..prompts.script_prompts import ScriptPrompts
        
        revision_prompt = ScriptPrompts.get_revision_prompt(
            main_subject=context,
            sub_subject=sub_subject,
            slide_content=slide_content,
            current_script=current_script,
            issues=issues
        )
        
        messages = [
            SystemMessage(content=revision_prompt["system_prompt"]),
            HumanMessage(content=revision_prompt["user_prompt"])
        ]
        
        try:
            response = self._make_api_call(messages, "talking_script_revision")
            revised_script = response.strip()
            
            # Validate the revised script
            self._validate_talking_script_enhanced(revised_script, sub_subject, slide_content, context)
            
            logger.info(f"Successfully regenerated talking script for: {sub_subject}")
            return revised_script
            
        except Exception as e:
            logger.error(f"Failed to regenerate talking script: {e}")
            raise ContentGenerationError(
                f"Failed to regenerate talking script: {e}",
                generation_step="talking_script_revision"
            )
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get information about the client configuration."""
        return {
            "model": self.config.gemini_model,
            "max_retries": self.config.max_retries,
            "rate_limit_delay": self.config.rate_limit_delay,
            "max_sub_subjects": self.config.max_sub_subjects,
            "min_sub_subjects": self.config.min_sub_subjects,
            "slide_text_max_length": self.config.slide_text_max_length,
            "script_min_length": self.config.script_min_length,
            "circuit_breaker_state": self._circuit_breaker.get_state().value,
            "circuit_breaker_failure_count": self._circuit_breaker.failure_count,
        }
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get detailed circuit breaker status."""
        return {
            "state": self._circuit_breaker.get_state().value,
            "failure_count": self._circuit_breaker.failure_count,
            "failure_threshold": self._circuit_breaker.failure_threshold,
            "timeout": self._circuit_breaker.timeout,
            "last_failure_time": self._circuit_breaker.last_failure_time,
            "can_execute": self._circuit_breaker.can_execute(),
        }
    
    def reset_circuit_breaker(self) -> None:
        """Reset the circuit breaker to closed state."""
        self._circuit_breaker.reset()
        logger.info("Circuit breaker has been manually reset")
    
    def _categorize_error(self, error: Exception) -> str:
        """
        Categorize errors for different recovery strategies.
        
        Args:
            error: The exception to categorize
            
        Returns:
            Error category string
        """
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "quota" in error_str:
            return "rate_limit"
        elif "timeout" in error_str or "connection" in error_str:
            return "network"
        elif "authentication" in error_str or "api key" in error_str:
            return "auth"
        elif "invalid" in error_str or "malformed" in error_str:
            return "validation"
        else:
            return "unknown"
    
    def _get_recovery_strategy(self, error_category: str, attempt: int) -> Dict[str, Any]:
        """
        Get recovery strategy based on error category.
        
        Args:
            error_category: Category of the error
            attempt: Current attempt number
            
        Returns:
            Recovery strategy configuration
        """
        strategies = {
            "rate_limit": {
                "should_retry": True,
                "backoff_multiplier": 3.0,  # Longer backoff for rate limits
                "max_attempts": self.config.max_retries,
            },
            "network": {
                "should_retry": True,
                "backoff_multiplier": 2.0,  # Standard exponential backoff
                "max_attempts": self.config.max_retries,
            },
            "auth": {
                "should_retry": False,  # Don't retry auth errors
                "backoff_multiplier": 1.0,
                "max_attempts": 1,
            },
            "validation": {
                "should_retry": attempt < 2,  # Only retry once for validation errors
                "backoff_multiplier": 1.0,
                "max_attempts": 2,
            },
            "unknown": {
                "should_retry": True,
                "backoff_multiplier": 2.0,
                "max_attempts": self.config.max_retries,
            }
        }
        
        return strategies.get(error_category, strategies["unknown"])
    
    def _should_retry_error(self, error: Exception, attempt: int) -> bool:
        """
        Determine if an error should be retried based on its type and attempt count.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-based)
            
        Returns:
            True if the error should be retried
        """
        error_category = self._categorize_error(error)
        strategy = self._get_recovery_strategy(error_category, attempt)
        
        if not strategy["should_retry"]:
            logger.debug(f"Error category '{error_category}' should not be retried")
            return False
        
        if attempt >= strategy["max_attempts"]:
            logger.debug(f"Max attempts ({strategy['max_attempts']}) reached for error category '{error_category}'")
            return False
        
        return True
    
    def _calculate_backoff_time(self, error: Exception, attempt: int) -> float:
        """
        Calculate backoff time based on error type and attempt number.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-based)
            
        Returns:
            Backoff time in seconds
        """
        error_category = self._categorize_error(error)
        strategy = self._get_recovery_strategy(error_category, attempt)
        
        base_backoff = (2 ** attempt) * self.config.rate_limit_delay
        backoff_time = base_backoff * strategy["backoff_multiplier"]
        
        # Add jitter to prevent thundering herd
        import random
        jitter = random.uniform(0.1, 0.5)
        backoff_time += jitter
        
        # Cap maximum backoff time
        max_backoff = 60.0  # 1 minute maximum
        return min(backoff_time, max_backoff)
    
    def _analyze_script_style(self, previous_scripts: List[str]) -> str:
        """
        Analyze the style of previous scripts to maintain consistency.
        
        Args:
            previous_scripts: List of previously generated scripts
            
        Returns:
            Style description for consistency
        """
        if not previous_scripts:
            return "professional"
        
        # Combine recent scripts for analysis
        combined_text = " ".join(previous_scripts[-3:]).lower()  # Last 3 scripts
        
        # Analyze tone indicators
        formal_indicators = ["furthermore", "therefore", "consequently", "moreover", "thus", "hence"]
        casual_indicators = ["so", "well", "now", "okay", "right", "you know", "let's"]
        engaging_indicators = ["we", "you", "our", "your", "together", "explore", "discover"]
        
        formal_count = sum(1 for indicator in formal_indicators if indicator in combined_text)
        casual_count = sum(1 for indicator in casual_indicators if indicator in combined_text)
        engaging_count = sum(1 for indicator in engaging_indicators if indicator in combined_text)
        
        # Determine predominant style
        if formal_count > casual_count and formal_count > engaging_count:
            return "formal"
        elif engaging_count > formal_count and engaging_count > casual_count:
            return "engaging"
        elif casual_count > formal_count:
            return "conversational"
        else:
            return "professional"