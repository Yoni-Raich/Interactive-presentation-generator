"""
Ollama LLM provider implementation.

This module provides integration with Ollama for running local LLM models
through the LangChain Ollama integration.
"""

import time
import requests
from typing import Dict, Any, List, Optional

from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage

from .base import LLMProvider
from ..utils.exceptions import ProviderError, ConfigurationError


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider implementation.
    
    This provider integrates with Ollama for running local LLM models.
    It supports various open-source models like Llama, Mistral, CodeLlama, etc.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs):
        """
        Initialize the Ollama provider.
        
        Args:
            api_key: Not used for Ollama (local provider)
            model: Specific Ollama model to use
            **kwargs: Additional configuration options:
                - base_url: Ollama server URL (default: http://localhost:11434)
                - temperature: Sampling temperature (0.0-2.0)
                - timeout: Request timeout in seconds
                - top_p: Nucleus sampling parameter
                - top_k: Top-k sampling parameter
                - num_predict: Maximum number of tokens to predict
        """
        super().__init__(api_key=api_key, model=model, **kwargs)
        self._client = None
        self._last_request_time = 0.0
        
        # Ollama-specific configuration
        self.base_url = kwargs.get('base_url', 'http://localhost:11434')
        self.temperature = kwargs.get('temperature', 0.7)
        self.timeout = kwargs.get('timeout', 60.0)  # Longer timeout for local models
        self.top_p = kwargs.get('top_p', None)
        self.top_k = kwargs.get('top_k', None)
        self.num_predict = kwargs.get('num_predict', 2048)
        
        # Rate limiting (less strict for local)
        self.rate_limit_delay = kwargs.get('rate_limit_delay', 0.1)
    
    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "ollama"
    
    @property
    def default_model(self) -> str:
        """Return the default model for this provider."""
        return "llama3.2"
    
    @property
    def supported_models(self) -> List[str]:
        """Return a list of commonly supported models for this provider."""
        return [
            "llama3.2",
            "llama3.1",
            "llama3",
            "llama2",
            "mistral",
            "mixtral",
            "codellama",
            "phi3",
            "gemma",
            "qwen",
            "deepseek-coder",
            "neural-chat",
            "starling-lm",
            "vicuna",
            "orca-mini"
        ]
    
    def _validate_config(self) -> None:
        """Validate Ollama-specific configuration."""
        # API key is not required for Ollama
        if not self.base_url:
            raise ConfigurationError(
                "Base URL is required for Ollama provider",
                field="base_url",
                details="Default: http://localhost:11434"
            )
        
        if not self.base_url.strip():
            raise ConfigurationError(
                "Base URL cannot be empty",
                field="base_url"
            )
        
        # Validate URL format
        if not (self.base_url.startswith('http://') or self.base_url.startswith('https://')):
            raise ConfigurationError(
                "Base URL must start with http:// or https://",
                field="base_url",
                value=self.base_url
            )
        
        # Validate parameters
        if not 0 <= self.temperature <= 2:
            raise ConfigurationError(
                f"Temperature must be between 0.0 and 2.0, got {self.temperature}",
                field="temperature"
            )
        
        if self.timeout <= 0:
            raise ConfigurationError(
                f"Timeout must be positive, got {self.timeout}",
                field="timeout"
            )
        
        if self.num_predict <= 0:
            raise ConfigurationError(
                f"Num predict must be positive, got {self.num_predict}",
                field="num_predict"
            )
    
    def _initialize_client(self) -> None:
        """Initialize the Ollama client."""
        if self._client is not None:
            return
        
        try:
            # Build client configuration
            client_config = {
                "model": self.get_effective_model(),
                "base_url": self.base_url,
                "temperature": self.temperature,
                "timeout": self.timeout,
                "num_predict": self.num_predict
            }
            
            # Add optional parameters if specified
            if self.top_p is not None:
                client_config["top_p"] = self.top_p
            if self.top_k is not None:
                client_config["top_k"] = self.top_k
            
            self._client = ChatOllama(**client_config)
            
        except ImportError as e:
            raise ConfigurationError(
                "Ollama package not installed",
                details="Install with: pip install langchain-ollama"
            ) from e
        except Exception as e:
            raise ProviderError(f"Failed to initialize Ollama client: {e}") from e
    
    def _respect_rate_limit(self) -> None:
        """Implement rate limiting (minimal for local provider)."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _check_ollama_server(self) -> bool:
        """Check if Ollama server is running and accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def _check_model_availability(self, model: str) -> bool:
        """Check if a specific model is available on the Ollama server."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [m['name'].split(':')[0] for m in models_data.get('models', [])]
                return model in available_models
            return False
        except requests.RequestException:
            return False
    
    def generate_content(self, prompt: str, **kwargs) -> str:
        """
        Generate content using the Ollama provider.
        
        Args:
            prompt: The input prompt for content generation
            **kwargs: Additional generation parameters:
                - system_prompt: Optional system prompt
                - temperature: Override default temperature
                - num_predict: Override default num_predict
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
        
        # Check if Ollama server is running
        if not self._check_ollama_server():
            raise ProviderError(
                f"Ollama server is not accessible at {self.base_url}. "
                "Please ensure Ollama is running."
            )
        
        # Check if model is available
        model = self.get_effective_model()
        if not self._check_model_availability(model):
            raise ProviderError(
                f"Model '{model}' is not available on Ollama server. "
                f"Please pull the model first: ollama pull {model}"
            )
        
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
            for param in ['temperature', 'num_predict', 'top_p', 'top_k']:
                if param in kwargs:
                    generation_kwargs[param] = kwargs[param]
            
            # Make the API call
            if generation_kwargs:
                # Create a temporary client with overridden parameters
                temp_config = {
                    "model": model,
                    "base_url": self.base_url,
                    "temperature": generation_kwargs.get('temperature', self.temperature),
                    "timeout": self.timeout,
                    "num_predict": generation_kwargs.get('num_predict', self.num_predict)
                }
                if 'top_p' in generation_kwargs:
                    temp_config['top_p'] = generation_kwargs['top_p']
                if 'top_k' in generation_kwargs:
                    temp_config['top_k'] = generation_kwargs['top_k']
                
                temp_client = ChatOllama(**temp_config)
                response = temp_client.invoke(messages)
            else:
                response = self._client.invoke(messages)
            
            if not response or not response.content:
                raise ProviderError("Empty response from Ollama")
            
            content = response.content.strip()
            if not content:
                raise ProviderError("Empty content in Ollama response")
            
            return content
            
        except Exception as e:
            error_str = str(e).lower()
            if "connection" in error_str or "refused" in error_str:
                raise ProviderError(
                    f"Cannot connect to Ollama server at {self.base_url}. "
                    "Please ensure Ollama is running."
                ) from e
            elif "timeout" in error_str:
                raise ProviderError(
                    f"Ollama request timeout. Model may be loading or server is overloaded: {e}"
                ) from e
            elif "model" in error_str and ("not found" in error_str or "not available" in error_str):
                raise ProviderError(
                    f"Model '{model}' not found. Please pull the model: ollama pull {model}"
                ) from e
            else:
                raise ProviderError(f"Ollama error: {e}") from e
    
    def test_connection(self) -> bool:
        """
        Test the connection to the Ollama provider.
        
        Returns:
            True if connection is successful, False otherwise
            
        Raises:
            ProviderError: If connection test fails with an error
        """
        try:
            self.validate_configuration()
            
            # Check server availability
            if not self._check_ollama_server():
                return False
            
            # Check model availability
            model = self.get_effective_model()
            if not self._check_model_availability(model):
                return False
            
            # Try a simple generation
            self._initialize_client()
            test_response = self.generate_content(
                "Respond with exactly: 'Connection successful'",
                temperature=0.0,
                num_predict=10
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
            
            # Try to get model info from Ollama server
            model_details = {}
            try:
                response = requests.get(f"{self.base_url}/api/show", 
                                      json={"name": model}, timeout=5)
                if response.status_code == 200:
                    model_details = response.json()
            except requests.RequestException:
                pass
            
            # Model-specific information
            model_info = {
                "name": model,
                "provider": self.provider_name,
                "type": "chat",
                "base_url": self.base_url,
                "server_accessible": self._check_ollama_server(),
                "model_available": self._check_model_availability(model),
                "model_family": self._get_model_family(model),
                "configuration": {
                    "temperature": self.temperature,
                    "num_predict": self.num_predict,
                    "timeout": self.timeout,
                    "top_p": self.top_p,
                    "top_k": self.top_k
                }
            }
            
            # Add server-provided details if available
            if model_details:
                model_info.update({
                    "size": model_details.get("size"),
                    "digest": model_details.get("digest"),
                    "modified_at": model_details.get("modified_at"),
                    "template": model_details.get("template")
                })
            
            return model_info
            
        except Exception as e:
            raise ProviderError(f"Failed to get model info: {e}") from e
    
    def _get_model_family(self, model: str) -> str:
        """Get the model family for a specific model."""
        model_lower = model.lower()
        if "llama" in model_lower:
            return "Llama"
        elif "mistral" in model_lower:
            return "Mistral"
        elif "mixtral" in model_lower:
            return "Mixtral"
        elif "codellama" in model_lower:
            return "Code Llama"
        elif "phi" in model_lower:
            return "Phi"
        elif "gemma" in model_lower:
            return "Gemma"
        elif "qwen" in model_lower:
            return "Qwen"
        elif "deepseek" in model_lower:
            return "DeepSeek"
        elif "neural-chat" in model_lower:
            return "Neural Chat"
        elif "starling" in model_lower:
            return "Starling"
        elif "vicuna" in model_lower:
            return "Vicuna"
        elif "orca" in model_lower:
            return "Orca"
        else:
            return "Unknown"
    
    def get_available_models(self) -> List[str]:
        """
        Get list of models available on the Ollama server.
        
        Returns:
            List of available model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                return [m['name'] for m in models_data.get('models', [])]
            return []
        except requests.RequestException:
            return []
    
    def pull_model(self, model: str) -> bool:
        """
        Pull a model to the Ollama server.
        
        Args:
            model: Model name to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model},
                timeout=300  # 5 minutes for model download
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
    
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
            "base_url": self.base_url,
            "server_accessible": self._check_ollama_server(),
            "available_models": self.get_available_models(),
            "last_request_time": self._last_request_time,
            "rate_limit_delay": self.rate_limit_delay,
            "client_initialized": self._client is not None
        }


# Register the provider with the factory
from .base import ProviderFactory
ProviderFactory.register_provider("ollama", OllamaProvider)