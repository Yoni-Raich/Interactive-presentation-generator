"""
Video processing component for assembling final presentation videos.

Consolidates video assembly functionality from the existing video_generator module
and integrates with the new Slide and Presentation data models.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List

from ..models.data import Slide, Presentation
from ..utils.exceptions import MediaProcessingError
from ..utils.config import Config


class VideoProcessor:
    """
    Processes slides with images and audio to create final video presentation.
    
    Consolidates video assembly functionality and integrates with the new data models.
    Uses FFmpeg to combine slide images and audio into a synchronized video.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the video processor.
        
        Args:
            config: Configuration object with video settings
        """
        self.config = config
        self.fps = config.video_fps
        self.resolution = f"{config.image_width}:{config.image_height}"
    
    def process_presentation(self, presentation: Presentation, output_dir: Path) -> None:
        """
        Process presentation to create final video and populate video_path.
        
        Args:
            presentation: Presentation object with slides containing image and audio paths
            output_dir: Directory to save the final video
            
        Raises:
            MediaProcessingError: If video assembly fails
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate video filename
        safe_topic = self._sanitize_filename(presentation.topic)
        video_filename = f"{safe_topic}_presentation.mp4"
        video_path = output_dir / video_filename
        
        try:
            # Validate slides have required media files
            valid_slides = self._validate_slides(presentation.slides, output_dir)
            
            if not valid_slides:
                raise MediaProcessingError("No valid slides with both image and audio found")
            
            # Create video segments for each slide
            temp_videos = []
            
            for i, slide in enumerate(valid_slides):
                temp_video = self._create_slide_video(slide, output_dir, i)
                if temp_video:
                    temp_videos.append(temp_video)
            
            if not temp_videos:
                raise MediaProcessingError("No video segments created")
            
            # Combine all segments into final video
            self._combine_videos(temp_videos, video_path)
            
            # Update presentation with video path
            presentation.video_path = str(video_path.relative_to(output_dir.parent))
            
            # Clean up temporary files
            self._cleanup_temp_files(temp_videos)
            
        except Exception as e:
            raise MediaProcessingError(f"Video processing failed: {e}")
    
    def _validate_slides(self, slides: List[Slide], output_dir: Path) -> List[Slide]:
        """
        Validate that slides have required image and audio files.
        
        Args:
            slides: List of slides to validate
            output_dir: Base directory for resolving relative paths
            
        Returns:
            List of valid slides with existing media files
        """
        valid_slides = []
        
        for slide in slides:
            if not slide.image_path or not slide.audio_path:
                continue
            
            # Resolve paths relative to output_dir
            image_path = output_dir / slide.image_path
            audio_path = output_dir / slide.audio_path
            
            # Handle case where audio might have .wav extension
            if not audio_path.exists():
                audio_path = audio_path.with_suffix('.wav')
            
            if image_path.exists() and audio_path.exists():
                valid_slides.append(slide)
        
        return valid_slides
    
    def _create_slide_video(self, slide: Slide, output_dir: Path, slide_index: int) -> Path:
        """
        Create video segment for a single slide.
        
        Args:
            slide: Slide with image and audio paths
            output_dir: Base directory for resolving paths
            slide_index: Index for temporary file naming
            
        Returns:
            Path to created video segment
            
        Raises:
            MediaProcessingError: If video segment creation fails
        """
        try:
            # Resolve full paths
            image_path = output_dir / slide.image_path
            audio_path = output_dir / slide.audio_path
            
            # Handle case where audio might have .wav extension
            if not audio_path.exists():
                audio_path = audio_path.with_suffix('.wav')
            
            # Create temporary video file
            temp_video = Path(tempfile.gettempdir()) / f"temp_slide_{slide_index:02d}.mp4"
            
            # FFmpeg command to create video from image and audio
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite existing files
                '-loop', '1',  # Loop the image
                '-i', str(image_path),  # Image file
                '-i', str(audio_path),  # Audio file
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'aac',  # Audio codec
                '-b:a', '192k',  # Audio bitrate
                '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                '-shortest',  # Video length based on audio duration
                '-vf', f'scale={self.resolution}:force_original_aspect_ratio=decrease,'
                       f'pad={self.resolution}:(ow-iw)/2:(oh-ih)/2',  # Scale and pad
                '-r', str(self.fps),  # Frame rate
                str(temp_video)
            ]
            
            # Run FFmpeg command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise MediaProcessingError(
                    f"FFmpeg failed for slide {slide_index}: {result.stderr}"
                )
            
            if not temp_video.exists():
                raise MediaProcessingError(f"Video segment not created: {temp_video}")
            
            return temp_video
            
        except subprocess.TimeoutExpired:
            raise MediaProcessingError(f"Video creation timed out for slide {slide_index}")
        except FileNotFoundError:
            raise MediaProcessingError(
                "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH."
            )
        except Exception as e:
            raise MediaProcessingError(f"Failed to create video segment: {e}")
    
    def _combine_videos(self, video_files: List[Path], output_path: Path) -> None:
        """
        Combine multiple video segments into final video.
        
        Args:
            video_files: List of video segment paths
            output_path: Path for final combined video
            
        Raises:
            MediaProcessingError: If video combination fails
        """
        if len(video_files) == 1:
            # Single video, just copy it
            try:
                import shutil
                shutil.copy2(video_files[0], output_path)
                return
            except Exception as e:
                raise MediaProcessingError(f"Failed to copy single video: {e}")
        
        # Create temporary file list for FFmpeg
        filelist_path = Path(tempfile.gettempdir()) / "temp_filelist.txt"
        
        try:
            # Write file list
            with open(filelist_path, 'w', encoding='utf-8') as f:
                for video_file in video_files:
                    # Use forward slashes for FFmpeg compatibility
                    f.write(f"file '{str(video_file).replace(os.sep, '/')}'\n")
            
            # FFmpeg command to concatenate videos
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite existing files
                '-f', 'concat',
                '-safe', '0',
                '-i', str(filelist_path),
                '-c', 'copy',  # Copy streams without re-encoding
                str(output_path)
            ]
            
            # Run FFmpeg command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                raise MediaProcessingError(f"Video combination failed: {result.stderr}")
            
            if not output_path.exists():
                raise MediaProcessingError(f"Final video not created: {output_path}")
            
        except subprocess.TimeoutExpired:
            raise MediaProcessingError("Video combination timed out")
        except Exception as e:
            raise MediaProcessingError(f"Failed to combine videos: {e}")
        finally:
            # Clean up file list
            if filelist_path.exists():
                try:
                    filelist_path.unlink()
                except Exception:
                    pass
    
    def _cleanup_temp_files(self, temp_files: List[Path]) -> None:
        """
        Remove temporary video files.
        
        Args:
            temp_files: List of temporary file paths to remove
        """
        for temp_file in temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                # Ignore cleanup errors
                pass
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe file system usage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = re.sub(r'\s+', '_', sanitized)
        sanitized = re.sub(r'_+', '_', sanitized).strip('_')
        
        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100].rstrip('_')
        
        return sanitized or 'presentation'