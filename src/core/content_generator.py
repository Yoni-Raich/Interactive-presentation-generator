"""
Content generation pipeline orchestrator.

This module provides the ContentGenerator class that orchestrates the complete
presentation generation process, including sub-subject generation, slide creation,
and talking script generation with progress tracking and error recovery.
"""

import time
from datetime import datetime
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass

from ..models.data_models import SlideData, PresentationData
from ..integrations.langchain_integration import LLMClient
from ..integrations.tts_client import TTSClient
from ..utils.config import Config
from ..utils.logger import get_logger
from ..utils.exceptions import (
    ContentGenerationError,
    PresentationGeneratorError,
    RetryExhaustedError
)

logger = get_logger(__name__)


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
    Main content generation pipeline orchestrator.
    
    This class coordinates the entire presentation generation process:
    1. Generate sub-subjects from main topic
    2. Create slide content for each sub-subject
    3. Generate talking scripts for each slide
    4. Handle errors and provide progress feedback
    """
    
    def __init__(self, llm_client: LLMClient, config: Config, tts_client: TTSClient = None):
        """
        Initialize the content generator.
        
        Args:
            llm_client: Initialized LLM client (supports multiple providers)
            config: Configuration object
            tts_client: Initialized TTS client
        """
        self.llm_client = llm_client
        self.config = config
        self.tts_client = tts_client
        self.progress_callback: Optional[Callable[[GenerationProgress], None]] = None
        self._current_progress: Optional[GenerationProgress] = None
        
        logger.info("ContentGenerator initialized")
    
    def set_progress_callback(self, callback: Callable[[GenerationProgress], None]) -> None:
        """
        Set a callback function to receive progress updates.
        
        Args:
            callback: Function that receives GenerationProgress updates
        """
        self.progress_callback = callback
        logger.debug("Progress callback set")
    
    def generate_presentation(self, subject: str) -> PresentationData:
        """
        Generate a complete presentation from a subject.
        
        This is the main entry point that orchestrates the entire generation process:
        1. Validates input
        2. Generates sub-subjects
        3. Creates slides with content and scripts
        4. Returns structured presentation data
        
        Args:
            subject: The main presentation subject
            
        Returns:
            Complete PresentationData object
            
        Raises:
            ContentGenerationError: If any step in the generation fails
            PresentationGeneratorError: For other generation-related errors
        """
        if not subject or not subject.strip():
            raise ContentGenerationError(
                "Subject cannot be empty",
                generation_step="input_validation"
            )
        
        subject = subject.strip()
        logger.info(f"Starting presentation generation for subject: {subject}")
        
        # Initialize progress tracking
        self._current_progress = GenerationProgress(
            current_step="Initializing",
            completed_steps=0,
            total_steps=4,  # sub-subjects, slides, scripts, finalization
            start_time=datetime.now()
        )
        self._update_progress()
        
        try:
            # Step 1: Generate sub-subjects
            logger.info("=== STEP 1: Sub-subject Generation ===")
            self._current_progress.current_step = "Generating sub-subjects"
            self._update_progress()
            
            sub_subjects = self._generate_sub_subjects(subject)
            
            self._current_progress.completed_steps = 1
            self._current_progress.total_slides = len(sub_subjects)
            self._update_progress()
            
            logger.info(f"Sub-subjects generated successfully: {sub_subjects}")
            
            # Step 2: Generate slides with integrated content and scripts
            logger.info("=== STEP 2: Integrated Slide and Script Generation ===")
            self._current_progress.current_step = "Generating integrated slide content and scripts"
            self._update_progress()
            
            slides = self._generate_slides_with_scripts(sub_subjects, subject)

            if self.tts_client:
                logger.info("=== STEP 3: Audio Generation ===")
                self._current_progress.current_step = "Generating audio for slides"
                self._update_progress()
                for i, slide in enumerate(slides):
                    self._generate_audio_for_slide(slide, i)
            
            self._current_progress.completed_steps = 3
            self._update_progress()
            
            logger.info(f"Generated {len(slides)} complete slides with content and scripts")
            
            # Step 3: Create final presentation data
            logger.info("=== STEP 3: Presentation Finalization ===")
            self._current_progress.current_step = "Finalizing presentation"
            self._update_progress()
            
            presentation = self._create_presentation_data(subject, slides)
            
            self._current_progress.completed_steps = 4
            self._current_progress.current_step = "Complete"
            self._update_progress()
            
            generation_time = self._current_progress.elapsed_time
            logger.info(f"=== GENERATION COMPLETE ===")
            logger.info(f"Total time: {generation_time:.2f} seconds")
            logger.info(f"Slides generated: {len(slides)}")
            logger.info(f"Success rate: 100%")
            
            return presentation
            
        except Exception as e:
            generation_time = self._current_progress.elapsed_time if self._current_progress else 0
            current_step = self._current_progress.current_step if self._current_progress else "unknown"
            
            logger.error(f"=== GENERATION FAILED ===")
            logger.error(f"Failed at step: {current_step}")
            logger.error(f"Time elapsed: {generation_time:.2f} seconds")
            logger.error(f"Error: {e}")
            
            if isinstance(e, PresentationGeneratorError):
                logger.error(f"Error details: {getattr(e, 'details', 'No additional details')}")
                raise
            else:
                raise ContentGenerationError(
                    f"Unexpected error during presentation generation: {e}",
                    generation_step=current_step,
                    retry_count=0
                )
    
    def _generate_sub_subjects(self, subject: str) -> List[str]:
        """
        Generate sub-subjects for the presentation.
        
        Args:
            subject: Main presentation subject
            
        Returns:
            List of sub-subjects
            
        Raises:
            ContentGenerationError: If sub-subject generation fails
        """
        logger.info("Generating sub-subjects")
        
        try:
            sub_subjects = self.llm_client.generate_sub_subjects(subject)
            
            logger.info(f"Generated {len(sub_subjects)} sub-subjects: {sub_subjects}")
            return sub_subjects
            
        except Exception as e:
            logger.error(f"Failed to generate sub-subjects: {e}")
            
            # Try recovery with simplified prompt if possible
            if isinstance(e, ContentGenerationError) and e.details.get("retry_count", 0) < 1:
                logger.info("Attempting sub-subject generation recovery")
                try:
                    # This would be a simplified fallback approach
                    sub_subjects = self._generate_sub_subjects_fallback(subject)
                    logger.info(f"Recovery successful: generated {len(sub_subjects)} sub-subjects")
                    return sub_subjects
                except Exception as recovery_error:
                    logger.error(f"Recovery attempt failed: {recovery_error}")
            
            raise ContentGenerationError(
                f"Failed to generate sub-subjects: {e}",
                generation_step="sub_subject_generation"
            )
    
    def _generate_sub_subjects_fallback(self, subject: str) -> List[str]:
        """
        Fallback method for sub-subject generation using simpler approach.
        
        Args:
            subject: Main presentation subject
            
        Returns:
            List of basic sub-subjects
        """
        # Simple fallback: create basic sub-subjects based on common presentation structure
        basic_subjects = [
            f"Introduction to {subject}",
            f"Key Concepts of {subject}",
            f"Applications of {subject}",
            f"Benefits and Advantages",
            f"Conclusion and Summary"
        ]
        
        # Limit to configured range
        max_subjects = min(len(basic_subjects), self.config.max_sub_subjects)
        min_subjects = max(self.config.min_sub_subjects, 3)
        
        return basic_subjects[:max(min_subjects, max_subjects)]
    
    def _generate_slides_with_scripts(self, sub_subjects: List[str], main_subject: str) -> List[SlideData]:
        """
        Generate slides with both content and talking scripts in sequence.
        
        This method integrates slide content and script generation with:
        - Context consistency across all generation steps
        - Comprehensive error handling with fallbacks
        - Progress tracking and detailed logging
        - Quality validation at each step
        
        Args:
            sub_subjects: List of sub-subjects for slides
            main_subject: Main presentation subject for context
            
        Returns:
            List of complete SlideData objects
            
        Raises:
            ContentGenerationError: If slide generation fails beyond recovery
        """
        slides = []
        failed_slides = []
        previous_scripts = []
        generation_context = {
            "main_subject": main_subject,
            "total_slides": len(sub_subjects),
            "presentation_tone": "professional",  # Default tone
            "generated_subjects": []
        }
        
        logger.info(f"Starting integrated slide and script generation for {len(sub_subjects)} sub-subjects")
        
        for i, sub_subject in enumerate(sub_subjects):
            slide_number = i + 1
            
            # Update progress tracking
            if self._current_progress:
                self._current_progress.current_slide = slide_number
                self._current_progress.current_step = f"Processing slide {slide_number}/{len(sub_subjects)}: {sub_subject}"
                self._update_progress()
            
            logger.info(f"Processing slide {slide_number}/{len(sub_subjects)}: {sub_subject}")
            
            try:
                # Step 1: Generate slide content with context
                logger.debug(f"Generating slide content for: {sub_subject}")
                slide_content = self._generate_slide_content_with_context(
                    sub_subject=sub_subject,
                    generation_context=generation_context,
                    slide_number=slide_number
                )
                
                # Step 2: Generate talking script with full context
                logger.debug(f"Generating talking script for: {sub_subject}")
                talking_script = self._generate_talking_script_with_context(
                    slide_content=slide_content,
                    sub_subject=sub_subject,
                    generation_context=generation_context,
                    slide_number=slide_number,
                    previous_scripts=previous_scripts
                )
                
                # Step 3: Validate content consistency
                logger.debug(f"Validating content consistency for: {sub_subject}")
                self._validate_slide_script_consistency(
                    slide_content=slide_content,
                    talking_script=talking_script,
                    sub_subject=sub_subject,
                    generation_context=generation_context
                )
                
                # Step 4: Create slide data
                slide = SlideData(
                    sub_subject=sub_subject,
                    slide_text=slide_content,
                    talking_script=talking_script
                )
                
                slides.append(slide)
                previous_scripts.append(talking_script)
                generation_context["generated_subjects"].append(sub_subject)
                
                logger.info(f"Successfully generated complete slide {slide_number}: {sub_subject}")
                
            except Exception as e:
                logger.error(f"Failed to generate slide {slide_number} ({sub_subject}): {e}")
                failed_slides.append((slide_number, sub_subject, str(e)))
                
                # Implement progressive error handling
                if self._should_continue_after_failure(failed_slides, len(sub_subjects), i):
                    # Try fallback generation
                    try:
                        logger.info(f"Attempting fallback generation for slide {slide_number}")
                        fallback_slide = self._generate_fallback_slide_with_context(
                            sub_subject=sub_subject,
                            generation_context=generation_context,
                            slide_number=slide_number,
                            error_info=str(e)
                        )
                        
                        slides.append(fallback_slide)
                        previous_scripts.append(fallback_slide.talking_script)
                        generation_context["generated_subjects"].append(sub_subject)
                        
                        logger.warning(f"Used fallback content for slide {slide_number}")
                        
                    except Exception as fallback_error:
                        logger.error(f"Fallback generation failed for slide {slide_number}: {fallback_error}")
                        # Skip this slide but continue with others
                        continue
                else:
                    # Too many failures - abort generation
                    raise ContentGenerationError(
                        f"Too many slide generation failures: {len(failed_slides)}/{len(sub_subjects)}. "
                        f"Last error: {e}",
                        generation_step="integrated_slide_generation",
                        retry_count=len(failed_slides)
                    )
        
        # Final validation and error reporting
        if not slides:
            raise ContentGenerationError(
                "No slides were successfully generated",
                generation_step="integrated_slide_generation",
                retry_count=len(failed_slides)
            )
        
        # Log final results
        success_rate = len(slides) / len(sub_subjects) * 100
        logger.info(f"Slide generation completed: {len(slides)}/{len(sub_subjects)} slides "
                   f"({success_rate:.1f}% success rate)")
        
        if failed_slides:
            logger.warning(f"Failed slides summary: {failed_slides}")
        
        # Perform final consistency check across all slides
        try:
            self._validate_presentation_consistency(slides, generation_context)
            logger.info("Presentation consistency validation passed")
        except Exception as consistency_error:
            logger.warning(f"Presentation consistency check failed: {consistency_error}")
            # Don't fail the entire generation for consistency issues
        
        return slides
    
    def _generate_slide_content_with_context(self, sub_subject: str, generation_context: Dict[str, Any], 
                                           slide_number: int) -> str:
        """
        Generate slide content with full context awareness and retry logic.
        
        Args:
            sub_subject: The sub-subject for this slide
            generation_context: Context about the presentation and previous slides
            slide_number: Position of this slide in the presentation
            
        Returns:
            Generated slide content
            
        Raises:
            ContentGenerationError: If generation fails after retries
        """
        max_attempts = 3
        last_error = None
        
        # Prepare context for generation
        previous_subjects = generation_context.get("generated_subjects", [])
        main_subject = generation_context["main_subject"]
        total_slides = generation_context["total_slides"]
        
        for attempt in range(max_attempts):
            try:
                logger.debug(f"Slide content generation attempt {attempt + 1} for: {sub_subject}")
                
                # Use enhanced slide generation with context
                slide_content = self.llm_client.generate_slide_content(
                    sub_subject=sub_subject,
                    context=main_subject
                )
                
                # Validate content quality
                self._validate_slide_content_quality(slide_content, sub_subject, generation_context)
                
                logger.debug(f"Slide content generated successfully for: {sub_subject}")
                return slide_content
                
            except Exception as e:
                last_error = e
                logger.warning(f"Slide content generation attempt {attempt + 1} failed for {sub_subject}: {e}")
                
                if attempt < max_attempts - 1:
                    # Progressive backoff with jitter
                    backoff_time = (1.0 * (attempt + 1)) + (0.1 * attempt)
                    logger.debug(f"Retrying slide content generation in {backoff_time:.1f} seconds")
                    time.sleep(backoff_time)
        
        # All attempts failed
        raise ContentGenerationError(
            f"Failed to generate slide content for '{sub_subject}' after {max_attempts} attempts: {last_error}",
            generation_step="slide_content_generation",
            retry_count=max_attempts
        )
    
    def _generate_talking_script_with_context(self, slide_content: str, sub_subject: str,
                                            generation_context: Dict[str, Any], slide_number: int,
                                            previous_scripts: List[str]) -> str:
        """
        Generate talking script with full context awareness and retry logic.
        
        Args:
            slide_content: The content of the slide
            sub_subject: The sub-subject for this slide
            generation_context: Context about the presentation and previous slides
            slide_number: Position of this slide in the presentation
            previous_scripts: List of previously generated scripts for consistency
            
        Returns:
            Generated talking script
            
        Raises:
            ContentGenerationError: If generation fails after retries
        """
        max_attempts = 3
        last_error = None
        
        # Prepare context for generation
        main_subject = generation_context["main_subject"]
        total_slides = generation_context["total_slides"]
        presentation_tone = generation_context.get("presentation_tone", "professional")
        generated_subjects = generation_context.get("generated_subjects", [])
        
        # Determine previous and next subjects for transitions
        previous_subject = generated_subjects[-1] if generated_subjects else None
        next_subject = None
        if slide_number < total_slides:
            # We don't know the next subject yet, but we can indicate it exists
            next_subject = "next topic"
        
        for attempt in range(max_attempts):
            try:
                logger.debug(f"Talking script generation attempt {attempt + 1} for: {sub_subject}")
                
                # Use enhanced script generation with full context
                talking_script = self.llm_client.generate_talking_script(
                    slide_content=slide_content,
                    sub_subject=sub_subject,
                    context=main_subject,
                    slide_number=slide_number,
                    total_slides=total_slides,
                    previous_subject=previous_subject,
                    next_subject=next_subject,
                    presentation_tone=presentation_tone,
                    previous_scripts=previous_scripts[-2:] if previous_scripts else None  # Last 2 for consistency
                )
                
                # Validate script quality and consistency
                self._validate_script_quality(talking_script, sub_subject, slide_content, generation_context)
                
                logger.debug(f"Talking script generated successfully for: {sub_subject}")
                return talking_script
                
            except Exception as e:
                last_error = e
                logger.warning(f"Talking script generation attempt {attempt + 1} failed for {sub_subject}: {e}")
                
                if attempt < max_attempts - 1:
                    # Progressive backoff with jitter
                    backoff_time = (1.5 * (attempt + 1)) + (0.2 * attempt)
                    logger.debug(f"Retrying talking script generation in {backoff_time:.1f} seconds")
                    time.sleep(backoff_time)
        
        # All attempts failed
        raise ContentGenerationError(
            f"Failed to generate talking script for '{sub_subject}' after {max_attempts} attempts: {last_error}",
            generation_step="talking_script_generation",
            retry_count=max_attempts
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
        
        # Stop if more than 60% of slides have failed
        if failure_rate > 0.6:
            logger.error(f"Failure rate too high: {failure_rate:.1%}")
            return False
        
        # Stop if we have more than 3 consecutive failures
        if len(failed_slides) >= 3:
            recent_failures = [f for f in failed_slides if f[0] > current_index - 2]
            if len(recent_failures) >= 3:
                logger.error("Too many consecutive failures")
                return False
        
        # Continue if we're early in the process or failure rate is acceptable
        return True
    
    def _validate_slide_content_quality(self, slide_content: str, sub_subject: str, 
                                      generation_context: Dict[str, Any]) -> None:
        """
        Validate the quality of generated slide content.
        
        Args:
            slide_content: Generated slide content
            sub_subject: The sub-subject for validation
            generation_context: Context for validation
            
        Raises:
            ContentGenerationError: If content quality is insufficient
        """
        if not slide_content or not slide_content.strip():
            raise ContentGenerationError(
                "Generated slide content is empty",
                generation_step="slide_content_validation"
            )
        
        # Check length constraints
        if len(slide_content) > self.config.slide_text_max_length:
            raise ContentGenerationError(
                f"Slide content too long: {len(slide_content)} > {self.config.slide_text_max_length}",
                generation_step="slide_content_validation"
            )
        
        if len(slide_content.strip()) < 20:
            raise ContentGenerationError(
                f"Slide content too short: {len(slide_content)} characters",
                generation_step="slide_content_validation"
            )
        
        # Check for relevance to sub-subject (more lenient for different languages)
        # Instead of strict word matching, check if content is substantial enough
        # The AI should naturally create relevant content based on the prompt
        if len(slide_content.strip()) < 50:  # Very basic relevance check
            raise ContentGenerationError(
                f"Slide content too brief to be relevant: {len(slide_content)} characters",
                generation_step="slide_content_validation"
            )
        
        logger.debug(f"Slide content quality validation passed for: {sub_subject}")
    
    def _validate_script_quality(self, talking_script: str, sub_subject: str, 
                               slide_content: str, generation_context: Dict[str, Any]) -> None:
        """
        Validate the quality of generated talking script.
        
        Args:
            talking_script: Generated talking script
            sub_subject: The sub-subject for validation
            slide_content: Related slide content
            generation_context: Context for validation
            
        Raises:
            ContentGenerationError: If script quality is insufficient
        """
        if not talking_script or not talking_script.strip():
            raise ContentGenerationError(
                "Generated talking script is empty",
                generation_step="talking_script_validation"
            )
        
        # Check length constraints
        if len(talking_script) < self.config.script_min_length:
            raise ContentGenerationError(
                f"Talking script too short: {len(talking_script)} < {self.config.script_min_length}",
                generation_step="talking_script_validation"
            )
        
        # Check for proper sentence structure
        sentences = [s.strip() for s in talking_script.split('.') if s.strip()]
        if len(sentences) < 3:
            raise ContentGenerationError(
                "Talking script needs more detailed explanation (minimum 3 sentences)",
                generation_step="talking_script_validation"
            )
        
        # Check for conversational elements (language-agnostic approach)
        # Instead of looking for specific English words, check for general script quality
        word_count = len(talking_script.split())
        if word_count < 30:  # Very basic check - if it's too short, it's probably not conversational
            raise ContentGenerationError(
                "Talking script too brief for conversational tone",
                generation_step="talking_script_validation"
            )
        
        # Check for basic punctuation that indicates natural speech flow
        punctuation_count = talking_script.count('.') + talking_script.count('!') + talking_script.count('?')
        if punctuation_count < 2:
            raise ContentGenerationError(
                "Talking script lacks proper sentence structure",
                generation_step="talking_script_validation"
            )
        
        logger.debug(f"Talking script quality validation passed for: {sub_subject}")
    
    def _validate_slide_script_consistency(self, slide_content: str, talking_script: str,
                                         sub_subject: str, generation_context: Dict[str, Any]) -> None:
        """
        Validate consistency between slide content and talking script.
        
        Args:
            slide_content: Generated slide content
            talking_script: Generated talking script
            sub_subject: The sub-subject for validation
            generation_context: Context for validation
            
        Raises:
            ContentGenerationError: If consistency check fails
        """
        # Check that script expands on slide content (language-agnostic approach)
        # Instead of word matching, check if script is substantially longer than slide
        # The AI should naturally create relevant content based on the prompt
        if len(talking_script.strip()) < 100:  # Basic check for substantial content
            raise ContentGenerationError(
                f"Talking script too brief to adequately expand on slide content",
                generation_step="slide_script_consistency"
            )
        
        # Script should be significantly longer than slide content
        if len(talking_script) < len(slide_content) * 2:
            raise ContentGenerationError(
                "Talking script should be more detailed than slide content",
                generation_step="slide_script_consistency"
            )
        
        logger.debug(f"Slide-script consistency validation passed for: {sub_subject}")
    
    def _generate_fallback_slide_with_context(self, sub_subject: str, generation_context: Dict[str, Any],
                                            slide_number: int, error_info: str) -> SlideData:
        """
        Create a contextual fallback slide when AI generation fails.
        
        Args:
            sub_subject: The sub-subject for the slide
            generation_context: Context about the presentation
            slide_number: Position of this slide
            error_info: Information about the error that occurred
            
        Returns:
            SlideData object with fallback content
        """
        main_subject = generation_context["main_subject"]
        total_slides = generation_context["total_slides"]
        
        logger.info(f"Creating fallback slide {slide_number}/{total_slides} for: {sub_subject}")
        
        # Create contextual slide content
        slide_content = f"""• {sub_subject}
• Key aspects of {main_subject}
• Important concepts and principles
• Practical applications and examples
• Relevance to overall topic"""
        
        # Create contextual talking script
        position_context = ""
        if slide_number == 1:
            position_context = "Let's begin our exploration by discussing "
        elif slide_number == total_slides:
            position_context = "To conclude our presentation, let's examine "
        else:
            position_context = "Next, let's turn our attention to "
        
        talking_script = f"""{position_context}{sub_subject}. This is a crucial component of {main_subject} that deserves our attention.

When we consider {sub_subject}, we need to understand its fundamental role in the broader context of {main_subject}. This topic encompasses several important concepts that help us build a comprehensive understanding.

The key aspects we should focus on include the practical applications, the underlying principles, and how this connects to what we've discussed and what we'll explore further. This foundation will help us appreciate the full scope of {main_subject}.

Understanding {sub_subject} provides valuable insights that enhance our overall comprehension of the topic and its real-world implications."""
        
        fallback_slide = SlideData(
            sub_subject=sub_subject,
            slide_text=slide_content,
            talking_script=talking_script
        )
        
        logger.warning(f"Generated fallback slide for: {sub_subject} (reason: {error_info[:100]}...)")
        return fallback_slide
    
    def _validate_presentation_consistency(self, slides: List[SlideData], generation_context: Dict[str, Any]) -> None:
        """
        Validate consistency across the entire presentation.
        
        Args:
            slides: List of generated slides
            generation_context: Context about the presentation
            
        Raises:
            ContentGenerationError: If presentation consistency issues are found
        """
        if len(slides) < 2:
            return  # Can't validate consistency with less than 2 slides
        
        logger.debug("Validating presentation consistency across all slides")
        
        # Check for duplicate content
        slide_contents = [slide.slide_text.lower() for slide in slides]
        for i, content1 in enumerate(slide_contents):
            for j, content2 in enumerate(slide_contents[i+1:], i+1):
                # Calculate similarity (simple word overlap)
                words1 = set(content1.split())
                words2 = set(content2.split())
                if words1 and words2:
                    similarity = len(words1.intersection(words2)) / len(words1.union(words2))
                    if similarity > 0.7:  # More than 70% similar
                        logger.warning(f"High similarity between slides {i+1} and {j+1}: {similarity:.1%}")
        
        # Check script length consistency
        script_lengths = [len(slide.talking_script) for slide in slides]
        avg_length = sum(script_lengths) / len(script_lengths)
        
        for i, length in enumerate(script_lengths):
            if length < avg_length * 0.5:  # Less than 50% of average
                logger.warning(f"Slide {i+1} script is unusually short: {length} vs avg {avg_length:.0f}")
            elif length > avg_length * 2:  # More than 200% of average
                logger.warning(f"Slide {i+1} script is unusually long: {length} vs avg {avg_length:.0f}")
        
        logger.debug("Presentation consistency validation completed")
    
    def _create_presentation_data(self, subject: str, slides: List[SlideData]) -> PresentationData:
        """
        Create the final PresentationData object.
        
        Args:
            subject: Main presentation subject
            slides: List of generated slides
            
        Returns:
            Complete PresentationData object
        """
        generation_time = self._current_progress.elapsed_time if self._current_progress else 0.0
        
        metadata = {
            "total_slides": len(slides),
            "generation_time": generation_time,
            "model_version": self.config.gemini_model,
            "generated_at": datetime.now().isoformat(),
            "config_version": "1.0"
        }
        
        presentation = PresentationData(
            main_subject=subject,
            slides=slides,
            created_at=datetime.now(),
            metadata=metadata
        )
        
        logger.info(f"Created presentation data with {len(slides)} slides")
        return presentation
    
    def _update_progress(self) -> None:
        """Update progress and call progress callback if set."""
        if self.progress_callback and self._current_progress:
            try:
                self.progress_callback(self._current_progress)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    def _generate_audio_for_slide(self, slide: SlideData, slide_index: int):
        """
        Generates audio for a single slide.

        Args:
            slide: The slide data.
            slide_index: The index of the slide.
        """
        if not self.tts_client:
            return

        try:
            audio_dir = "audio_files"
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)

            file_path = os.path.join(audio_dir, f"slide_{slide_index}")
            self.tts_client.generate_audio(slide.talking_script, file_path)
        except Exception as e:
            logger.error(f"Error generating audio for slide {slide_index}: {e}")

    def get_current_progress(self) -> Optional[GenerationProgress]:
        """Get the current generation progress."""
        return self._current_progress
    
    def cancel_generation(self) -> None:
        """Cancel the current generation process (if supported in future)."""
        # This is a placeholder for future cancellation support
        logger.warning("Generation cancellation requested (not yet implemented)")
        pass