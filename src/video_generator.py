#!/usr/bin/env python3
"""
Create MP4 video from JSON presentation with images and audio
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

class VideoGenerator:
    """Class for creating video from presentation"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def create_video_from_presentation(self, json_file_path: str, output_video_path: str = None) -> str:
        """
        Creates MP4 video from JSON presentation
        
        Args:
            json_file_path: Path to presentation JSON file
            output_video_path: Path for output video (optional)
            
        Returns:
            str: Path to created video file
        """
        
        # Read JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            presentation_data = json.load(f)
        
        # Set output video path
        if output_video_path is None:
            base_name = os.path.splitext(os.path.basename(json_file_path))[0]
            output_dir = os.path.dirname(json_file_path)
            output_video_path = os.path.join(output_dir, f"{base_name}_video.mp4")
        
        # Validate data
        slides = presentation_data.get('slides', [])
        if not slides:
            raise ValueError("No slides found in presentation")
        
        # Create video segments for each slide
        temp_videos = []
        base_dir = os.path.dirname(json_file_path)
        
        for i, slide in enumerate(slides):
            # Check for image and audio paths (try both possible field names)
            image_path = slide.get('image_path') or slide.get('slide_image_path')
            audio_path = slide.get('audio_path')
            
            if not image_path or not audio_path:
                continue
            
            # Convert to full paths - handle paths that include base directory
            # Strip "output\" prefix if it exists in the path
            if image_path.startswith("output\\") or image_path.startswith("output/"):
                image_path = image_path[7:]  # Remove "output\" or "output/"
            if audio_path.startswith("output\\") or audio_path.startswith("output/"):
                audio_path = audio_path[7:]  # Remove "output\" or "output/"
                
            full_image_path = os.path.join(base_dir, image_path)
            full_audio_path = os.path.join(base_dir, audio_path)
            
            if not os.path.exists(full_image_path) or not os.path.exists(full_audio_path):
                continue
            
            # Create video segment for slide
            temp_video = self._create_slide_video(full_image_path, full_audio_path, i)
            if temp_video:
                temp_videos.append(temp_video)
        
        if not temp_videos:
            raise ValueError("No video segments created")
        
        # Combine all segments into one video
        final_video = self._combine_videos(temp_videos, output_video_path)
        
        # Clean up temporary files
        self._cleanup_temp_files(temp_videos)
        
        return final_video
    
    def _create_slide_video(self, image_path: str, audio_path: str, slide_index: int) -> str:
        """Creates video segment for single slide"""
        
        temp_video_path = f"temp_slide_{slide_index:02d}.mp4"
        
        try:
            # FFmpeg command to create video from image and audio
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite existing files
                '-loop', '1',  # Loop the image
                '-i', image_path,  # Image file
                '-i', audio_path,  # Audio file
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'aac',  # Audio codec
                '-b:a', '192k',  # Audio quality
                '-pix_fmt', 'yuv420p',  # Pixel format
                '-shortest',  # Video length based on audio
                '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',  # Scale to HD
                temp_video_path
            ]
            
            # Run command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return temp_video_path
            else:
                return None
                
        except FileNotFoundError:
            return None
        except Exception as e:
            return None
    
    def _combine_videos(self, video_files: list, output_path: str) -> str:
        """Combines multiple video segments into one file"""
        
        # Create file list for FFmpeg
        filelist_path = "temp_filelist.txt"
        
        try:
            with open(filelist_path, 'w') as f:
                for video_file in video_files:
                    f.write(f"file '{video_file}'\n")
            
            # FFmpeg command to concatenate files
            cmd = [
                'ffmpeg',
                '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', filelist_path,
                '-c', 'copy',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return output_path
            else:
                return None
                
        except Exception as e:
            return None
        finally:
            # Remove file list
            if os.path.exists(filelist_path):
                os.remove(filelist_path)
    
    def _cleanup_temp_files(self, temp_files: list):
        """Removes temporary files"""
        
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass

# Simple usage function
def create_video_from_json(json_file_path: str, output_video_path: str = None) -> str:
    """
    Simple function to create video from JSON presentation
    
    Args:
        json_file_path: Path to JSON presentation file
        output_video_path: Optional output path for video
        
    Returns:
        str: Path to created video file
    """
    generator = VideoGenerator()
    return generator.create_video_from_presentation(json_file_path, output_video_path)

if __name__ == '__main__':
    json_path = r"C:\Users\SHIRA\Documents\AI\Auto_curs\output\example_presentation_with_audio.json"
    path_out = create_video_from_json(json_file_path=json_path)