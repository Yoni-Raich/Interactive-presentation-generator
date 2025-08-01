"""
Slide to Image Converter

A clean, minimal Python utility for converting Markdown slides to PNG images.
"""

from .slide_converter.processor import SlideProcessor
from .slide_converter.markdown_converter import MarkdownConverter
from .slide_converter.html_renderer import HTMLRenderer
from .slide_converter.config import Config
from .slide_converter.exceptions import SlideConverterError

__version__ = "1.0.0"
__all__ = [
    "SlideProcessor",
    "MarkdownConverter", 
    "HTMLRenderer",
    "Config",
    "SlideConverterError"
]