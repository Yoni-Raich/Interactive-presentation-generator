"""
Anthropic Claude LLM provider implementation.

This module provides integration with Anthropic's Claude models through
the LangChain Anthropic integration.
"""

import time
from typing import Dict, Any, List, Optional

from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage

from .base import LLMProvider
from ..utils.exceptions import ProviderError, ConfigurationError


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude LLM provider implementation.
    
    This provider integrates with Anthropic's Claude models using the
    LangChain Anthropic integration. It supports various Claude models
    including Claude 3 Sonnet, Claude 3 Haiku, and Claude 3 Opus.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs):
        """
        Initialize the Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            model: Specific Claude model to use
            **kwargs: Additional configuration options:
                - temperature: Sampling temperature (0.0-1.0)
                - max_tokens: Maximum tokens in response
                - timeout: Request timeout in seconds
                - top_p: Nucleus sampling parameter
                - top_k: Top-k sampling parameter
        """
        super().__init__(api_key=api_key, model=model, **kwargs)
        self._client = None
        self._last_request_time = 0.0
        
        # Anthropic-specific configuration
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
        return "anthropic"
    
    @property
    def default_model(self) -> str:
        """Return the default model for this provider."""
        return "claude-3-sonnet-20240229"
    
    @property
    def supported_models(self) -> List[str]:
        """Return a list of supported models for this provider."""
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20240620",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]
    
    def _validate_config(self) -> None:
        """Validate Anthropic-specific configuration."""
        if not self.api_key:
            raise ConfigurationError(
                "Anthropic API key is required",
                field="api_key",
                details="Get your API key from https://console.anthropic.com/"
            )
        
        if not self.api_key.strip():
            raise ConfigurationError(
                "Anthropic API key cannot be empty",
                field="api_key"
            )
        
        # Basic API key format validation
        if not self.api_key.startswith('sk-ant-'):
            raise ConfigurationError(
                "Anthropic API key should start with 'sk-ant-'",
                field="api_key"
            )
        
        # Validate model
        effective_model = self.get_effective_model()
        if effective_model not in self.supported_models:
            raise ConfigurationError(
                f"Unsupported Anthropic model: {effective_model}",
                field="model",
                details=f"Supported models: {', '.join(self.supported_models)}"
            )
        
        # Validate parameters (Anthropic uses 0-1 range for temperature)
        if not 0 <= self.temperature <= 1:
            raise ConfigurationError(
                f"Temperature must be between 0.0 and 1.0 for Anthropic, got {self.temperature}",
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
        """Initialize the Anthropic client."""
        if self._client is not None:
            return
        
        try:
            # Build client configuration
            client_config = {
                "model": self.get_effective_model(),
                "anthropic_api_key": self.api_key,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "timeout": self.timeout
            }
            
            # Add optional parameters if specified
            if self.top_p is not None:
                client_config["top_p"] = self.top_p
            if self.top_k is not None:
                client_config["top_k"] = self.top_k
            
            self._client = ChatAnthropic(**client_config)
            
        except ImportError as e:
            raise ConfigurationError(
                "Anthropic package not installed",
                details="Install with: pip install langchain-anthropic"
            ) from e
        except Exception as e:
            raise ProviderError(f"Failed to initialize Anthropic client: {e}") from e
    
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
        Generate content using the Anthropic provider.
        
        Args:
            prompt: The input prompt for content generation
            **kwargs: Additional generation parameters:
                - system_prompt: Optional system prompt
                - temperature: Override default temperature
                - max_tokens: Override default max tokens
                - top_p: Override default top_p
                - top_k: Override default top_k
                
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
            for param in ['temperature', 'max_tokens', 'top_p', 'top_k']:
                if param in kwargs:
                    generation_kwargs[param] = kwargs[param]
            
            # Validate temperature override for Anthropic
            if 'temperature' in generation_kwargs:
                temp = generation_kwargs['temperature']
                if not 0 <= temp <= 1:
                    raise ProviderError(
                        f"Temperature must be between 0.0 and 1.0 for Anthropic, got {temp}"
                    )
            
            # Make the API call
            if generation_kwargs:
                # Create a temporary client with overridden parameters
                temp_config = {
                    "model": self.get_effective_model(),
                    "anthropic_api_key": self.api_key,
                    "temperature": generation_kwargs.get('temperature', self.temperature),
                    "max_tokens": generation_kwargs.get('max_tokens', self.max_tokens),
                    "timeout": self.timeout
                }
                if 'top_p' in generation_kwargs:
                    temp_config['top_p'] = generation_kwargs['top_p']
                if 'top_k' in generation_kwargs:
                    temp_config['top_k'] = generation_kwargs['top_k']
                
                temp_client = ChatAnthropic(**temp_config)
                response = temp_client.invoke(messages)
            else:
                response = self._client.invoke(messages)
            
            if not response or not response.content:
                raise ProviderError("Empty response from Anthropic API")
            
            content = response.content.strip()
            if not content:
                raise ProviderError("Empty content in Anthropic response")
            
            return content
            
        except Exception as e:
            error_str = str(e).lower()
            if "api key" in error_str or "unauthorized" in error_str:
                raise ConfigurationError(
                    "Invalid or expired Anthropic API key",
                    field="api_key",
                    details=str(e)
                ) from e
            elif "rate limit" in error_str or "too many requests" in error_str:
                raise ProviderError(
                    f"Anthropic API rate limit exceeded: {e}"
                ) from e
            elif "timeout" in error_str:
                raise ProviderError(
                    f"Anthropic API request timeout: {e}"
                ) from e
            elif "model" in error_str and ("not found" in error_str or "not supported" in error_str):
                raise ConfigurationError(
                    f"Anthropic model not found or not accessible: {self.get_effective_model()}",
                    field="model",
                    details=str(e)
                ) from e
            elif "credit" in error_str or "billing" in error_str:
                raise ProviderError(
                    f"Anthropic API billing or credit issue: {e}"
                ) from e
            else:
                raise ProviderError(f"Anthropic API error: {e}") from e
    
    def test_connection(self) -> bool:
        """
        Test the connection to the Anthropic provider.
        
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
                "supports_vision": model in ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-5-sonnet-20240620"],
                "supports_function_calling": model.startswith("claude-3"),
                "model_family": self._get_model_family(model),
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
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            "claude-3-5-sonnet-20240620": 200000,
            "claude-2.1": 200000,
            "claude-2.0": 100000,
            "claude-instant-1.2": 100000
        }
        return context_windows.get(model, 100000)  # Default to 100K
    
    def _get_model_family(self, model: str) -> str:
        """Get the model family for a specific model."""
        if model.startswith("claude-3-opus"):
            return "Claude 3 Opus"
        elif model.startswith("claude-3-5-sonnet"):
            return "Claude 3.5 Sonnet"
        elif model.startswith("claude-3-sonnet"):
            return "Claude 3 Sonnet"
        elif model.startswith("claude-3-haiku"):
            return "Claude 3 Haiku"
        elif model.startswith("claude-2.1"):
            return "Claude 2.1"
        elif model.startswith("claude-2.0"):
            return "Claude 2.0"
        elif model.startswith("claude-instant"):
            return "Claude Instant"
        else:
            return "Claude"
    
    def get_usage_info(self) -> Dict[str, Any]:
        """
        Get usage information and statistics.
        
        Returns:
            Dictionary containing usage statistics
        """
        return {
            "provider": self.provider_name,
            "model": self.get_effective_model(),
            "model_family": self._get_model_family(self.get_effective_model()),
            "last_request_time": self._last_request_time,
            "rate_limit_delay": self.rate_limit_delay,
            "client_initialized": self._client is not None
        }


# Register the provider with the factory
from .base import ProviderFactory
ProviderFactory.register_provider("anthropic", AnthropicProvider)