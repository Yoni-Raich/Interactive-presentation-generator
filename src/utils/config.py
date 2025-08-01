"""Configuration management for the presentation generator."""

import os
import yaml
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

from src.utils.exceptions import ConfigurationError


@dataclass
class Config:
    """Configuration class for the presentation generator."""
    
    # LLM Provider Configuration
    llm_provider: str = "gemini"  # gemini, ollama, openai, anthropic
    llm_model: str = "gemini-2.5-flash"
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None  # For Ollama and other local providers
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    llm_timeout: float = 30.0
    
    # Legacy support (deprecated but maintained for backward compatibility)
    google_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    
    # Generation Parameters
    max_sub_subjects: int = 3
    min_sub_subjects: int = 1
    slide_text_max_length: int = 500
    script_min_length: int = 200
    
    # Retry and Rate Limiting
    max_retries: int = 3
    rate_limit_delay: float = 1.0
    
    # Output Configuration
    output_directory: str = "./output"
    
    # Internal state
    config_file: Optional[str] = field(default=None, repr=False)

    @classmethod
    def from_yaml(cls, config_path: str) -> "Config":
        """Create configuration from a YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        except (yaml.YAMLError, IOError) as e:
            raise ConfigurationError(f"Error reading configuration file: {e}")

        if not isinstance(config_data, dict):
            raise ConfigurationError("Invalid YAML format: root should be a dictionary")

        # Extract nested configurations
        llm_config = config_data.get("llm", {})
        gen_config = config_data.get("generation", {})
        retry_config = config_data.get("retry", {})
        output_config = config_data.get("output", {})

        return cls(
            config_file=config_path,
            llm_provider=llm_config.get("provider", "gemini"),
            llm_model=llm_config.get("model", "gemini-2.5-flash"),
            llm_api_key=llm_config.get("api_key"),
            llm_base_url=llm_config.get("base_url"),
            llm_temperature=float(llm_config.get("temperature", 0.7)),
            llm_max_tokens=int(llm_config.get("max_tokens", 2048)),
            llm_timeout=float(llm_config.get("timeout", 30.0)),
            max_sub_subjects=int(gen_config.get("max_sub_subjects", 8)),
            min_sub_subjects=int(gen_config.get("min_sub_subjects", 3)),
            slide_text_max_length=int(gen_config.get("slide_text_max_length", 500)),
            script_min_length=int(gen_config.get("script_min_length", 200)),
            max_retries=int(retry_config.get("max_retries", 3)),
            rate_limit_delay=float(retry_config.get("rate_limit_delay", 1.0)),
            output_directory=output_config.get("directory", "./output")
        )

    def override_with_env(self):
        """Override configuration with environment variables."""
        load_dotenv()
        
        # LLM Provider Configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", self.llm_provider).lower()
        self.llm_model = os.getenv("LLM_MODEL", self.llm_model)
        self.llm_api_key = os.getenv("LLM_API_KEY", self.llm_api_key)
        self.llm_base_url = os.getenv("LLM_BASE_URL", self.llm_base_url)
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", self.llm_temperature))
        self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", self.llm_max_tokens))
        self.llm_timeout = float(os.getenv("LLM_TIMEOUT", self.llm_timeout))
        
        # Legacy support
        self.google_api_key = os.getenv("GOOGLE_API_KEY", self.google_api_key)
        self.gemini_model = os.getenv("GEMINI_MODEL", self.gemini_model)
        
        # Handle backward compatibility and provider-specific logic
        self._apply_provider_logic()

        # Other configuration
        self.max_sub_subjects = int(os.getenv("MAX_SUB_SUBJECTS", self.max_sub_subjects))
        self.min_sub_subjects = int(os.getenv("MIN_SUB_SUBJECTS", self.min_sub_subjects))
        self.slide_text_max_length = int(os.getenv("SLIDE_TEXT_MAX_LENGTH", self.slide_text_max_length))
        self.script_min_length = int(os.getenv("SCRIPT_MIN_LENGTH", self.script_min_length))
        self.max_retries = int(os.getenv("MAX_RETRIES", self.max_retries))
        self.rate_limit_delay = float(os.getenv("RATE_LIMIT_DELAY", self.rate_limit_delay))
        self.output_directory = os.getenv("OUTPUT_DIRECTORY", self.output_directory)

    def _apply_provider_logic(self):
        """Apply provider-specific logic and defaults."""
        if self.llm_provider == "gemini":
            if not self.llm_api_key and self.google_api_key:
                self.llm_api_key = self.google_api_key
            if not self.llm_model and self.gemini_model:
                self.llm_model = self.gemini_model
            if not self.llm_model:
                self.llm_model = "gemini-2.5-flash"
        elif self.llm_provider == "ollama":
            if not self.llm_model:
                self.llm_model = "gemma3"
            if not self.llm_base_url:
                self.llm_base_url = "http://localhost:11434"
        elif self.llm_provider == "openai":
            if not self.llm_model:
                self.llm_model = "gpt-4"
            if not self.llm_api_key:
                self.llm_api_key = os.getenv("OPENAI_API_KEY")
        elif self.llm_provider == "anthropic":
            if not self.llm_model:
                self.llm_model = "claude-3-sonnet-20240229"
            if not self.llm_api_key:
                self.llm_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Final validation check for API key
        if self.llm_provider in ["gemini", "openai", "anthropic"] and not self.llm_api_key:
            key_map = {
                "gemini": "LLM_API_KEY or GOOGLE_API_KEY",
                "openai": "LLM_API_KEY or OPENAI_API_KEY",
                "anthropic": "LLM_API_KEY or ANTHROPIC_API_KEY"
            }
            raise ConfigurationError(f"{key_map[self.llm_provider]} is required for {self.llm_provider}")
    
    def validate(self) -> None:
        """Validate configuration values."""
        # Validate LLM provider
        supported_providers = ["gemini", "ollama", "openai", "anthropic"]
        if self.llm_provider not in supported_providers:
            raise ConfigurationError(f"Unsupported LLM provider: {self.llm_provider}. Supported: {supported_providers}")
        
        # Validate API key for providers that require it
        if self.llm_provider in ["gemini", "openai", "anthropic"]:
            if not self.llm_api_key:
                raise ConfigurationError(f"API key is required for {self.llm_provider} provider")
            if not self.llm_api_key.strip():
                raise ConfigurationError(f"API key cannot be empty or whitespace only for {self.llm_provider} provider")
        
        # Validate model name
        if not self.llm_model or not self.llm_model.strip():
            raise ConfigurationError("LLM model name cannot be empty")
        
        # Validate LLM parameters
        if not 0 <= self.llm_temperature <= 2:
            raise ConfigurationError("llm_temperature must be between 0 and 2")
        
        if self.llm_max_tokens <= 0:
            raise ConfigurationError("llm_max_tokens must be positive")
        
        if self.llm_timeout <= 0:
            raise ConfigurationError("llm_timeout must be positive")
        
        # Validate generation parameters
        if self.max_sub_subjects < self.min_sub_subjects:
            raise ConfigurationError("max_sub_subjects must be greater than or equal to min_sub_subjects")
        
        if self.min_sub_subjects < 1:
            raise ConfigurationError("min_sub_subjects must be at least 1")
        
        if self.max_sub_subjects > 20:
            raise ConfigurationError("max_sub_subjects cannot exceed 20 (per requirement 2.2)")
        
        if self.slide_text_max_length <= 0:
            raise ConfigurationError("slide_text_max_length must be positive")
        
        if self.script_min_length <= 0:
            raise ConfigurationError("script_min_length must be positive")
        
        if self.max_retries < 0:
            raise ConfigurationError("max_retries must be non-negative")
        
        if self.max_retries > 10:
            raise ConfigurationError("max_retries should not exceed 10 to prevent excessive API calls")
        
        if self.rate_limit_delay < 0:
            raise ConfigurationError("rate_limit_delay must be non-negative")
        
        # Validate output directory can be created
        output_path = Path(self.output_directory)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise ConfigurationError(f"Cannot create output directory '{self.output_directory}': {e}")
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for provider initialization."""
        return {
            "provider": self.llm_provider,
            "model": self.llm_model,
            "api_key": self.llm_api_key,
            "base_url": self.llm_base_url,
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens,
            "timeout": self.llm_timeout,
            "max_retries": self.max_retries,
            "rate_limit_delay": self.rate_limit_delay
        }
    
    def get_api_config(self) -> dict:
        """Get API-specific configuration for LangChain integration (legacy method)."""
        # Maintain backward compatibility
        if self.llm_provider == "gemini":
            return {
                "google_api_key": self.llm_api_key or self.google_api_key,
                "model": self.llm_model or self.gemini_model,
                "max_retries": self.max_retries,
                "rate_limit_delay": self.rate_limit_delay
            }
        else:
            return self.get_llm_config()
    
    def get_generation_config(self) -> dict:
        """Get content generation configuration."""
        return {
            "max_sub_subjects": self.max_sub_subjects,
            "min_sub_subjects": self.min_sub_subjects,
            "slide_text_max_length": self.slide_text_max_length,
            "script_min_length": self.script_min_length
        }


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load and validate configuration from YAML file and environment variables.

    - If config_path is provided, it loads from that file.
    - If not, it looks for 'config.yaml' in the current directory.
    - If no file is found, it loads a default configuration.
    - Finally, it overrides with any existing environment variables.
    """
    if config_path:
        config = Config.from_yaml(config_path)
    elif os.path.exists("config.yaml"):
        config = Config.from_yaml("config.yaml")
    else:
        # Create a default config if no file is specified or found
        config = Config()

    # Override with environment variables
    config.override_with_env()

    # Validate the final configuration
    config.validate()

    return config