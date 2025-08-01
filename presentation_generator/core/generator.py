"""
Main presentation generator orchestrator class.

This module contains the PresentationGenerator class that coordinates
the complete presentation workflow from topic input to final video output.
"""

import os
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from ..models.data import PresentationResult, Presentation
from ..utils.config import Config
from ..utils.exceptions import (
    PresentationGeneratorError,
    ConfigurationError,
    ContentGenerationError,
    MediaProcessingError,
    WorkflowError
)
from ..providers.base import ProviderFactory
from .content import ContentGenerator
from .workflow import WorkflowManager, WorkflowProgress
from ..media.images import ImageProcessor
from ..media.audio import AudioProcessor
from ..media.video import VideoProcessor


class PresentationGenerator:
    """
    Main orchestrator class for presentation generation.
    
    This class coordinates the complete workflow from topic input to final video output:
    1. Content generation (slides and scripts using LLM)
    2. Image rendering (slide to image conversion)
    3. Audio generation (text-to-speech from scripts)
    4. Video assembly (combining images and audio)
    
    The generator integrates all components and provides a simple public API
    while handling the complete workflow internally with error recovery and cleanup.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the presentation generator.
        
        Args:
            config: Configuration object (uses defaults if None)
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = config or Config()
        
        # Validate configuration for generation
        try:
            self.config.validate_for_generation()
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}")
        
        # Initialize components
        self._provider = None
        self._content_generator = None
        self._image_processor = None
        self._audio_processor = None
        self._video_processor = None
        self._workflow_manager = None
        
        # Progress tracking
        self.progress_callback: Optional[Callable[[WorkflowProgress], None]] = None
    
    def generate(self, topic: str, **options) -> PresentationResult:
        """
        Generate a complete presentation from a topic.
        
        This is the main public API method that orchestrates the complete workflow:
        1. Validates input and configuration
        2. Initializes all required components
        3. Executes the workflow through WorkflowManager
        4. Returns structured presentation result
        
        Args:
            topic: The presentation topic
            **options: Additional generation options:
                - progress_callback: Function to receive progress updates
                - output_dir: Override output directory
                - slide_count: Override target slide count
                - include_audio: Override audio generation setting
                - include_video: Override video generation setting
                
        Returns:
            PresentationResult with the generated presentation and all assets
            
        Raises:
            PresentationGeneratorError: If generation fails at any step
            ConfigurationError: If configuration is invalid
            ValidationError: If input validation fails
        """
        if not topic or not topic.strip():
            raise PresentationGeneratorError(
                "Topic cannot be empty",
                details="Please provide a valid presentation topic"
            )
        
        topic = topic.strip()
        
        try:
            # Apply options to configuration
            effective_config = self._apply_generation_options(options)
            
            # Set progress callback if provided
            if 'progress_callback' in options:
                self.progress_callback = options['progress_callback']
            
            # Initialize all components
            self._initialize_components(effective_config)
            
            # Set up progress tracking
            if self.progress_callback:
                self._workflow_manager.set_progress_callback(self.progress_callback)
                self._content_generator.set_progress_callback(
                    lambda progress: self.progress_callback(
                        # Convert content progress to workflow progress format
                        type('WorkflowProgress', (), {
                            'current_step': f"Content: {progress.current_step}",
                            'progress_percentage': progress.progress_percentage,
                            'elapsed_time': progress.elapsed_time
                        })()
                    )
                )
            
            # Execute the complete workflow
            result = self._workflow_manager.execute_workflow(
                topic=topic,
                content_generator=self._content_generator,
                image_processor=self._image_processor,
                audio_processor=self._audio_processor if effective_config.include_audio else None,
                video_assembler=self._video_processor if effective_config.include_video else None
            )
            
            return result
            
        except (ConfigurationError, ContentGenerationError, MediaProcessingError, WorkflowError) as e:
            # Re-raise known exceptions
            raise
        except Exception as e:
            # Wrap unexpected exceptions
            raise PresentationGeneratorError(
                f"Unexpected error during presentation generation: {e}",
                details=f"Topic: {topic}"
            ) from e
    
    def _apply_generation_options(self, options: Dict[str, Any]) -> Config:
        """
        Apply generation options to create effective configuration.
        
        Args:
            options: Generation options to apply
            
        Returns:
            Configuration with options applied
        """
        # Create a copy of the current config
        config_dict = self.config.to_dict()
        
        # Apply overrides from options
        if 'output_dir' in options:
            config_dict['output_dir'] = options['output_dir']
        if 'slide_count' in options:
            config_dict['slide_count'] = options['slide_count']
        if 'include_audio' in options:
            config_dict['include_audio'] = options['include_audio']
        if 'include_video' in options:
            config_dict['include_video'] = options['include_video']
        
        # Create new config with overrides
        effective_config = Config.from_dict(config_dict)
        effective_config.validate_for_generation()
        
        return effective_config
    
    def _initialize_components(self, config: Config) -> None:
        """
        Initialize all required components for generation.
        
        Args:
            config: Configuration to use for initialization
            
        Raises:
            ConfigurationError: If component initialization fails
        """
        try:
            # Initialize LLM provider
            self._provider = ProviderFactory.create_provider(
                provider_type=config.llm_provider,
                api_key=config.api_key,
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=config.timeout,
                base_url=config.base_url,
                organization=config.organization
            )
            
            # Initialize content generator
            self._content_generator = ContentGenerator(
                provider=self._provider,
                config=config
            )
            
            # Initialize image processor
            self._image_processor = ImageProcessor(config)
            
            # Initialize audio processor (if needed)
            if config.include_audio:
                self._audio_processor = AudioProcessor(config)
            
            # Initialize video processor (if needed)
            if config.include_video:
                self._video_processor = VideoProcessor(config)
            
            # Initialize workflow manager
            self._workflow_manager = WorkflowManager(config)
            
        except Exception as e:
            raise ConfigurationError(
                f"Failed to initialize components: {e}",
                details="Check your configuration and API keys"
            ) from e
    
    def configure(self, config: Config) -> None:
        """
        Update the generator configuration.
        
        This will reset all initialized components to use the new configuration.
        
        Args:
            config: New configuration object
            
        Raises:
            ConfigurationError: If the new configuration is invalid
        """
        try:
            config.validate_for_generation()
            self.config = config
            
            # Reset components to force re-initialization with new config
            self._provider = None
            self._content_generator = None
            self._image_processor = None
            self._audio_processor = None
            self._video_processor = None
            self._workflow_manager = None
            
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}")
    
    def get_supported_providers(self) -> list[str]:
        """
        Get list of supported LLM providers.
        
        Returns:
            List of supported provider names
        """
        return ProviderFactory.get_available_providers()
    
    def test_provider_connection(self) -> bool:
        """
        Test connection to the configured LLM provider.
        
        Returns:
            True if connection is successful, False otherwise
            
        Raises:
            ConfigurationError: If provider is not configured
        """
        try:
            if not self._provider:
                self._initialize_components(self.config)
            
            return self._provider.test_connection()
            
        except Exception:
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the configured provider.
        
        Returns:
            Dictionary containing provider information
            
        Raises:
            ConfigurationError: If provider is not configured
        """
        try:
            if not self._provider:
                self._initialize_components(self.config)
            
            return self._provider.get_model_info()
            
        except Exception as e:
            raise ConfigurationError(f"Failed to get provider info: {e}")
    
    def get_generation_estimate(self, topic: str) -> Dict[str, Any]:
        """
        Get an estimate of generation time and resources.
        
        Args:
            topic: The presentation topic
            
        Returns:
            Dictionary with generation estimates
        """
        try:
            # Estimate based on configuration
            slide_count = self.config.slide_count or 6
            
            # Time estimates (in seconds)
            content_time = slide_count * 5  # ~5 seconds per slide for content
            image_time = slide_count * 3    # ~3 seconds per slide for images
            audio_time = slide_count * 4 if self.config.include_audio else 0  # ~4 seconds per slide
            video_time = slide_count * 2 if self.config.include_video else 0  # ~2 seconds per slide
            
            total_time = content_time + image_time + audio_time + video_time
            
            return {
                "estimated_slides": slide_count,
                "estimated_duration_seconds": total_time,
                "estimated_duration_minutes": round(total_time / 60, 1),
                "steps": {
                    "content_generation": content_time,
                    "image_generation": image_time,
                    "audio_generation": audio_time,
                    "video_assembly": video_time
                },
                "includes_audio": self.config.include_audio,
                "includes_video": self.config.include_video,
                "provider": self.config.llm_provider,
                "model": self.config.model or "default"
            }
            
        except Exception as e:
            return {
                "error": f"Failed to generate estimate: {e}",
                "estimated_slides": 6,
                "estimated_duration_minutes": 5.0
            }
    
    def cancel_generation(self) -> None:
        """
        Cancel the current generation process.
        
        Note: This is a placeholder for future implementation.
        Cancellation support would require coordination with all components.
        """
        if self._workflow_manager:
            self._workflow_manager.cancel_workflow()
        if self._content_generator:
            self._content_generator.cancel_generation()
    
    def cleanup_resources(self) -> None:
        """
        Clean up any resources held by the generator.
        
        This method can be called to free up resources when the generator
        is no longer needed.
        """
        # Reset all components
        self._provider = None
        self._content_generator = None
        self._image_processor = None
        self._audio_processor = None
        self._video_processor = None
        self._workflow_manager = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup_resources()
    
    def __str__(self) -> str:
        """String representation of the generator."""
        return f"PresentationGenerator(provider={self.config.llm_provider}, model={self.config.model})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the generator."""
        return (
            f"PresentationGenerator("
            f"provider={self.config.llm_provider}, "
            f"model={self.config.model}, "
            f"output_dir={self.config.output_dir}, "
            f"include_audio={self.config.include_audio}, "
            f"include_video={self.config.include_video})"
        )