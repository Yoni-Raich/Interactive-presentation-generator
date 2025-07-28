"""Custom exception classes for the presentation generator."""

from typing import Optional, Any


class PresentationGeneratorError(Exception):
    """Base exception class for all presentation generator errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[dict] = None):
        """Initialize the exception.
        
        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class InputValidationError(PresentationGeneratorError):
    """Raised when user input validation fails."""
    
    def __init__(self, message: str, input_value: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="INPUT_VALIDATION_ERROR",
            details={"input_value": input_value}
        )


class ConfigurationError(PresentationGeneratorError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key}
        )


class APIConnectionError(PresentationGeneratorError):
    """Raised when API connection or communication fails."""
    
    def __init__(self, message: str, api_name: str = "Gemini", status_code: Optional[int] = None):
        super().__init__(
            message=message,
            error_code="API_CONNECTION_ERROR",
            details={"api_name": api_name, "status_code": status_code}
        )


class ContentGenerationError(PresentationGeneratorError):
    """Raised when content generation fails."""
    
    def __init__(self, message: str, generation_step: str, retry_count: int = 0):
        super().__init__(
            message=message,
            error_code="CONTENT_GENERATION_ERROR",
            details={"generation_step": generation_step, "retry_count": retry_count}
        )


class FileOperationError(PresentationGeneratorError):
    """Raised when file I/O operations fail."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, operation: str = "unknown"):
        super().__init__(
            message=message,
            error_code="FILE_OPERATION_ERROR",
            details={"file_path": file_path, "operation": operation}
        )


class JSONSerializationError(PresentationGeneratorError):
    """Raised when JSON serialization or validation fails."""
    
    def __init__(self, message: str, data_type: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="JSON_SERIALIZATION_ERROR",
            details={"data_type": data_type}
        )


class RetryExhaustedError(PresentationGeneratorError):
    """Raised when maximum retry attempts are exceeded."""
    
    def __init__(self, message: str, operation: str, max_retries: int, last_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code="RETRY_EXHAUSTED_ERROR",
            details={
                "operation": operation,
                "max_retries": max_retries,
                "last_error": str(last_error) if last_error else None
            }
        )


def categorize_error(error: Exception) -> str:
    """Categorize an error for logging and handling purposes.
    
    Args:
        error: The exception to categorize
        
    Returns:
        String category of the error
    """
    if isinstance(error, InputValidationError):
        return "USER_INPUT"
    elif isinstance(error, ConfigurationError):
        return "CONFIGURATION"
    elif isinstance(error, APIConnectionError):
        return "API_CONNECTION"
    elif isinstance(error, ContentGenerationError):
        return "CONTENT_GENERATION"
    elif isinstance(error, FileOperationError):
        return "FILE_OPERATION"
    elif isinstance(error, JSONSerializationError):
        return "JSON_SERIALIZATION"
    elif isinstance(error, RetryExhaustedError):
        return "RETRY_EXHAUSTED"
    elif isinstance(error, PresentationGeneratorError):
        return "PRESENTATION_GENERATOR"
    else:
        return "UNKNOWN"


def get_user_friendly_message(error: Exception) -> str:
    """Get a user-friendly error message.
    
    Args:
        error: The exception to get a message for
        
    Returns:
        User-friendly error message
    """
    if isinstance(error, InputValidationError):
        return f"Invalid input: {error.message}"
    elif isinstance(error, ConfigurationError):
        return f"Configuration error: {error.message}"
    elif isinstance(error, APIConnectionError):
        return f"Unable to connect to AI service: {error.message}"
    elif isinstance(error, ContentGenerationError):
        return f"Failed to generate content: {error.message}"
    elif isinstance(error, FileOperationError):
        return f"File operation failed: {error.message}"
    elif isinstance(error, JSONSerializationError):
        return f"Data formatting error: {error.message}"
    elif isinstance(error, RetryExhaustedError):
        return f"Operation failed after multiple attempts: {error.message}"
    elif isinstance(error, PresentationGeneratorError):
        return error.message
    else:
        return f"An unexpected error occurred: {str(error)}"