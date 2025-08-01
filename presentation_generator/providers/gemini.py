"""
Google Gemini LLM provider implementation.

This module provides integration with Google's Gemini AI models through
the LangChain Google GenAI integration.
"""

import time
from typing import Dict, Any, List, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from .base import LLMProvider
from ..utils.exceptions import ProviderError, ConfigurationError


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM provider implementation.
    
    This provider integrates with Google's Gemini AI models using the
    LangChain Google GenAI integration. It supports various Gemini models
    including Gemini 2.5 Flash and Gemini 1.5 Pro.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs):
        """
        Initialize the Gemini provider.
        
        Args:
            api_key: Google API key for Gemini access
            model: Specific Gemini model to use
            **kwargs: Additional configuration options:
                - temperature: Sampling temperature (0.0-2.0)
                - max_tokens: Maximum tokens in response
                - timeout: Request timeout in seconds
                - top_p: Nucleus sampling parameter
                - top_k: Top-k sampling parameter
        """
        super().__init__(api_key=api_key, model=model, **kwargs)
        self._client = None
        self._last_request_time = 0.0
        
        # Gemini-specific configuration
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens', 2048)
        self.timeout = kwargs.get('timeout', 30.0)
        self.top_p = kwargs.get('top_p', None)
        self.top_k = kwargs.get('top_k', None)
        
        # Rate limiting
        self.rate_limit_delay = kwargs.get('rate_limit_delay', 1.0)
    
    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "gemini"
    
    @property
    def default_model(self) -> str:
        """Return the default model for this provider."""
        return "gemini-2.5-flash"
    
    @property
    def supported_models(self) -> List[str]:
        """Return a list of supported models for this provider."""
        return [
            "gemini-2.5-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro",
            "gemini-pro-vision"
        ]
    
    def _validate_config(self) -> None:
        """Validate Gemini-specific configuration."""
        if not self.api_key:
            raise ConfigurationError(
                "Google API key is required for Gemini provider",
                field="api_key",
                details="Get your API key from https://makersuite.google.com/app/apikey"
            )
        
        if not self.api_key.strip():
            raise ConfigurationError(
                "Google API key cannot be empty",
                field="api_key"
            )
        
        # Validate model
        effective_model = self.get_effective_model()
        if effective_model not in self.supported_models:
            raise ConfigurationError(
                f"Unsupported Gemini model: {effective_model}",
                field="model",
                details=f"Supported models: {', '.join(self.supported_models)}"
            )
        
        # Validate parameters
        if not 0 <= self.temperature <= 2:
            raise ConfigurationError(
                f"Temperature must be between 0.0 and 2.0, got {self.temperature}",
                field="temperature"
            )
        
        if self.max_tokens <= 0:
            raise ConfigurationError(
                f"Max tokens must be positive, got {self.max_tokens}",
                field="max_tokens"
            )
        
        if self.timeout <= 0:
            raise ConfigurationError(
                f"Timeout must be positive, got {self.timeout}",
                field="timeout"
            )
    
    def _initialize_client(self) -> None:
        """Initialize the Gemini client."""
        if self._client is not None:
            return
        
        try:
            # Build client configuration
            client_config = {
                "model": self.get_effective_model(),
                "google_api_key": self.api_key,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "timeout": self.timeout
            }
            
            # Add optional parameters if specified
            if self.top_p is not None:
                client_config["top_p"] = self.top_p
            if self.top_k is not None:
                client_config["top_k"] = self.top_k
            
            self._client = ChatGoogleGenerativeAI(**client_config)
            
        except ImportError as e:
            raise ConfigurationError(
                "Google GenAI package not installed",
                details="Install with: pip install langchain-google-genai"
            ) from e
        except Exception as e:
            raise ProviderError(f"Failed to initialize Gemini client: {e}") from e
    
    def _respect_rate_limit(self) -> None:
        """Implement rate limiting to avoid API limits."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def generate_content(self, prompt: str, **kwargs) -> str:
        """
        Generate content using the Gemini provider.
        
        Args:
            prompt: The input prompt for content generation
            **kwargs: Additional generation parameters:
                - system_prompt: Optional system prompt
                - temperature: Override default temperature
                - max_tokens: Override default max tokens
                
        Returns:
            Generated content as a string
            
        Raises:
            ProviderError: If content generation fails
            ConfigurationError: If provider is not properly configured
        """
        self.validate_configuration()
        self._initialize_client()
        
        if not prompt or not prompt.strip():
            raise ProviderError("Prompt cannot be empty")
        
        try:
            # Respect rate limiting
            self._respect_rate_limit()
            
            # Build messages
            messages = []
            
            # Add system prompt if provided
            system_prompt = kwargs.get('system_prompt')
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            
            # Add main prompt
            messages.append(HumanMessage(content=prompt.strip()))
            
            # Override client parameters if specified
            generation_kwargs = {}
            if 'temperature' in kwargs:
                generation_kwargs['temperature'] = kwargs['temperature']
            if 'max_tokens' in kwargs:
                generation_kwargs['max_tokens'] = kwargs['max_tokens']
            
            # Make the API call
            if generation_kwargs:
                # Create a temporary client with overridden parameters
                temp_config = {
                    "model": self.get_effective_model(),
                    "google_api_key": self.api_key,
                    "temperature": generation_kwargs.get('temperature', self.temperature),
                    "max_tokens": generation_kwargs.get('max_tokens', self.max_tokens),
                    "timeout": self.timeout
                }
                temp_client = ChatGoogleGenerativeAI(**temp_config)
                response = temp_client.invoke(messages)
            else:
                response = self._client.invoke(messages)
            
            if not response or not response.content:
                raise ProviderError("Empty response from Gemini API")
            
            content = response.content.strip()
            if not content:
                raise ProviderError("Empty content in Gemini response")
            
            return content
            
        except Exception as e:
            if "API key" in str(e).lower():
                raise ConfigurationError(
                    "Invalid or expired Google API key",
                    field="api_key",
                    details=str(e)
                ) from e
            elif "quota" in str(e).lower() or "rate limit" in str(e).lower():
                raise ProviderError(
                    f"Gemini API rate limit or quota exceeded: {e}"
                ) from e
            elif "timeout" in str(e).lower():
                raise ProviderError(
                    f"Gemini API request timeout: {e}"
                ) from e
            else:
                raise ProviderError(f"Gemini API error: {e}") from e
    
    def test_connection(self) -> bool:
        """
        Test the connection to the Gemini provider.
        
        Returns:
            True if connection is successful, False otherwise
            
        Raises:
            ProviderError: If connection test fails with an error
        """
        try:
            self.validate_configuration()
            self._initialize_client()
            
            # Simple test prompt
            test_response = self.generate_content(
                "Respond with exactly: 'Connection successful'",
                temperature=0.0,
                max_tokens=10
            )
            
            return "successful" in test_response.lower()
            
        except (ConfigurationError, ProviderError):
            return False
        except Exception as e:
            raise ProviderError(f"Connection test failed: {e}") from e
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary containing model information
            
        Raises:
            ProviderError: If model information cannot be retrieved
        """
        try:
            self.validate_configuration()
            
            model = self.get_effective_model()
            
            # Model-specific information
            model_info = {
                "name": model,
                "provider": self.provider_name,
                "type": "chat",
                "context_window": self._get_context_window(model),
                "supports_vision": "vision" in model.lower(),
                "supports_function_calling": model in ["gemini-1.5-pro", "gemini-2.5-flash"],
                "configuration": {
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "timeout": self.timeout,
                    "top_p": self.top_p,
                    "top_k": self.top_k
                }
            }
            
            return model_info
            
        except Exception as e:
            raise ProviderError(f"Failed to get model info: {e}") from e
    
    def _get_context_window(self, model: str) -> int:
        """Get the context window size for a specific model."""
        context_windows = {
            "gemini-2.5-flash": 1048576,  # 1M tokens
            "gemini-1.5-pro": 2097152,    # 2M tokens
            "gemini-1.5-flash": 1048576,  # 1M tokens
            "gemini-pro": 32768,          # 32K tokens
            "gemini-pro-vision": 16384    # 16K tokens
        }
        return context_windows.get(model, 32768)  # Default to 32K
    
    def get_usage_info(self) -> Dict[str, Any]:
        """
        Get usage information and statistics.
        
        Returns:
            Dictionary containing usage statistics
        """
        return {
            "provider": self.provider_name,
            "model": self.get_effective_model(),
            "last_request_time": self._last_request_time,
            "rate_limit_delay": self.rate_limit_delay,
            "client_initialized": self._client is not None
        }


# Register the provider with the factory
from .base import ProviderFactory
ProviderFactory.register_provider("gemini", GeminiProvider)