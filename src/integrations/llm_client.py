"""
Unified LLM client with multi-provider support.

Simple, clean integration supporting multiple LLM providers through LangChain.
The only differences between providers are the imports and initialization.
"""

import time
from typing import List, Optional, Dict, Any
from enum import Enum

from langchain.schema import HumanMessage, SystemMessage

from ..utils.config import Config
from ..utils.exceptions import (
    APIConnectionError,
    ContentGenerationError,
    ConfigurationError,
    RetryExhaustedError
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Simple circuit breaker to prevent cascade failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = CircuitBreakerState.CLOSED
        
    def can_execute(self) -> bool:
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self) -> None:
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
    
    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
    
    def get_state(self) -> CircuitBreakerState:
        return self.state
    
    def reset(self) -> None:
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0


class LLMClient:
    """
    Unified LLM client supporting multiple providers.
    
    The only differences between providers are imports and initialization.
    Everything else is identical thanks to LangChain's unified interface.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self._client = None
        self._last_request_time = 0.0
        self._circuit_breaker = CircuitBreaker()
        
        self._validate_config()
        self._initialize_client()
        
        logger.info(f"LLM client initialized with {config.llm_provider} provider")
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        if not self.config.llm_provider:
            raise ConfigurationError("LLM provider is required", "llm_provider")
        if not self.config.llm_model:
            raise ConfigurationError("LLM model is required", "llm_model")
    
    def _initialize_client(self) -> None:
        """Initialize the appropriate LLM client based on provider."""
        provider = self.config.llm_provider.lower()
        
        try:
            if provider == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                if not self.config.llm_api_key:
                    raise ConfigurationError("Google API key required for Gemini", "llm_api_key")
                self._client = ChatGoogleGenerativeAI(
                    model=self.config.llm_model,
                    google_api_key=self.config.llm_api_key,
                    temperature=self.config.llm_temperature,
                    max_tokens=self.config.llm_max_tokens,
                    timeout=self.config.llm_timeout
                )
            
            elif provider == "openai":
                from langchain_openai import ChatOpenAI
                if not self.config.llm_api_key:
                    raise ConfigurationError("OpenAI API key required", "llm_api_key")
                self._client = ChatOpenAI(
                    model=self.config.llm_model,
                    openai_api_key=self.config.llm_api_key,
                    temperature=self.config.llm_temperature,
                    max_tokens=self.config.llm_max_tokens,
                    timeout=self.config.llm_timeout
                )
            
            elif provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                if not self.config.llm_api_key:
                    raise ConfigurationError("Anthropic API key required", "llm_api_key")
                self._client = ChatAnthropic(
                    model=self.config.llm_model,
                    anthropic_api_key=self.config.llm_api_key,
                    temperature=self.config.llm_temperature,
                    max_tokens=self.config.llm_max_tokens,
                    timeout=self.config.llm_timeout
                )
            
            elif provider == "ollama":
                from langchain_ollama import ChatOllama
                base_url = self.config.llm_base_url or "http://localhost:11434"
                self._client = ChatOllama(
                    model=self.config.llm_model,
                    base_url=base_url,
                    temperature=self.config.llm_temperature,
                    timeout=self.config.llm_timeout
                )
            
            else:
                raise ConfigurationError(f"Unsupported provider: {provider}", "llm_provider")
                
        except ImportError as e:
            raise ConfigurationError(f"Missing package for {provider}: {e}", "llm_provider")
        except Exception as e:
            raise APIConnectionError(f"Failed to initialize {provider} client: {e}")
    
    def test_connection(self) -> bool:
        """Test connection to the LLM provider."""
        try:
            test_message = [HumanMessage(content="Hello, respond with 'Connection successful'")]
            response = self._client.invoke(test_message)
            return response and "successful" in response.content.lower()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def _respect_rate_limit(self) -> None:
        """Simple rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.config.rate_limit_delay:
            time.sleep(self.config.rate_limit_delay - time_since_last)
        self._last_request_time = time.time()
    
    def _make_api_call(self, messages: List[Any], operation: str) -> str:
        """Make API call with retry logic and circuit breaker."""
        if not self._circuit_breaker.can_execute():
            raise APIConnectionError(f"Circuit breaker open for {operation}")
        
        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                self._respect_rate_limit()
                response = self._client.invoke(messages)
                
                if not response or not response.content:
                    raise ContentGenerationError(f"Empty response for {operation}")
                
                content = response.content.strip()
                if not content:
                    raise ContentGenerationError(f"Empty content for {operation}")
                
                self._circuit_breaker.record_success()
                return content
                
            except Exception as e:
                last_error = e
                self._circuit_breaker.record_failure()
                
                if attempt < self.config.max_retries:
                    backoff = min((2 ** attempt) * 1.0, 30.0)
                    time.sleep(backoff)
                else:
                    break
        
        raise RetryExhaustedError(f"Failed {operation} after {self.config.max_retries + 1} attempts", 
                                operation=operation, max_retries=self.config.max_retries, last_error=last_error)
    
    def generate_sub_subjects(self, subject: str) -> List[str]:
        """Generate sub-subjects for presentation."""
        if not subject or not subject.strip():
            raise ContentGenerationError("Subject cannot be empty")
        
        system_prompt = """You are an expert presentation designer. Break down the main subject into 3-8 logical sub-subjects for a presentation.

Requirements:
- Generate 3-8 sub-subjects based on topic complexity
- Each sub-subject should be distinct and relevant
- Use clear, concise titles (2-8 words each)
- Ensure logical flow for presentation

Format as numbered list, one per line."""
        
        human_prompt = f"""Generate sub-subjects for: "{subject}"

Make each sub-subject:
1. Directly related to the main topic
2. Distinct from others
3. Suitable for a presentation slide
4. Logically ordered

Provide only the numbered list."""
        
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
        response = self._make_api_call(messages, "sub_subject_generation")
        
        # Parse response
        sub_subjects = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            # Remove numbering
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                for i, char in enumerate(line):
                    if char in ['.', ')', ' '] and i > 0:
                        line = line[i+1:].strip()
                        break
            if line:
                sub_subjects.append(line)
        
        # Validate
        if not sub_subjects:
            raise ContentGenerationError("No sub-subjects generated")
        if len(sub_subjects) < self.config.min_sub_subjects:
            raise ContentGenerationError(f"Too few sub-subjects: {len(sub_subjects)}")
        if len(sub_subjects) > self.config.max_sub_subjects:
            raise ContentGenerationError(f"Too many sub-subjects: {len(sub_subjects)}")
        
        return sub_subjects
    
    def generate_slide_content(self, sub_subject: str, context: str) -> str:
        """Generate slide content for sub-subject."""
        if not sub_subject or not sub_subject.strip():
            raise ContentGenerationError("Sub-subject cannot be empty")
        
        system_prompt = f"""Create concise, engaging slide content.

Requirements:
- Keep under {self.config.slide_text_max_length} characters
- Use bullet points or short paragraphs
- Focus on key points for visual presentation
- Make it engaging and informative"""
        
        human_prompt = f"""Create slide content for: "{sub_subject}"
Context: Part of presentation about "{context}"

Generate clear, concise content that:
1. Covers key points of this sub-subject
2. Is appropriate for a slide (not text-heavy)
3. Uses bullet points or short paragraphs
4. Stays under {self.config.slide_text_max_length} characters

Provide only the slide content."""
        
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
        content = self._make_api_call(messages, "slide_content_generation")
        
        # Validate
        if len(content) > self.config.slide_text_max_length:
            raise ContentGenerationError(f"Slide content too long: {len(content)}")
        if len(content.strip()) < 20:
            raise ContentGenerationError("Slide content too short")
        
        return content
    
    def generate_talking_script(self, slide_content: str, sub_subject: str, context: str,
                              slide_number: int = None, total_slides: int = None,
                              previous_subject: str = None, next_subject: str = None,
                              presentation_tone: str = None, previous_scripts: List[str] = None) -> str:
        """Generate talking script for slide."""
        if not slide_content or not slide_content.strip():
            raise ContentGenerationError("Slide content cannot be empty")
        if not sub_subject or not sub_subject.strip():
            raise ContentGenerationError("Sub-subject cannot be empty")
        
        # Build context-aware prompt
        system_prompt = """You are an expert presentation coach. Create a detailed talking script that expands on slide content.

Requirements:
- Conversational and engaging tone
- Expand beyond what's on the slide
- Include smooth transitions
- Natural speaking rhythm
- Minimum 50 words"""
        
        context_info = f"Main topic: {context}\nSub-subject: {sub_subject}\nSlide content: {slide_content}"
        
        if slide_number and total_slides:
            context_info += f"\nSlide {slide_number} of {total_slides}"
        if previous_subject:
            context_info += f"\nPrevious topic: {previous_subject}"
        if next_subject:
            context_info += f"\nNext topic: {next_subject}"
        if presentation_tone:
            context_info += f"\nTone: {presentation_tone}"
        
        human_prompt = f"""Create a talking script for this slide:

{context_info}

Generate a script that:
1. Expands on the slide content naturally
2. Uses conversational language
3. Includes smooth transitions
4. Is engaging for the audience
5. Flows well when spoken aloud

Provide only the talking script."""
        
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
        script = self._make_api_call(messages, "talking_script_generation")
        
        # Validate
        if len(script) < self.config.script_min_length:
            raise ContentGenerationError(f"Script too short: {len(script)}")
        
        word_count = len(script.split())
        if word_count < 50:
            raise ContentGenerationError(f"Script too brief: {word_count} words")
        
        return script
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get current provider information."""
        return {
            "provider": self.config.llm_provider,
            "model": self.config.llm_model,
            "circuit_breaker_state": self._circuit_breaker.get_state().value,
            "failure_count": self._circuit_breaker.failure_count
        }
    
    @staticmethod
    def get_supported_providers() -> Dict[str, Dict[str, Any]]:
        """Get information about all supported providers."""
        return {
            "gemini": {
                "name": "Google Gemini",
                "requires_api_key": True,
                "default_models": ["gemini-2.5-flash", "gemini-1.5-pro"],
                "description": "Google's Gemini AI models"
            },
            "openai": {
                "name": "OpenAI",
                "requires_api_key": True,
                "default_models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                "description": "OpenAI's GPT models"
            },
            "anthropic": {
                "name": "Anthropic Claude",
                "requires_api_key": True,
                "default_models": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                "description": "Anthropic's Claude models"
            },
            "ollama": {
                "name": "Ollama",
                "requires_api_key": False,
                "default_models": ["llama3.2", "mistral", "codellama"],
                "description": "Local LLM runner with various open-source models",
                "default_base_url": "http://localhost:11434"
            }
        }


# Backward compatibility aliases
UnifiedLLMClient = LLMClient
LangChainGeminiClient = LLMClient  # Legacy compatibility

# For main.py compatibility
class LLMProvider:
    """Simple enum-like class for provider names."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

class LLMProviderFactory:
    """Factory class for backward compatibility with main.py."""
    
    @staticmethod
    def get_provider_info():
        """Get provider info in the format expected by main.py."""
        providers = LLMClient.get_supported_providers()
        # Convert to enum-like format for main.py
        result = {}
        for key, info in providers.items():
            # Create a simple object with value attribute
            provider_obj = type('Provider', (), {'value': key})()
            result[provider_obj] = info
        return result
    
    @staticmethod
    def create_provider(config):
        """Create provider - just return LLMClient for compatibility."""
        return LLMClient(config)

class LLMConfig:
    """Simple config class for compatibility."""
    def __init__(self, provider, model, api_key=None, **kwargs):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        for k, v in kwargs.items():
            setattr(self, k, v)