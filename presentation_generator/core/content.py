"""
Content generation engine for presentation creation.

This module provides the ContentGenerator class that orchestrates the complete
content generation process, including slide creation and script generation
with context-aware generation, quality validation, retry logic, and error recovery.
"""

import time
from datetime import datetime
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass

from ..models.data import Slide, Presentation
from ..providers.base import LLMProvider
from ..utils.config import Config
from ..utils.exceptions import (
    ContentGenerationError,
    ProviderError,
    ValidationError,
    WorkflowError
)


@dataclass
class GenerationProgress:
    """Tracks progress during presentation generation."""
    current_step: str
    completed_steps: int
    total_steps: int
    current_slide: Optional[int] = None
    total_slides: Optional[int] = None
    start_time: Optional[datetime] = None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100
    
    @property
    def slide_progress_percentage(self) -> float:
        """Calculate slide-specific progress percentage."""
        if not self.current_slide or not self.total_slides:
            return 0.0
        return (self.current_slide / self.total_slides) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds since generation started."""
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()


class ContentGenerator:
    """
    Content generation engine for creating presentation slides and scripts.
    
    This class coordinates the content generation process:
    1. Generate slide topics from main subject
    2. Create slide content for each topic
    3. Generate narration scripts for each slide
    4. Handle errors and provide progress feedback
    5. Validate content quality throughout the process
    """
    
    def __init__(self, provider: LLMProvider, config: Config):
        """
        Initialize the content generator.
        
        Args:
            provider: Configured LLM provider instance
            config: Configuration object
        """
        self.provider = provider
        self.config = config
        self.progress_callback: Optional[Callable[[GenerationProgress], None]] = None
        self._current_progress: Optional[GenerationProgress] = None
        
        # Validate provider is ready
        if not provider.is_configured():
            raise ContentGenerationError(
                "LLM provider is not properly configured",
                provider=provider.provider_name
            )
    
    def set_progress_callback(self, callback: Callable[[GenerationProgress], None]) -> None:
        """
        Set a callback function to receive progress updates.
        
        Args:
            callback: Function that receives GenerationProgress updates
        """
        self.progress_callback = callback
    
    def generate_slides(self, topic: str) -> List[Slide]:
        """
        Generate a complete set of slides for the given topic.
        
        This is the main entry point that orchestrates the entire generation process:
        1. Validates input
        2. Generates slide topics
        3. Creates slides with content and scripts
        4. Returns structured slide data
        
        Args:
            topic: The main presentation topic
            
        Returns:
            List of Slide objects with content and scripts
            
        Raises:
            ContentGenerationError: If any step in the generation fails
            ValidationError: If input validation fails
        """
        if not topic or not topic.strip():
            raise ValidationError(
                "Topic cannot be empty",
                field="topic",
                value=topic
            )
        
        topic = topic.strip()
        
        # Initialize progress tracking
        self._current_progress = GenerationProgress(
            current_step="Initializing",
            completed_steps=0,
            total_steps=3,  # topics, slides, finalization
            start_time=datetime.now()
        )
        self._update_progress()
        
        try:
            # Step 1: Generate slide topics
            self._current_progress.current_step = "Generating slide topics"
            self._update_progress()
            
            topics = self._generate_slide_topics(topic)
            
            self._current_progress.completed_steps = 1
            self._current_progress.total_slides = len(topics)
            self._update_progress()
            
            # Step 2: Generate slides with content and scripts
            self._current_progress.current_step = "Generating slide content and scripts"
            self._update_progress()
            
            slides = self._generate_slides_with_scripts(topics, topic)
            
            self._current_progress.completed_steps = 2
            self._update_progress()
            
            # Step 3: Final validation and cleanup
            self._current_progress.current_step = "Finalizing slides"
            self._update_progress()
            
            self._validate_slide_collection(slides, topic)
            
            self._current_progress.completed_steps = 3
            self._current_progress.current_step = "Complete"
            self._update_progress()
            
            return slides
            
        except Exception as e:
            current_step = self._current_progress.current_step if self._current_progress else "unknown"
            
            if isinstance(e, (ContentGenerationError, ValidationError, ProviderError)):
                raise
            else:
                raise ContentGenerationError(
                    f"Unexpected error during content generation: {e}",
                    provider=self.provider.provider_name,
                    details=f"Failed at step: {current_step}"
                )
    
    def _generate_slide_topics(self, main_topic: str) -> List[str]:
        """
        Generate slide topics for the presentation.
        
        Args:
            main_topic: Main presentation topic
            
        Returns:
            List of slide topics
            
        Raises:
            ContentGenerationError: If topic generation fails
        """
        target_count = self.config.slide_count or 6  # Default to 6 slides
        min_slides = max(3, target_count - 2)
        max_slides = min(10, target_count + 2)
        
        prompt = f"""Generate {target_count} slide topics for a presentation about "{main_topic}".

Requirements:
- Create {min_slides}-{max_slides} distinct topics
- Each topic should be clear and specific (2-8 words)
- Topics should flow logically for a presentation
- Cover the most important aspects of {main_topic}
- Ensure topics are suitable for individual slides

Format as a numbered list, one topic per line."""
        
        try:
            response = self._make_api_call_with_retry(prompt, "slide_topic_generation")
            topics = self._parse_topic_list(response)
            
            # Validate topic count
            if len(topics) < min_slides:
                raise ContentGenerationError(
                    f"Too few topics generated: {len(topics)} < {min_slides}",
                    provider=self.provider.provider_name
                )
            
            if len(topics) > max_slides:
                topics = topics[:max_slides]  # Truncate if too many
            
            return topics
            
        except Exception as e:
            if isinstance(e, ContentGenerationError):
                raise
            raise ContentGenerationError(
                f"Failed to generate slide topics: {e}",
                provider=self.provider.provider_name
            )
    
    def _generate_slides_with_scripts(self, topics: List[str], main_topic: str) -> List[Slide]:
        """
        Generate slides with both content and scripts.
        
        Args:
            topics: List of slide topics
            main_topic: Main presentation topic for context
            
        Returns:
            List of complete Slide objects
            
        Raises:
            ContentGenerationError: If slide generation fails beyond recovery
        """
        slides = []
        failed_slides = []
        generation_context = {
            "main_topic": main_topic,
            "total_slides": len(topics),
            "generated_topics": []
        }
        
        for i, topic in enumerate(topics):
            slide_number = i + 1
            
            # Update progress
            if self._current_progress:
                self._current_progress.current_slide = slide_number
                self._current_progress.current_step = f"Processing slide {slide_number}/{len(topics)}: {topic}"
                self._update_progress()
            
            try:
                # Generate slide content
                content = self._generate_slide_content(
                    topic=topic,
                    context=generation_context,
                    slide_number=slide_number
                )
                
                # Generate narration script
                script = self._generate_slide_script(
                    topic=topic,
                    content=content,
                    context=generation_context,
                    slide_number=slide_number
                )
                
                # Validate content-script consistency
                self._validate_content_script_consistency(content, script, topic)
                
                # Create slide
                slide = Slide(
                    title=topic,
                    content=content,
                    script=script
                )
                
                slides.append(slide)
                generation_context["generated_topics"].append(topic)
                
            except Exception as e:
                failed_slides.append((slide_number, topic, str(e)))
                
                # Try fallback generation
                if self._should_continue_after_failure(failed_slides, len(topics), i):
                    try:
                        fallback_slide = self._generate_fallback_slide(
                            topic=topic,
                            context=generation_context,
                            slide_number=slide_number
                        )
                        slides.append(fallback_slide)
                        generation_context["generated_topics"].append(topic)
                    except Exception:
                        continue  # Skip this slide
                else:
                    raise ContentGenerationError(
                        f"Too many slide generation failures: {len(failed_slides)}/{len(topics)}",
                        provider=self.provider.provider_name,
                        details=f"Last error: {e}"
                    )
        
        if not slides:
            raise ContentGenerationError(
                "No slides were successfully generated",
                provider=self.provider.provider_name
            )
        
        return slides
    
    def _generate_slide_content(self, topic: str, context: Dict[str, Any], slide_number: int) -> str:
        """
        Generate content for a single slide.
        
        Args:
            topic: The slide topic
            context: Generation context
            slide_number: Position of this slide
            
        Returns:
            Generated slide content
            
        Raises:
            ContentGenerationError: If content generation fails
        """
        main_topic = context["main_topic"]
        total_slides = context["total_slides"]
        
        prompt = f"""Create slide content for: "{topic}"

Context:
- Part of presentation about "{main_topic}"
- Slide {slide_number} of {total_slides}

Requirements:
- Keep content concise and visual-friendly
- Use bullet points or short paragraphs
- Focus on key points for this specific topic
- Make it engaging and informative
- Suitable for display on a slide

Generate only the slide content."""
        
        content = self._make_api_call_with_retry(prompt, "slide_content_generation")
        
        # Validate content
        self._validate_slide_content(content, topic)
        
        return content
    
    def _generate_slide_script(self, topic: str, content: str, context: Dict[str, Any], slide_number: int) -> str:
        """
        Generate narration script for a slide.
        
        Args:
            topic: The slide topic
            content: The slide content
            context: Generation context
            slide_number: Position of this slide
            
        Returns:
            Generated narration script
            
        Raises:
            ContentGenerationError: If script generation fails
        """
        main_topic = context["main_topic"]
        total_slides = context["total_slides"]
        generated_topics = context.get("generated_topics", [])
        
        # Determine context for transitions
        previous_topic = generated_topics[-1] if generated_topics else None
        
        position_context = ""
        if slide_number == 1:
            position_context = "This is the opening slide of the presentation."
        elif slide_number == total_slides:
            position_context = "This is the concluding slide of the presentation."
        else:
            position_context = f"This is slide {slide_number} of {total_slides}."
        
        prompt = f"""Create a narration script for this slide:

Topic: {topic}
Slide Content: {content}

Context:
- Main presentation topic: {main_topic}
- {position_context}
{f"- Previous topic: {previous_topic}" if previous_topic else ""}

Requirements:
- Conversational and engaging tone
- Expand on the slide content naturally
- Include smooth transitions where appropriate
- Natural speaking rhythm
- Minimum 100 words for adequate narration

Generate only the narration script."""
        
        script = self._make_api_call_with_retry(prompt, "script_generation")
        
        # Validate script
        self._validate_slide_script(script, topic, content)
        
        return script
    
    def _make_api_call_with_retry(self, prompt: str, operation: str) -> str:
        """
        Make API call with retry logic and error handling.
        
        Args:
            prompt: The prompt to send to the LLM
            operation: Description of the operation for error reporting
            
        Returns:
            Generated content
            
        Raises:
            ContentGenerationError: If all retry attempts fail
        """
        max_retries = self.config.max_retries
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Test connection before making the call
                if not self.provider.test_connection():
                    raise ProviderError(
                        "Provider connection test failed",
                        provider=self.provider.provider_name
                    )
                
                # Make the API call
                response = self.provider.generate_content(
                    prompt=prompt,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                
                if not response or not response.strip():
                    raise ContentGenerationError(
                        f"Empty response from provider for {operation}",
                        provider=self.provider.provider_name
                    )
                
                return response.strip()
                
            except Exception as e:
                last_error = e
                
                if attempt < max_retries:
                    # Exponential backoff with jitter
                    backoff_time = min((2 ** attempt) * 1.0 + (0.1 * attempt), 30.0)
                    time.sleep(backoff_time)
                else:
                    break
        
        # All attempts failed
        if isinstance(last_error, (ProviderError, ContentGenerationError)):
            raise last_error
        else:
            raise ContentGenerationError(
                f"Failed {operation} after {max_retries + 1} attempts: {last_error}",
                provider=self.provider.provider_name,
                details=f"Max retries: {max_retries}"
            )
    
    def _parse_topic_list(self, response: str) -> List[str]:
        """
        Parse topic list from LLM response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            List of parsed topics
        """
        topics = []
        
        for line in response.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering and bullet points
            if line and (line[0].isdigit() or line.startswith(('-', '*', '•'))):
                for i, char in enumerate(line):
                    if char in ['.', ')', ' '] and i > 0:
                        line = line[i+1:].strip()
                        break
            
            if line:
                topics.append(line)
        
        return topics
    
    def _validate_slide_content(self, content: str, topic: str) -> None:
        """
        Validate slide content quality.
        
        Args:
            content: Generated slide content
            topic: The slide topic
            
        Raises:
            ValidationError: If content quality is insufficient
        """
        if not content or not content.strip():
            raise ValidationError(
                "Slide content cannot be empty",
                field="content",
                value="<empty>"
            )
        
        if len(content.strip()) < 20:
            raise ValidationError(
                f"Slide content too short: {len(content)} characters",
                field="content",
                value=str(len(content))
            )
        
        # Check for reasonable maximum length (configurable)
        max_length = getattr(self.config, 'slide_content_max_length', 1000)
        if len(content) > max_length:
            raise ValidationError(
                f"Slide content too long: {len(content)} > {max_length}",
                field="content",
                value=str(len(content))
            )
    
    def _validate_slide_script(self, script: str, topic: str, content: str) -> None:
        """
        Validate slide script quality.
        
        Args:
            script: Generated slide script
            topic: The slide topic
            content: The slide content
            
        Raises:
            ValidationError: If script quality is insufficient
        """
        if not script or not script.strip():
            raise ValidationError(
                "Slide script cannot be empty",
                field="script",
                value="<empty>"
            )
        
        word_count = len(script.split())
        if word_count < 50:
            raise ValidationError(
                f"Script too brief: {word_count} words (minimum 50)",
                field="script",
                value=str(word_count)
            )
        
        # Check for proper sentence structure
        sentences = [s.strip() for s in script.split('.') if s.strip()]
        if len(sentences) < 3:
            raise ValidationError(
                "Script needs more detailed explanation (minimum 3 sentences)",
                field="script",
                value=str(len(sentences))
            )
    
    def _validate_content_script_consistency(self, content: str, script: str, topic: str) -> None:
        """
        Validate consistency between slide content and script.
        
        Args:
            content: Slide content
            script: Slide script
            topic: Slide topic
            
        Raises:
            ValidationError: If consistency check fails
        """
        # Script should be substantially longer than content
        if len(script) < len(content) * 1.5:
            raise ValidationError(
                "Script should be more detailed than slide content",
                field="script_consistency",
                details=f"Script: {len(script)} chars, Content: {len(content)} chars"
            )
    
    def _should_continue_after_failure(self, failed_slides: List[tuple], total_slides: int, current_index: int) -> bool:
        """
        Determine if generation should continue after a slide failure.
        
        Args:
            failed_slides: List of failed slide information
            total_slides: Total number of slides to generate
            current_index: Current slide index (0-based)
            
        Returns:
            True if generation should continue with fallback
        """
        failure_rate = len(failed_slides) / (current_index + 1)
        
        # Stop if more than 50% of slides have failed
        if failure_rate > 0.5:
            return False
        
        # Stop if we have more than 3 consecutive failures
        if len(failed_slides) >= 3:
            recent_failures = [f for f in failed_slides if f[0] > current_index - 2]
            if len(recent_failures) >= 3:
                return False
        
        return True
    
    def _generate_fallback_slide(self, topic: str, context: Dict[str, Any], slide_number: int) -> Slide:
        """
        Create a fallback slide when AI generation fails.
        
        Args:
            topic: The slide topic
            context: Generation context
            slide_number: Position of this slide
            
        Returns:
            Slide object with fallback content
        """
        main_topic = context["main_topic"]
        total_slides = context["total_slides"]
        
        # Create basic slide content
        content = f"""• {topic}
• Key aspects and concepts
• Important principles
• Practical applications
• Relevance to {main_topic}"""
        
        # Create basic script
        position_text = ""
        if slide_number == 1:
            position_text = "Let's begin by exploring "
        elif slide_number == total_slides:
            position_text = "To conclude, let's examine "
        else:
            position_text = "Next, let's discuss "
        
        script = f"""{position_text}{topic}. This is an important aspect of {main_topic} that we need to understand.

When we consider {topic}, we should focus on the key concepts and principles that make it significant. This topic encompasses several important elements that contribute to our overall understanding of {main_topic}.

The practical applications and real-world relevance of {topic} help us appreciate its importance in the broader context of our discussion. Understanding these aspects will enhance our comprehension of {main_topic} and its implications."""
        
        return Slide(
            title=topic,
            content=content,
            script=script
        )
    
    def _validate_slide_collection(self, slides: List[Slide], main_topic: str) -> None:
        """
        Validate the complete collection of slides.
        
        Args:
            slides: List of generated slides
            main_topic: Main presentation topic
            
        Raises:
            ValidationError: If slide collection validation fails
        """
        if not slides:
            raise ValidationError(
                "No slides generated",
                field="slides",
                value="0"
            )
        
        if len(slides) < 3:
            raise ValidationError(
                f"Too few slides generated: {len(slides)} (minimum 3)",
                field="slides",
                value=str(len(slides))
            )
        
        # Check for duplicate titles
        titles = [slide.title.lower() for slide in slides]
        if len(set(titles)) != len(titles):
            raise ValidationError(
                "Duplicate slide titles detected",
                field="slide_titles"
            )
    
    def _update_progress(self) -> None:
        """Update progress and call progress callback if set."""
        if self.progress_callback and self._current_progress:
            try:
                self.progress_callback(self._current_progress)
            except Exception:
                # Don't let callback errors break the generation process
                pass
    
    def get_current_progress(self) -> Optional[GenerationProgress]:
        """Get the current generation progress."""
        return self._current_progress
    
    def cancel_generation(self) -> None:
        """Cancel the current generation process (placeholder for future implementation)."""
        # This is a placeholder for future cancellation support
        pass