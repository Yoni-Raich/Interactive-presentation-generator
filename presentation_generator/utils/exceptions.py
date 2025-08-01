"""
Custom exception classes for the presentation generator library.

This module defines a hierarchy of exceptions that provide clear error
messages and context for different types of failures that can occur
during presentation generation.
"""


class PresentationGeneratorError(Exception):
    """
    Base exception for all presentation generator errors.
    
    All custom exceptions in the library inherit from this base class,
    making it easy to catch any library-specific error.
    """
    
    def __init__(self, message: str, details: str = None):
        """
        Initialize the exception with a message and optional details.
        
        Args:
            message: The main error message
            details: Additional details about the error (optional)
        """
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self):
        """Return a formatted error message."""
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message


class ConfigurationError(PresentationGeneratorError):
    """
    Raised when there are configuration or setup related errors.
    
    This includes invalid configuration values, missing API keys,
    invalid provider settings, or other setup issues.
    """
    pass


class ContentGenerationError(PresentationGeneratorError):
    """
    Raised when LLM content generation fails.
    
    This includes API failures, invalid responses, content validation
    failures, or other issues during the content generation phase.
    """
    
    def __init__(self, message: str, provider: str = None, details: str = None):
        """
        Initialize with provider-specific context.
        
        Args:
            message: The main error message
            provider: The LLM provider that failed (optional)
            details: Additional details about the error (optional)
        """
        super().__init__(message, details)
        self.provider = provider

    def __str__(self):
        """Return a formatted error message with provider info."""
        base_msg = super().__str__()
        if self.provider:
            return f"[{self.provider}] {base_msg}"
        return base_msg


class MediaProcessingError(PresentationGeneratorError):
    """
    Raised when image, audio, or video processing fails.
    
    This includes slide-to-image conversion failures, TTS generation
    issues, video assembly problems, or other media processing errors.
    """
    
    def __init__(self, message: str, media_type: str = None, details: str = None):
        """
        Initialize with media type context.
        
        Args:
            message: The main error message
            media_type: The type of media being processed (image, audio, video)
            details: Additional details about the error (optional)
        """
        super().__init__(message, details)
        self.media_type = media_type

    def __str__(self):
        """Return a formatted error message with media type info."""
        base_msg = super().__str__()
        if self.media_type:
            return f"[{self.media_type}] {base_msg}"
        return base_msg


class ProviderError(PresentationGeneratorError):
    """
    Raised when there are LLM provider specific errors.
    
    This includes authentication failures, rate limiting, model
    unavailability, or other provider-specific issues.
    """
    
    def __init__(self, message: str, provider: str, error_code: str = None, details: str = None):
        """
        Initialize with provider-specific context.
        
        Args:
            message: The main error message
            provider: The LLM provider that failed
            error_code: Provider-specific error code (optional)
            details: Additional details about the error (optional)
        """
        super().__init__(message, details)
        self.provider = provider
        self.error_code = error_code

    def __str__(self):
        """Return a formatted error message with provider and error code info."""
        base_msg = super().__str__()
        provider_info = f"[{self.provider}"
        if self.error_code:
            provider_info += f":{self.error_code}"
        provider_info += "]"
        return f"{provider_info} {base_msg}"


class WorkflowError(PresentationGeneratorError):
    """
    Raised when there are workflow orchestration errors.
    
    This includes step coordination failures, resource management
    issues, or other problems in the overall workflow execution.
    """
    
    def __init__(self, message: str, step: str = None, details: str = None):
        """
        Initialize with workflow step context.
        
        Args:
            message: The main error message
            step: The workflow step that failed (optional)
            details: Additional details about the error (optional)
        """
        super().__init__(message, details)
        self.step = step

    def __str__(self):
        """Return a formatted error message with step info."""
        base_msg = super().__str__()
        if self.step:
            return f"[{self.step}] {base_msg}"
        return base_msg


class ValidationError(PresentationGeneratorError):
    """
    Raised when data validation fails.
    
    This includes invalid input data, malformed content, or other
    validation failures during processing.
    """
    
    def __init__(self, message: str, field: str = None, value: str = None, details: str = None):
        """
        Initialize with validation context.
        
        Args:
            message: The main error message
            field: The field that failed validation (optional)
            value: The invalid value (optional)
            details: Additional details about the error (optional)
        """
        super().__init__(message, details)
        self.field = field
        self.value = value

    def __str__(self):
        """Return a formatted error message with validation context."""
        base_msg = super().__str__()
        if self.field:
            context = f"[{self.field}"
            if self.value:
                context += f"={self.value}"
            context += "]"
            return f"{context} {base_msg}"
        return base_msg