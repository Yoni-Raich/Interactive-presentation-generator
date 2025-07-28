"""Configuration management for the presentation generator."""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


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
    max_sub_subjects: int = 8
    min_sub_subjects: int = 3
    slide_text_max_length: int = 500
    script_min_length: int = 200
    
    # Retry and Rate Limiting
    max_retries: int = 3
    rate_limit_delay: float = 1.0
    
    # Output Configuration
    output_directory: str = "./output"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        # Load environment variables from .env file if it exists
        load_dotenv()
        
        # LLM Provider Configuration
        llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        llm_model = os.getenv("LLM_MODEL")
        llm_api_key = os.getenv("LLM_API_KEY")
        llm_base_url = os.getenv("LLM_BASE_URL")
        llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        llm_timeout = float(os.getenv("LLM_TIMEOUT", "30.0"))
        
        # Legacy support - check for old environment variables
        google_api_key = os.getenv("GOOGLE_API_KEY")
        gemini_model = os.getenv("GEMINI_MODEL")
        
        # Handle backward compatibility and provider-specific defaults
        if llm_provider == "gemini":
            # For Gemini, use legacy vars if new ones aren't set
            if not llm_api_key and google_api_key:
                llm_api_key = google_api_key
            if not llm_model and gemini_model:
                llm_model = gemini_model
            if not llm_model:
                llm_model = "gemini-2.5-flash"
        elif llm_provider == "ollama":
            # Ollama defaults
            if not llm_model:
                llm_model = "llama3.2"
            if not llm_base_url:
                llm_base_url = "http://localhost:11434"
        elif llm_provider == "openai":
            # OpenAI defaults
            if not llm_model:
                llm_model = "gpt-4"
            if not llm_api_key:
                llm_api_key = os.getenv("OPENAI_API_KEY")
        elif llm_provider == "anthropic":
            # Anthropic defaults
            if not llm_model:
                llm_model = "claude-3-sonnet-20240229"
            if not llm_api_key:
                llm_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Validate required API key for providers that need it
        if llm_provider in ["gemini", "openai", "anthropic"] and not llm_api_key:
            provider_key_map = {
                "gemini": "LLM_API_KEY or GOOGLE_API_KEY",
                "openai": "LLM_API_KEY or OPENAI_API_KEY", 
                "anthropic": "LLM_API_KEY or ANTHROPIC_API_KEY"
            }
            raise ValueError(f"{provider_key_map[llm_provider]} environment variable is required for {llm_provider} provider")
        
        # Other configuration
        max_sub_subjects = int(os.getenv("MAX_SUB_SUBJECTS", "8"))
        min_sub_subjects = int(os.getenv("MIN_SUB_SUBJECTS", "3"))
        slide_text_max_length = int(os.getenv("SLIDE_TEXT_MAX_LENGTH", "500"))
        script_min_length = int(os.getenv("SCRIPT_MIN_LENGTH", "200"))
        max_retries = int(os.getenv("MAX_RETRIES", "3"))
        rate_limit_delay = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))
        output_directory = os.getenv("OUTPUT_DIRECTORY", "./output")
        
        return cls(
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            llm_temperature=llm_temperature,
            llm_max_tokens=llm_max_tokens,
            llm_timeout=llm_timeout,
            google_api_key=google_api_key,  # Keep for backward compatibility
            gemini_model=gemini_model,      # Keep for backward compatibility
            max_sub_subjects=max_sub_subjects,
            min_sub_subjects=min_sub_subjects,
            slide_text_max_length=slide_text_max_length,
            script_min_length=script_min_length,
            max_retries=max_retries,
            rate_limit_delay=rate_limit_delay,
            output_directory=output_directory
        )
    
    def validate(self) -> None:
        """Validate configuration values."""
        # Validate LLM provider
        supported_providers = ["gemini", "ollama", "openai", "anthropic"]
        if self.llm_provider not in supported_providers:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}. Supported: {supported_providers}")
        
        # Validate API key for providers that require it
        if self.llm_provider in ["gemini", "openai", "anthropic"]:
            if not self.llm_api_key:
                raise ValueError(f"API key is required for {self.llm_provider} provider")
            if not self.llm_api_key.strip():
                raise ValueError(f"API key cannot be empty or whitespace only for {self.llm_provider} provider")
        
        # Validate model name
        if not self.llm_model or not self.llm_model.strip():
            raise ValueError("LLM model name cannot be empty")
        
        # Validate LLM parameters
        if not 0 <= self.llm_temperature <= 2:
            raise ValueError("llm_temperature must be between 0 and 2")
        
        if self.llm_max_tokens <= 0:
            raise ValueError("llm_max_tokens must be positive")
        
        if self.llm_timeout <= 0:
            raise ValueError("llm_timeout must be positive")
        
        # Validate generation parameters
        if self.max_sub_subjects < self.min_sub_subjects:
            raise ValueError("max_sub_subjects must be greater than or equal to min_sub_subjects")
        
        if self.min_sub_subjects < 1:
            raise ValueError("min_sub_subjects must be at least 1")
        
        if self.max_sub_subjects > 20:
            raise ValueError("max_sub_subjects cannot exceed 20 (per requirement 2.2)")
        
        if self.slide_text_max_length <= 0:
            raise ValueError("slide_text_max_length must be positive")
        
        if self.script_min_length <= 0:
            raise ValueError("script_min_length must be positive")
        
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        
        if self.max_retries > 10:
            raise ValueError("max_retries should not exceed 10 to prevent excessive API calls")
        
        if self.rate_limit_delay < 0:
            raise ValueError("rate_limit_delay must be non-negative")
        
        # Validate output directory can be created
        output_path = Path(self.output_directory)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise ValueError(f"Cannot create output directory '{self.output_directory}': {e}")
    
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


def load_config() -> Config:
    """Load and validate configuration from environment variables."""
    config = Config.from_env()
    config.validate()
    return config