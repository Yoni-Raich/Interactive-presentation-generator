"""
OpenAI LLM provider implementation.

This module provides integration with OpenAI's GPT models through
the LangChain OpenAI integration.
"""

import time
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from .base import LLMProvider
from ..utils.exceptions import ProviderError, ConfigurationError


class OpenAIProvider(LLMProvider):
    """
    OpenAI LLM provider implementation.
    
    This provider integrates with OpenAI's GPT models using the
    LangChain OpenAI integration. It supports various GPT models
    including GPT-4, GPT-4 Turbo, and GPT-3.5 Turbo.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Specific OpenAI model to use
            **kwargs: Additional configuration options:
                - temperature: Sampling temperature (0.0-2.0)
                - max_tokens: Maximum tokens in response
                - timeout: Request timeout in seconds
                - top_p: Nucleus sampling parameter
                - frequency_penalty: Frequency penalty (-2.0 to 2.0)
                - presence_penalty: Presence penalty (-2.0 to 2.0)
                - organization: OpenAI organization ID
        """
        super().__init__(api_key=api_key, model=model, **kwargs)
        self._client = None
        self._last_request_time = 0.0
        
        # OpenAI-specific configuration
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens', 2048)
        self.timeout = kwargs.get('timeout', 30.0)
        self.top_p = kwargs.get('top_p', None)
        self.frequency_penalty = kwargs.get('frequency_penalty', 0.0)
        self.presence_penalty = kwargs.get('presence_penalty', 0.0)
        self.organization = kwargs.get('organization', None)
        
        # Rate limiting
        self.rate_limit_delay = kwargs.get('rate_limit_delay', 1.0)
    
    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "openai"
    
    @property
    def default_model(self) -> str:
        """Return the default model for this provider."""
        return "gpt-4"
    
    @property
    def supported_models(self) -> List[str]:
        """Return a list of supported models for this provider."""
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4-0125-preview",
            "gpt-4-1106-preview",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-0125",
            "gpt-3.5-turbo-1106",
            "gpt-4o",
            "gpt-4o-mini"
        ]
    
    def _validate_config(self) -> None:
        """Validate OpenAI-specific configuration."""
        if not self.api_key:
            raise ConfigurationError(
                "OpenAI API key is required",
                field="api_key",
                details="Get your API key from https://platform.openai.com/api-keys"
            )
        
        if not self.api_key.strip():
            raise ConfigurationError(
                "OpenAI API key cannot be empty",
                field="api_key"
            )
        
        # Basic API key format validation
        if not self.api_key.startswith(('sk-', 'sk-proj-')):
            raise ConfigurationError(
                "OpenAI API key should start with 'sk-' or 'sk-proj-'",
                field="api_key"
            )
        
        # Validate model
        effective_model = self.get_effective_model()
        if effective_model not in self.supported_models:
            raise ConfigurationError(
                f"Unsupported OpenAI model: {effective_model}",
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
        
        if not -2.0 <= self.frequency_penalty <= 2.0:
            raise ConfigurationError(
                f"Frequency penalty must be between -2.0 and 2.0, got {self.frequency_penalty}",
                field="frequency_penalty"
            )
        
        if not -2.0 <= self.presence_penalty <= 2.0:
            raise ConfigurationError(
                f"Presence penalty must be between -2.0 and 2.0, got {self.presence_penalty}",
                field="presence_penalty"
            )
    
    def _initialize_client(self) -> None:
        """Initialize the OpenAI client."""
        if self._client is not None:
            return
        
        try:
            # Build client configuration
            client_config = {
                "model": self.get_effective_model(),
                "openai_api_key": self.api_key,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "timeout": self.timeout,
                "frequency_penalty": self.frequency_penalty,
                "presence_penalty": self.presence_penalty
            }
            
            # Add optional parameters if specified
            if self.top_p is not None:
                client_config["top_p"] = self.top_p
            if self.organization:
                client_config["openai_organization"] = self.organization
            
            self._client = ChatOpenAI(**client_config)
            
        except ImportError as e:
            raise ConfigurationError(
                "OpenAI package not installed",
                details="Install with: pip install langchain-openai"
            ) from e
        except Exception as e:
            raise ProviderError(f"Failed to initialize OpenAI client: {e}") from e
    
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
        Generate content using the OpenAI provider.
        
        Args:
            prompt: The input prompt for content generation
            **kwargs: Additional generation parameters:
                - system_prompt: Optional system prompt
                - temperature: Override default temperature
                - max_tokens: Override default max tokens
                - top_p: Override default top_p
                - frequency_penalty: Override default frequency penalty
                - presence_penalty: Override default presence penalty
                
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
            for param in ['temperature', 'max_tokens', 'top_p', 'frequency_penalty', 'presence_penalty']:
                if param in kwargs:
                    generation_kwargs[param] = kwargs[param]
            
            # Make the API call
            if generation_kwargs:
                # Create a temporary client with overridden parameters
                temp_config = {
                    "model": self.get_effective_model(),
                    "openai_api_key": self.api_key,
                    "temperature": generation_kwargs.get('temperature', self.temperature),
                    "max_tokens": generation_kwargs.get('max_tokens', self.max_tokens),
                    "timeout": self.timeout,
                    "frequency_penalty": generation_kwargs.get('frequency_penalty', self.frequency_penalty),
                    "presence_penalty": generation_kwargs.get('presence_penalty', self.presence_penalty)
                }
                if 'top_p' in generation_kwargs:
                    temp_config['top_p'] = generation_kwargs['top_p']
                if self.organization:
                    temp_config['openai_organization'] = self.organization
                
                temp_client = ChatOpenAI(**temp_config)
                response = temp_client.invoke(messages)
            else:
                response = self._client.invoke(messages)
            
            if not response or not response.content:
                raise ProviderError("Empty response from OpenAI API")
            
            content = response.content.strip()
            if not content:
                raise ProviderError("Empty content in OpenAI response")
            
            return content
            
        except Exception as e:
            error_str = str(e).lower()
            if "api key" in error_str or "unauthorized" in error_str:
                raise ConfigurationError(
                    "Invalid or expired OpenAI API key",
                    field="api_key",
                    details=str(e)
                ) from e
            elif "quota" in error_str or "rate limit" in error_str:
                raise ProviderError(
                    f"OpenAI API rate limit or quota exceeded: {e}"
                ) from e
            elif "timeout" in error_str:
                raise ProviderError(
                    f"OpenAI API request timeout: {e}"
                ) from e
            elif "model" in error_str and "not found" in error_str:
                raise ConfigurationError(
                    f"OpenAI model not found or not accessible: {self.get_effective_model()}",
                    field="model",
                    details=str(e)
                ) from e
            else:
                raise ProviderError(f"OpenAI API error: {e}") from e
    
    def test_connection(self) -> bool:
        """
        Test the connection to the OpenAI provider.
        
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
                "supports_vision": model in ["gpt-4o", "gpt-4-turbo", "gpt-4-vision-preview"],
                "supports_function_calling": True,  # All supported models support function calling
                "training_cutoff": self._get_training_cutoff(model),
                "configuration": {
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "timeout": self.timeout,
                    "top_p": self.top_p,
                    "frequency_penalty": self.frequency_penalty,
                    "presence_penalty": self.presence_penalty,
                    "organization": self.organization
                }
            }
            
            return model_info
            
        except Exception as e:
            raise ProviderError(f"Failed to get model info: {e}") from e
    
    def _get_context_window(self, model: str) -> int:
        """Get the context window size for a specific model."""
        context_windows = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-4-turbo-preview": 128000,
            "gpt-4-0125-preview": 128000,
            "gpt-4-1106-preview": 128000,
            "gpt-3.5-turbo": 16385,
            "gpt-3.5-turbo-0125": 16385,
            "gpt-3.5-turbo-1106": 16385,
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000
        }
        return context_windows.get(model, 8192)  # Default to GPT-4 context window
    
    def _get_training_cutoff(self, model: str) -> str:
        """Get the training data cutoff for a specific model."""
        training_cutoffs = {
            "gpt-4": "April 2023",
            "gpt-4-turbo": "April 2024",
            "gpt-4-turbo-preview": "April 2024",
            "gpt-4-0125-preview": "April 2024",
            "gpt-4-1106-preview": "April 2024",
            "gpt-3.5-turbo": "September 2021",
            "gpt-3.5-turbo-0125": "September 2021",
            "gpt-3.5-turbo-1106": "September 2021",
            "gpt-4o": "October 2023",
            "gpt-4o-mini": "October 2023"
        }
        return training_cutoffs.get(model, "Unknown")
    
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
            "client_initialized": self._client is not None,
            "organization": self.organization
        }


# Register the provider with the factory
from .base import ProviderFactory
ProviderFactory.register_provider("openai", OpenAIProvider)