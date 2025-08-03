"""
Centralized prompt management for the presentation generator library.

This module provides a clean interface for accessing all prompts used throughout
the library, making them easy to maintain, version, and customize.
"""

from .content_generation import ContentPrompts
from .slide_generation import SlidePrompts
from .provider_prompts import ProviderPrompts
from .validation_prompts import ValidationPrompts

__all__ = [
    "ContentPrompts",
    "SlidePrompts", 
    "ProviderPrompts",
    "ValidationPrompts"
]