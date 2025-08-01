"""
Core presentation generation components.

This module contains the core logic for presentation generation,
including content generation, workflow management, and orchestration.
"""

from .content import ContentGenerator, GenerationProgress

__all__ = [
    'ContentGenerator',
    'GenerationProgress'
]