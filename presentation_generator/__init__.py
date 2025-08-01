"""
Presentation Generator Library

A clean Python library for generating complete presentations programmatically.
Provides the complete workflow: Topic Input → Content Generation → Slide Creation → 
Image Rendering → Audio Generation → Video Assembly.
"""

from .core.generator import PresentationGenerator
from .models.data import Slide, Presentation, PresentationResult
from .utils.config import Config, load_config
from .utils.exceptions import (
    PresentationGeneratorError,
    ConfigurationError,
    ContentGenerationError,
    MediaProcessingError,
    ProviderError
)

__version__ = "1.0.0"
__all__ = [
    "PresentationGenerator",
    "Slide",
    "Presentation", 
    "PresentationResult",
    "Config",
    "load_config",
    "PresentationGeneratorError",
    "ConfigurationError",
    "ContentGenerationError",
    "MediaProcessingError",
    "ProviderError"
]