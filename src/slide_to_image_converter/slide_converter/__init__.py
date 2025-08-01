"""
Slide to Image Converter

A clean, minimal Python utility for converting Markdown slides to PNG images.
"""

from .processor import SlideProcessor
from .markdown_converter import MarkdownConverter
from .html_renderer import HTMLRenderer
from .config import Config
from .exceptions import SlideConverterError

__version__ = "1.0.0"
__all__ = [
    "SlideProcessor",
    "MarkdownConverter", 
    "HTMLRenderer",
    "Config",
    "SlideConverterError"
]