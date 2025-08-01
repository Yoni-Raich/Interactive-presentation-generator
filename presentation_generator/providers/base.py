"""
Abstract base provider interface and factory for LLM providers.

This module defines the common interface that all LLM providers must implement,
along with a factory pattern for dynamic provider instantiation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, List
from enum import Enum

from ..utils.exceptions import ProviderError, ConfigurationError


class ProviderType(Enum):
    """Enumeration of supported LLM provider types."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    
    This class defines the common interface that all LLM provider implementations
    must follow, ensuring consistent behavior across different providers.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs):
        """
        Initialize the provider with configuration.
        
        Args:
            api_key: API key for the provider (if required)
            model: Model name to use (provider-specific)
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs
        self._validated = False

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider."""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Return a list of supported models for this provider."""
        pass

    @abstractmethod
    def generate_content(self, prompt: str, **kwargs) -> str:
        """
        Generate content using the LLM provider.
        
        Args:
            prompt: The input prompt for content generation
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated content as a string
            
        Raises:
            ProviderError: If content generation fails
            ConfigurationError: If provider is not properly configured
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the connection to the provider.
        
        Returns:
            True if connection is successful, False otherwise
            
        Raises:
            ProviderError: If connection test fails with an error
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary containing model information (name, version, capabilities, etc.)
            
        Raises:
            ProviderError: If model information cannot be retrieved
        """
        pass

    def validate_configuration(self) -> None:
        """
        Validate the provider configuration.
        
        This method should be called before using the provider to ensure
        all required configuration is present and valid.
        
        Raises:
            ConfigurationError: If configuration is invalid or incomplete
        """
        if not self._validated:
            self._validate_config()
            self._validated = True

    @abstractmethod
    def _validate_config(self) -> None:
        """
        Internal method to validate provider-specific configuration.
        
        Subclasses should implement this to validate their specific requirements.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        pass

    def get_effective_model(self) -> str:
        """
        Get the model that will be used for generation.
        
        Returns the configured model or the default model if none is specified.
        
        Returns:
            The model name that will be used
        """
        return self.model or self.default_model

    def is_configured(self) -> bool:
        """
        Check if the provider is properly configured.
        
        Returns:
            True if the provider is configured and ready to use
        """
        try:
            self.validate_configuration()
            return True
        except (ConfigurationError, ProviderError):
            return False

    def __str__(self) -> str:
        """Return a string representation of the provider."""
        return f"{self.provider_name}(model={self.get_effective_model()})"

    def __repr__(self) -> str:
        """Return a detailed string representation of the provider."""
        return (
            f"{self.__class__.__name__}("
            f"provider_name='{self.provider_name}', "
            f"model='{self.get_effective_model()}', "
            f"configured={self.is_configured()})"
        )


class ProviderFactory:
    """
    Factory class for creating LLM provider instances.
    
    This factory provides a centralized way to create and manage different
    LLM provider implementations, supporting dynamic provider selection
    and configuration.
    """
    
    _providers: Dict[str, Type[LLMProvider]] = {}
    _instances: Dict[str, LLMProvider] = {}

    @classmethod
    def register_provider(cls, provider_type: str, provider_class: Type[LLMProvider]) -> None:
        """
        Register a new provider implementation.
        
        Args:
            provider_type: The provider type identifier (e.g., "gemini", "openai")
            provider_class: The provider class to register
            
        Raises:
            ValueError: If provider_type is already registered
        """
        if provider_type in cls._providers:
            raise ValueError(f"Provider '{provider_type}' is already registered")
        
        if not issubclass(provider_class, LLMProvider):
            raise ValueError(f"Provider class must inherit from LLMProvider")
        
        cls._providers[provider_type] = provider_class

    @classmethod
    def create_provider(
        cls, 
        provider_type: str, 
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """
        Create a new provider instance.
        
        Args:
            provider_type: The type of provider to create
            api_key: API key for the provider (if required)
            model: Model name to use
            **kwargs: Additional provider-specific configuration
            
        Returns:
            A configured provider instance
            
        Raises:
            ConfigurationError: If provider type is not supported or configuration is invalid
        """
        if provider_type not in cls._providers:
            available = ", ".join(cls.get_available_providers())
            raise ConfigurationError(
                f"Unsupported provider type: '{provider_type}'",
                f"Available providers: {available}"
            )
        
        provider_class = cls._providers[provider_type]
        
        try:
            provider = provider_class(api_key=api_key, model=model, **kwargs)
            provider.validate_configuration()
            return provider
        except Exception as e:
            raise ConfigurationError(
                f"Failed to create provider '{provider_type}'",
                str(e)
            )

    @classmethod
    def get_provider(
        cls,
        provider_type: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ) -> LLMProvider:
        """
        Get a provider instance, optionally using caching.
        
        Args:
            provider_type: The type of provider to get
            api_key: API key for the provider (if required)
            model: Model name to use
            use_cache: Whether to use cached instances
            **kwargs: Additional provider-specific configuration
            
        Returns:
            A provider instance
            
        Raises:
            ConfigurationError: If provider cannot be created
        """
        if not use_cache:
            return cls.create_provider(provider_type, api_key, model, **kwargs)
        
        # Create cache key based on configuration
        cache_key = f"{provider_type}:{model or 'default'}:{hash(str(sorted(kwargs.items())))}"
        
        if cache_key not in cls._instances:
            cls._instances[cache_key] = cls.create_provider(
                provider_type, api_key, model, **kwargs
            )
        
        return cls._instances[cache_key]

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """
        Get a list of available provider types.
        
        Returns:
            List of registered provider type names
        """
        return list(cls._providers.keys())

    @classmethod
    def is_provider_available(cls, provider_type: str) -> bool:
        """
        Check if a provider type is available.
        
        Args:
            provider_type: The provider type to check
            
        Returns:
            True if the provider is available
        """
        return provider_type in cls._providers

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the provider instance cache."""
        cls._instances.clear()

    @classmethod
    def get_provider_info(cls, provider_type: str) -> Dict[str, Any]:
        """
        Get information about a provider type.
        
        Args:
            provider_type: The provider type to get info for
            
        Returns:
            Dictionary with provider information
            
        Raises:
            ConfigurationError: If provider type is not available
        """
        if provider_type not in cls._providers:
            raise ConfigurationError(f"Provider '{provider_type}' is not available")
        
        provider_class = cls._providers[provider_type]
        
        # Create a temporary instance to get info (without validation)
        try:
            temp_provider = provider_class()
            return {
                "name": temp_provider.provider_name,
                "default_model": temp_provider.default_model,
                "supported_models": temp_provider.supported_models,
                "class": provider_class.__name__,
                "module": provider_class.__module__
            }
        except Exception as e:
            return {
                "name": provider_type,
                "error": f"Could not get provider info: {str(e)}",
                "class": provider_class.__name__,
                "module": provider_class.__module__
            }


# Convenience function for creating providers
def create_provider(
    provider_type: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Convenience function to create a provider instance.
    
    Args:
        provider_type: The type of provider to create
        api_key: API key for the provider (if required)
        model: Model name to use
        **kwargs: Additional provider-specific configuration
        
    Returns:
        A configured provider instance
    """
    return ProviderFactory.create_provider(provider_type, api_key, model, **kwargs)