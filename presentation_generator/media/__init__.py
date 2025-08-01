"""
Media processing components for presentation generation.

This module provides components for processing different types of media:
- Image generation from slide content
- Audio generation from text scripts with duration calculation
- Video assembly from images and audio
"""

from .images import ImageProcessor
from .audio import AudioProcessor
from .video import VideoProcessor

__all__ = ['ImageProcessor', 'AudioProcessor', 'VideoProcessor']