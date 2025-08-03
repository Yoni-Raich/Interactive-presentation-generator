"""
Presentation Generator Library

A clean Python library for generating complete presentations programmatically.
Provides the complete workflow: Topic Input → Content Generation → Slide Creation → 
Image Rendering → Audio Generation → Video Assembly.

Basic Usage:
    from presentation_generator import PresentationGenerator, Config
    
    # Simple usage - generates complete video presentation
    generator = PresentationGenerator()
    presentation = generator.generate("Machine Learning Basics")
    print(f"Video created: {presentation.video_path}")
    
    # Advanced usage with configuration
    config = Config(
        llm_provider="gemini",
        api_key="your-key",
        output_dir="./presentations"
    )
    generator = PresentationGenerator(config)
    presentation = generator.generate("AI Ethics")
"""

# Core classes - main public API
from .core.generator import PresentationGenerator
from .models.data import Slide, Presentation, PresentationResult
from .utils.config import Config, load_config

# Exception classes for error handling
from .utils.exceptions import (
    PresentationGeneratorError,
    ConfigurationError,
    ContentGenerationError,
    MediaProcessingError,
    ProviderError,
    ValidationError,
    WorkflowError
)

# Library metadata
__version__ = "1.0.0"
__author__ = "Presentation Generator Team"
__description__ = "A clean Python library for generating complete presentations programmatically"

# Public API exports - only expose what users need
__all__ = [
    # Main classes
    "PresentationGenerator",
    "Config",
    
    # Data models
    "Slide",
    "Presentation", 
    "PresentationResult",
    
    # Configuration utilities
    "load_config",
    
    # Exception classes
    "PresentationGeneratorError",
    "ConfigurationError",
    "ContentGenerationError",
    "MediaProcessingError",
    "ProviderError",
    "ValidationError",
    "WorkflowError",
]

# Convenience functions for quick access
def create_generator(provider: str = "gemini", api_key: str = None, **kwargs) -> PresentationGenerator:
    """
    Create a PresentationGenerator with simplified configuration.
    
    Args:
        provider: LLM provider to use (gemini, openai, anthropic, ollama)
        api_key: API key for the provider (not needed for ollama)
        **kwargs: Additional configuration options
        
    Returns:
        Configured PresentationGenerator instance
        
    Example:
        generator = create_generator("gemini", "your-api-key")
        presentation = generator.generate("Python Basics")
    """
    config = Config(llm_provider=provider, api_key=api_key, **kwargs)
    return PresentationGenerator(config)

def quick_generate(topic: str, provider: str = "gemini", api_key: str = None, **kwargs) -> PresentationResult:
    """
    Generate a presentation with minimal setup.
    
    Args:
        topic: The presentation topic
        provider: LLM provider to use (gemini, openai, anthropic, ollama)
        api_key: API key for the provider (not needed for ollama)
        **kwargs: Additional configuration options
        
    Returns:
        PresentationResult with the generated presentation
        
    Example:
        result = quick_generate("Machine Learning", "gemini", "your-api-key")
        print(f"Video: {result.presentation.video_path}")
    """
    generator = create_generator(provider, api_key, **kwargs)
    return generator.generate(topic)

def get_supported_providers() -> list[str]:
    """
    Get list of supported LLM providers.
    
    Returns:
        List of supported provider names
        
    Example:
        providers = get_supported_providers()
        print(f"Available providers: {providers}")
    """
    from .providers.base import ProviderFactory
    return ProviderFactory.get_available_providers()

# Add convenience functions to __all__
__all__.extend([
    "create_generator",
    "quick_generate", 
    "get_supported_providers"
])

# Clean up namespace - remove internal modules and imports from public API
# This hides internal implementation details from users
import sys as _sys

# Remove internal module references from the namespace
_internal_modules = ['core', 'media', 'models', 'providers', 'utils']
_current_module = _sys.modules[__name__]

for _module_name in _internal_modules:
    if hasattr(_current_module, _module_name):
        delattr(_current_module, _module_name)

# Clean up temporary variables
del _internal_modules, _current_module, _module_name, _sys