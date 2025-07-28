"""
LLM Provider abstraction layer.

This module provides a unified interface for different LLM providers,
allowing the system to work with various AI services like Gemini, Ollama, OpenAI, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage

from ..utils.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: float = 30.0
    
    # Provider-specific settings
    extra_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self) -> None:
        """Initialize the provider-specific client."""
        pass
    
    @abstractmethod
    def invoke(self, messages: List[Any]) -> str:
        """
        Invoke the LLM with messages and return response.
        
        Args:
            messages: List of messages (SystemMessage, HumanMessage, etc.)
            
        Returns:
            Response content as string
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to the LLM provider."""
        pass


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider implementation."""
    
    def _initialize_client(self) -> None:
        """Initialize the Gemini client."""
        if not self.config.api_key:
            raise ValueError("Google API key is required for Gemini provider")
        
        try:
            self._client = ChatGoogleGenerativeAI(
                model=self.config.model,
                google_api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
                **self.config.extra_params
            )
            logger.debug(f"Initialized Gemini client with model: {self.config.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def invoke(self, messages: List[Any]) -> str:
        """Invoke Gemini with messages."""
        try:
            response = self._client.invoke(messages)
            return response.content.strip() if response and response.content else ""
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test Gemini connection."""
        try:
            test_message = [HumanMessage(content="Hello, respond with 'Connection successful'")]
            response = self.invoke(test_message)
            return "successful" in response.lower()
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False


class OllamaProvider(BaseLLMProvider):
    """Ollama provider implementation."""
    
    def _initialize_client(self) -> None:
        """Initialize the Ollama client."""
        try:
            base_url = self.config.base_url or "http://localhost:11434"
            
            self._client = ChatOllama(
                model=self.config.model,
                base_url=base_url,
                temperature=self.config.temperature,
                timeout=self.config.timeout,
                **self.config.extra_params
            )
            logger.debug(f"Initialized Ollama client with model: {self.config.model} at {base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            raise
    
    def invoke(self, messages: List[Any]) -> str:
        """Invoke Ollama with messages."""
        try:
            # ChatOllama can handle messages directly
            response = self._client.invoke(messages)
            return response.content.strip() if response and response.content else ""
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test Ollama connection."""
        try:
            test_message = [HumanMessage(content="Hello, respond with 'Connection successful'")]
            response = self.invoke(test_message)
            return "successful" in response.lower()
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation."""
    
    def _initialize_client(self) -> None:
        """Initialize the OpenAI client."""
        if not self.config.api_key:
            raise ValueError("OpenAI API key is required for OpenAI provider")
        
        try:
            self._client = ChatOpenAI(
                model=self.config.model,
                openai_api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
                **self.config.extra_params
            )
            logger.debug(f"Initialized OpenAI client with model: {self.config.model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def invoke(self, messages: List[Any]) -> str:
        """Invoke OpenAI with messages."""
        try:
            response = self._client.invoke(messages)
            return response.content.strip() if response and response.content else ""
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test OpenAI connection."""
        try:
            test_message = [HumanMessage(content="Hello, respond with 'Connection successful'")]
            response = self.invoke(test_message)
            return "successful" in response.lower()
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation."""
    
    def _initialize_client(self) -> None:
        """Initialize the Anthropic client."""
        if not self.config.api_key:
            raise ValueError("Anthropic API key is required for Anthropic provider")
        
        try:
            self._client = ChatAnthropic(
                model=self.config.model,
                anthropic_api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
                **self.config.extra_params
            )
            logger.debug(f"Initialized Anthropic client with model: {self.config.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise
    
    def invoke(self, messages: List[Any]) -> str:
        """Invoke Anthropic with messages."""
        try:
            response = self._client.invoke(messages)
            return response.content.strip() if response and response.content else ""
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test Anthropic connection."""
        try:
            test_message = [HumanMessage(content="Hello, respond with 'Connection successful'")]
            response = self.invoke(test_message)
            return "successful" in response.lower()
        except Exception as e:
            logger.error(f"Anthropic connection test failed: {e}")
            return False


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers = {
        LLMProvider.GEMINI: GeminiProvider,
        LLMProvider.OLLAMA: OllamaProvider,
        LLMProvider.OPENAI: OpenAIProvider,
        LLMProvider.ANTHROPIC: AnthropicProvider,
    }
    
    @classmethod
    def create_provider(cls, config: LLMConfig) -> BaseLLMProvider:
        """
        Create an LLM provider based on configuration.
        
        Args:
            config: LLM configuration
            
        Returns:
            Initialized LLM provider
            
        Raises:
            ValueError: If provider is not supported
        """
        if config.provider not in cls._providers:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")
        
        provider_class = cls._providers[config.provider]
        return provider_class(config)
    
    @classmethod
    def get_supported_providers(cls) -> List[LLMProvider]:
        """Get list of supported providers."""
        return list(cls._providers.keys())
    
    @classmethod
    def get_provider_info(cls) -> Dict[LLMProvider, Dict[str, Any]]:
        """Get information about supported providers."""
        return {
            LLMProvider.GEMINI: {
                "name": "Google Gemini",
                "requires_api_key": True,
                "default_models": ["gemini-2.5-flash", "gemini-1.5-pro"],
                "description": "Google's Gemini AI models"
            },
            LLMProvider.OLLAMA: {
                "name": "Ollama",
                "requires_api_key": False,
                "default_models": ["llama3.2", "mistral", "codellama"],
                "description": "Local LLM runner with various open-source models",
                "default_base_url": "http://localhost:11434"
            },
            LLMProvider.OPENAI: {
                "name": "OpenAI",
                "requires_api_key": True,
                "default_models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                "description": "OpenAI's GPT models"
            },
            LLMProvider.ANTHROPIC: {
                "name": "Anthropic Claude",
                "requires_api_key": True,
                "default_models": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                "description": "Anthropic's Claude models"
            }
        }