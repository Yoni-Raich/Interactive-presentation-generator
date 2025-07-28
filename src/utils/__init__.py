"""Utility modules for the presentation generator."""

from .config import Config, load_config
from .logger import StructuredLogger, get_logger, setup_application_logging
from .exceptions import (
    PresentationGeneratorError,
    InputValidationError,
    ConfigurationError,
    APIConnectionError,
    ContentGenerationError,
    FileOperationError,
    JSONSerializationError,
    RetryExhaustedError,
    categorize_error,
    get_user_friendly_message
)

__all__ = [
    "Config",
    "load_config",
    "StructuredLogger",
    "get_logger",
    "setup_application_logging",
    "PresentationGeneratorError",
    "InputValidationError",
    "ConfigurationError",
    "APIConnectionError",
    "ContentGenerationError",
    "FileOperationError",
    "JSONSerializationError",
    "RetryExhaustedError",
    "categorize_error",
    "get_user_friendly_message"
]