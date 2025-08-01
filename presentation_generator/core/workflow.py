"""
Workflow orchestrator for presentation generation.

This module provides the WorkflowManager class that coordinates the complete
presentation generation workflow with step coordination, progress tracking,
error handling, and resource cleanup.
"""

import os
import shutil
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, Future, as_completed

from ..models.data import Slide, Presentation, PresentationResult
from ..utils.config import Config
from ..utils.exceptions import (
    WorkflowError,
    MediaProcessingError,
    ContentGenerationError,
    PresentationGeneratorError
)


@dataclass
class WorkflowStep:
    """Represents a single step in the workflow."""
    name: str
    description: str
    required: bool = True
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: float = 0.0  # seconds
    
    def __post_init__(self):
        """Validate step configuration."""
        if not self.name.strip():
            raise ValueError("Step name cannot be empty")
        if not self.description.strip():
            raise ValueError("Step description cannot be empty")


@dataclass
class StepResult:
    """Result of executing a workflow step."""
    step_name: str
    success: bool
    start_time: datetime
    end_time: Optional[datetime] = None
    result_data: Optional[Any] = None
    error: Optional[Exception] = None
    cleanup_actions: List[Callable[[], None]] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        """Get step execution duration in seconds."""
        if not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()
    
    def add_cleanup_action(self, action: Callable[[], None]) -> None:
        """Add a cleanup action to be executed later."""
        self.cleanup_actions.append(action)


@dataclass
class WorkflowProgress:
    """Tracks overall workflow progress."""
    current_step: str
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    total_steps: int = 0
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        if self.total_steps == 0:
            return 0.0
        return (len(self.completed_steps) / self.total_steps) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds since workflow started."""
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return len(self.completed_steps) == self.total_steps
    
    @property
    def has_failures(self) -> bool:
        """Check if workflow has any failures."""
        return len(self.failed_steps) > 0


class ResourceManager:
    """Manages temporary files and resources during workflow execution."""
    
    def __init__(self, base_dir: Optional[str] = None, cleanup_on_exit: bool = True):
        """
        Initialize resource manager.
        
        Args:
            base_dir: Base directory for temporary files
            cleanup_on_exit: Whether to cleanup resources on exit
        """
        self.base_dir = Path(base_dir) if base_dir else Path(tempfile.gettempdir())
        self.cleanup_on_exit = cleanup_on_exit
        self.temp_dirs: List[Path] = []
        self.temp_files: List[Path] = []
        self.cleanup_actions: List[Callable[[], None]] = []
        self._lock = threading.Lock()
    
    def create_temp_dir(self, prefix: str = "presentation_gen_") -> Path:
        """
        Create a temporary directory.
        
        Args:
            prefix: Prefix for the directory name
            
        Returns:
            Path to the created directory
        """
        with self._lock:
            temp_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=self.base_dir))
            self.temp_dirs.append(temp_dir)
            return temp_dir
    
    def create_temp_file(self, suffix: str = "", prefix: str = "temp_") -> Path:
        """
        Create a temporary file.
        
        Args:
            suffix: File suffix/extension
            prefix: File prefix
            
        Returns:
            Path to the created file
        """
        with self._lock:
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=self.base_dir)
            os.close(fd)  # Close the file descriptor
            temp_file = Path(temp_path)
            self.temp_files.append(temp_file)
            return temp_file
    
    def register_cleanup_action(self, action: Callable[[], None]) -> None:
        """
        Register a cleanup action to be executed during cleanup.
        
        Args:
            action: Cleanup function to execute
        """
        with self._lock:
            self.cleanup_actions.append(action)
    
    def cleanup_all(self) -> None:
        """Clean up all managed resources."""
        with self._lock:
            errors = []
            
            # Execute custom cleanup actions
            for action in self.cleanup_actions:
                try:
                    action()
                except Exception as e:
                    errors.append(f"Cleanup action failed: {e}")
            
            # Clean up temporary files
            for temp_file in self.temp_files:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                except Exception as e:
                    errors.append(f"Failed to remove temp file {temp_file}: {e}")
            
            # Clean up temporary directories
            for temp_dir in self.temp_dirs:
                try:
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
                except Exception as e:
                    errors.append(f"Failed to remove temp dir {temp_dir}: {e}")
            
            # Clear lists
            self.temp_files.clear()
            self.temp_dirs.clear()
            self.cleanup_actions.clear()
            
            if errors and len(errors) > 3:
                # Log errors but don't raise exception during cleanup
                print(f"Warning: {len(errors)} cleanup errors occurred")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        if self.cleanup_on_exit:
            self.cleanup_all()


class WorkflowManager:
    """
    Orchestrates the complete presentation generation workflow.
    
    This class coordinates all steps of the presentation generation process:
    1. Content generation (slides and scripts)
    2. Image rendering (slide to image conversion)
    3. Audio generation (text-to-speech)
    4. Video assembly (combining images and audio)
    
    Features:
    - Step-by-step progress tracking
    - Error recovery and fallback strategies
    - Resource management and cleanup
    - Parallel processing where possible
    - Comprehensive error handling
    """
    
    def __init__(self, config: Config):
        """
        Initialize the workflow manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.progress_callback: Optional[Callable[[WorkflowProgress], None]] = None
        self.resource_manager: Optional[ResourceManager] = None
        self._current_progress: Optional[WorkflowProgress] = None
        self._step_results: Dict[str, StepResult] = {}
        self._workflow_steps: Dict[str, WorkflowStep] = {}
        self._lock = threading.Lock()
        
        # Initialize workflow steps
        self._initialize_workflow_steps()
    
    def _initialize_workflow_steps(self) -> None:
        """Initialize the workflow step definitions."""
        self._workflow_steps = {
            "content_generation": WorkflowStep(
                name="content_generation",
                description="Generate slide content and scripts using LLM",
                required=True,
                dependencies=[],
                estimated_duration=30.0
            ),
            "image_generation": WorkflowStep(
                name="image_generation",
                description="Convert slides to images",
                required=True,
                dependencies=["content_generation"],
                estimated_duration=15.0
            ),
            "audio_generation": WorkflowStep(
                name="audio_generation",
                description="Generate audio narration from scripts",
                required=self.config.include_audio,
                dependencies=["content_generation"],
                estimated_duration=20.0
            ),
            "video_assembly": WorkflowStep(
                name="video_assembly",
                description="Assemble final video from images and audio",
                required=self.config.include_video,
                dependencies=["image_generation", "audio_generation"] if self.config.include_audio else ["image_generation"],
                estimated_duration=25.0
            ),
            "finalization": WorkflowStep(
                name="finalization",
                description="Finalize presentation and cleanup",
                required=True,
                dependencies=["video_assembly"] if self.config.include_video else ["image_generation"],
                estimated_duration=5.0
            )
        }
    
    def set_progress_callback(self, callback: Callable[[WorkflowProgress], None]) -> None:
        """
        Set a callback function to receive progress updates.
        
        Args:
            callback: Function that receives WorkflowProgress updates
        """
        self.progress_callback = callback
    
    def execute_workflow(
        self,
        topic: str,
        content_generator: Any,
        image_processor: Any,
        audio_processor: Optional[Any] = None,
        video_assembler: Optional[Any] = None
    ) -> PresentationResult:
        """
        Execute the complete presentation generation workflow.
        
        Args:
            topic: Presentation topic
            content_generator: Content generation component
            image_processor: Image processing component
            audio_processor: Audio processing component (optional)
            video_assembler: Video assembly component (optional)
            
        Returns:
            PresentationResult with generated presentation
            
        Raises:
            WorkflowError: If workflow execution fails
        """
        if not topic or not topic.strip():
            raise WorkflowError("Topic cannot be empty", step="validation")
        
        # Initialize progress tracking
        required_steps = [name for name, step in self._workflow_steps.items() if step.required]
        self._current_progress = WorkflowProgress(
            current_step="Initializing",
            total_steps=len(required_steps),
            start_time=datetime.now()
        )
        self._update_progress()
        
        # Initialize resource management
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with ResourceManager(base_dir=str(output_dir), cleanup_on_exit=self.config.temp_cleanup) as resource_manager:
            self.resource_manager = resource_manager
            
            try:
                # Create working directory for this presentation
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                topic_slug = self._create_topic_slug(topic)
                work_dir = resource_manager.create_temp_dir(f"presentation_{topic_slug}_{timestamp}_")
                
                # Execute workflow steps
                presentation_data = self._execute_workflow_steps(
                    topic=topic,
                    work_dir=work_dir,
                    content_generator=content_generator,
                    image_processor=image_processor,
                    audio_processor=audio_processor,
                    video_assembler=video_assembler
                )
                
                # Create final result
                result = PresentationResult(
                    presentation=presentation_data,
                    json_path=str(work_dir / "presentation.json") if self.config.temp_cleanup else None
                )
                
                self._current_progress.current_step = "Complete"
                self._update_progress()
                
                return result
                
            except Exception as e:
                self._handle_workflow_error(e)
                raise
            finally:
                self.resource_manager = None
    
    def _execute_workflow_steps(
        self,
        topic: str,
        work_dir: Path,
        content_generator: Any,
        image_processor: Any,
        audio_processor: Optional[Any],
        video_assembler: Optional[Any]
    ) -> Presentation:
        """Execute all workflow steps in order."""
        presentation_data = None
        
        # Step 1: Content Generation
        if self._should_execute_step("content_generation"):
            self._current_progress.current_step = "Generating content"
            self._update_progress()
            
            slides = self._execute_step_with_error_handling(
                step_name="content_generation",
                step_function=lambda: self._execute_content_generation(content_generator, topic),
                required=True
            )
            
            presentation_data = Presentation(
                topic=topic,
                slides=slides,
                metadata={"work_dir": str(work_dir)}
            )
            
            self._mark_step_complete("content_generation")
        
        # Step 2: Image Generation
        if self._should_execute_step("image_generation"):
            self._current_progress.current_step = "Generating images"
            self._update_progress()
            
            self._execute_step_with_error_handling(
                step_name="image_generation",
                step_function=lambda: self._execute_image_generation(
                    image_processor, presentation_data, work_dir
                ),
                required=True
            )
            
            self._mark_step_complete("image_generation")
        
        # Step 3: Audio Generation (if enabled)
        if self._should_execute_step("audio_generation") and audio_processor:
            self._current_progress.current_step = "Generating audio"
            self._update_progress()
            
            self._execute_step_with_error_handling(
                step_name="audio_generation",
                step_function=lambda: self._execute_audio_generation(
                    audio_processor, presentation_data, work_dir
                ),
                required=self.config.include_audio
            )
            
            self._mark_step_complete("audio_generation")
        
        # Step 4: Video Assembly (if enabled)
        if self._should_execute_step("video_assembly") and video_assembler:
            self._current_progress.current_step = "Assembling video"
            self._update_progress()
            
            video_path = self._execute_step_with_error_handling(
                step_name="video_assembly",
                step_function=lambda: self._execute_video_assembly(
                    video_assembler, presentation_data, work_dir
                ),
                required=self.config.include_video
            )
            
            if video_path:
                presentation_data.video_path = str(video_path)
            
            self._mark_step_complete("video_assembly")
        
        # Step 5: Finalization
        if self._should_execute_step("finalization"):
            self._current_progress.current_step = "Finalizing"
            self._update_progress()
            
            self._execute_step_with_error_handling(
                step_name="finalization",
                step_function=lambda: self._execute_finalization(presentation_data, work_dir),
                required=True
            )
            
            self._mark_step_complete("finalization")
        
        return presentation_data
    
    def _execute_content_generation(self, content_generator: Any, topic: str) -> List[Slide]:
        """Execute content generation step."""
        try:
            slides = content_generator.generate_slides(topic)
            if not slides:
                raise ContentGenerationError("No slides were generated")
            return slides
        except Exception as e:
            raise WorkflowError(
                f"Content generation failed: {e}",
                step="content_generation",
                details=str(e)
            )
    
    def _execute_image_generation(self, image_processor: Any, presentation: Presentation, work_dir: Path) -> None:
        """Execute image generation step."""
        try:
            images_dir = work_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            # Process slides in parallel for better performance
            with ThreadPoolExecutor(max_workers=min(4, len(presentation.slides))) as executor:
                futures = []
                
                for i, slide in enumerate(presentation.slides):
                    future = executor.submit(
                        self._generate_single_image,
                        image_processor,
                        slide,
                        images_dir,
                        i + 1
                    )
                    futures.append((future, slide, i))
                
                # Collect results
                for future, slide, index in futures:
                    try:
                        image_path = future.result(timeout=60)  # 60 second timeout per image
                        slide.image_path = str(image_path)
                    except Exception as e:
                        raise MediaProcessingError(
                            f"Failed to generate image for slide {index + 1}: {e}",
                            media_type="image"
                        )
        
        except Exception as e:
            if isinstance(e, MediaProcessingError):
                raise
            raise WorkflowError(
                f"Image generation failed: {e}",
                step="image_generation",
                details=str(e)
            )
    
    def _generate_single_image(self, image_processor: Any, slide: Slide, images_dir: Path, slide_number: int) -> Path:
        """Generate image for a single slide."""
        image_path = images_dir / f"slide_{slide_number:03d}.png"
        image_processor.generate_image(slide, str(image_path))
        return image_path
    
    def _execute_audio_generation(self, audio_processor: Any, presentation: Presentation, work_dir: Path) -> None:
        """Execute audio generation step."""
        try:
            audio_dir = work_dir / "audio"
            audio_dir.mkdir(exist_ok=True)
            
            # Process audio in parallel
            with ThreadPoolExecutor(max_workers=min(3, len(presentation.slides))) as executor:
                futures = []
                
                for i, slide in enumerate(presentation.slides):
                    future = executor.submit(
                        self._generate_single_audio,
                        audio_processor,
                        slide,
                        audio_dir,
                        i + 1
                    )
                    futures.append((future, slide, i))
                
                # Collect results
                for future, slide, index in futures:
                    try:
                        audio_path, duration = future.result(timeout=120)  # 2 minute timeout per audio
                        slide.audio_path = str(audio_path)
                        slide.duration = duration
                    except Exception as e:
                        raise MediaProcessingError(
                            f"Failed to generate audio for slide {index + 1}: {e}",
                            media_type="audio"
                        )
        
        except Exception as e:
            if isinstance(e, MediaProcessingError):
                raise
            raise WorkflowError(
                f"Audio generation failed: {e}",
                step="audio_generation",
                details=str(e)
            )
    
    def _generate_single_audio(self, audio_processor: Any, slide: Slide, audio_dir: Path, slide_number: int) -> tuple[Path, float]:
        """Generate audio for a single slide."""
        audio_path = audio_dir / f"slide_{slide_number:03d}.{self.config.audio_format}"
        duration = audio_processor.generate_audio(slide.script, str(audio_path))
        return audio_path, duration
    
    def _execute_video_assembly(self, video_assembler: Any, presentation: Presentation, work_dir: Path) -> Path:
        """Execute video assembly step."""
        try:
            video_path = work_dir / f"{self._create_topic_slug(presentation.topic)}.mp4"
            video_assembler.assemble_video(presentation, str(video_path))
            return video_path
        except Exception as e:
            raise WorkflowError(
                f"Video assembly failed: {e}",
                step="video_assembly",
                details=str(e)
            )
    
    def _execute_finalization(self, presentation: Presentation, work_dir: Path) -> None:
        """Execute finalization step."""
        try:
            # Save presentation metadata if requested
            if not self.config.temp_cleanup:
                import json
                metadata_path = work_dir / "presentation.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "topic": presentation.topic,
                        "slide_count": len(presentation.slides),
                        "total_duration": presentation.total_duration,
                        "created_at": presentation.created_at.isoformat(),
                        "video_path": presentation.video_path,
                        "slides": [
                            {
                                "title": slide.title,
                                "image_path": slide.image_path,
                                "audio_path": slide.audio_path,
                                "duration": slide.duration
                            }
                            for slide in presentation.slides
                        ]
                    }, f, indent=2)
            
            # Move final outputs to permanent location if needed
            if presentation.video_path and self.config.include_video:
                final_output_dir = Path(self.config.output_dir) / "presentations"
                final_output_dir.mkdir(parents=True, exist_ok=True)
                
                final_video_path = final_output_dir / Path(presentation.video_path).name
                if Path(presentation.video_path).exists():
                    shutil.copy2(presentation.video_path, final_video_path)
                    presentation.video_path = str(final_video_path)
        
        except Exception as e:
            raise WorkflowError(
                f"Finalization failed: {e}",
                step="finalization",
                details=str(e)
            )
    
    def _should_execute_step(self, step_name: str) -> bool:
        """Check if a step should be executed."""
        step = self._workflow_steps.get(step_name)
        if not step:
            return False
        
        # Check if step is required
        if not step.required:
            return False
        
        # Check if already completed (only if progress tracking is active)
        if self._current_progress and step_name in self._current_progress.completed_steps:
            return False
        
        # Check dependencies (only if progress tracking is active)
        if self._current_progress:
            for dep in step.dependencies:
                if dep not in self._current_progress.completed_steps:
                    return False
        
        return True
    
    def _execute_step_with_error_handling(
        self,
        step_name: str,
        step_function: Callable[[], Any],
        required: bool = True
    ) -> Any:
        """Execute a step with comprehensive error handling."""
        step_result = StepResult(
            step_name=step_name,
            success=False,
            start_time=datetime.now()
        )
        
        try:
            result = step_function()
            step_result.success = True
            step_result.result_data = result
            step_result.end_time = datetime.now()
            
            self._step_results[step_name] = step_result
            return result
            
        except Exception as e:
            step_result.error = e
            step_result.end_time = datetime.now()
            self._step_results[step_name] = step_result
            
            if required:
                raise WorkflowError(
                    f"Required step '{step_name}' failed: {e}",
                    step=step_name,
                    details=str(e)
                )
            else:
                # Log warning for optional step failure
                print(f"Warning: Optional step '{step_name}' failed: {e}")
                return None
    
    def _mark_step_complete(self, step_name: str) -> None:
        """Mark a step as completed."""
        with self._lock:
            if step_name not in self._current_progress.completed_steps:
                self._current_progress.completed_steps.append(step_name)
                self._update_progress()
    
    def _handle_workflow_error(self, error: Exception) -> None:
        """Handle workflow errors with cleanup."""
        current_step = self._current_progress.current_step if self._current_progress else "unknown"
        
        # Mark current step as failed
        if self._current_progress and current_step not in self._current_progress.failed_steps:
            self._current_progress.failed_steps.append(current_step)
        
        # Execute cleanup for completed steps
        self._cleanup_step_resources()
        
        # Update progress to reflect failure
        if self._current_progress:
            self._current_progress.current_step = f"Failed: {current_step}"
            self._update_progress()
    
    def _cleanup_step_resources(self) -> None:
        """Clean up resources from completed steps."""
        for step_result in self._step_results.values():
            for cleanup_action in step_result.cleanup_actions:
                try:
                    cleanup_action()
                except Exception as e:
                    print(f"Warning: Cleanup action failed: {e}")
    
    def _create_topic_slug(self, topic: str) -> str:
        """Create a filesystem-safe slug from the topic."""
        import re
        slug = re.sub(r'[^\w\s-]', '', topic.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')[:50]  # Limit length
    
    def _update_progress(self) -> None:
        """Update progress and call progress callback if set."""
        if self.progress_callback and self._current_progress:
            try:
                self.progress_callback(self._current_progress)
            except Exception:
                # Don't let callback errors break the workflow
                pass
    
    def get_current_progress(self) -> Optional[WorkflowProgress]:
        """Get the current workflow progress."""
        return self._current_progress
    
    def get_step_results(self) -> Dict[str, StepResult]:
        """Get results from all executed steps."""
        return self._step_results.copy()
    
    def cancel_workflow(self) -> None:
        """Cancel the current workflow execution (placeholder for future implementation)."""
        # This is a placeholder for future cancellation support
        if self._current_progress:
            self._current_progress.current_step = "Cancelled"
            self._update_progress()
    
    @contextmanager
    def managed_execution(self):
        """Context manager for managed workflow execution with automatic cleanup."""
        try:
            yield self
        finally:
            if self.resource_manager:
                self.resource_manager.cleanup_all()