"""
Exception classes for slide converter.
"""


class SlideConverterError(Exception):
    """Base exception for slide converter operations."""
    
    def __init__(self, message: str, suggested_fix: str = None):
        super().__init__(message)
        self.message = message
        self.suggested_fix = suggested_fix
    
    def __str__(self) -> str:
        error_msg = self.message
        if self.suggested_fix:
            error_msg += f"\nSuggested fix: {self.suggested_fix}"
        return error_msg


class MarkdownError(SlideConverterError):
    """Raised when Markdown conversion fails."""
    pass


class RenderError(SlideConverterError):
    """Raised when HTML rendering fails."""
    pass


class ValidationError(SlideConverterError):
    """Raised when input validation fails."""
    pass