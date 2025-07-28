"""
Prompt templates package for presentation generation.

This package contains all prompt templates used for generating presentation content
including sub-subjects, slide content, and talking scripts.
"""

from .sub_subject_prompts import SubSubjectPrompts
from .slide_prompts import SlidePrompts
from .script_prompts import ScriptPrompts

__all__ = [
    'SubSubjectPrompts',
    'SlidePrompts', 
    'ScriptPrompts'
]