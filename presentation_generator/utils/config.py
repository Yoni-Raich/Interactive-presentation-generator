"""
Configuration management for the presentation generator library.

This module provides comprehensive configuration management with support for
multiple configuration sources (direct config, environment variables, defaults),
validation, and provider credential checking.
"""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from .exceptions import ConfigurationError, ValidationError


@dataclass
class Config:
    """
    Configuration class for the presentation generator library.
    
    This class supports multiple configuration sources with the following priority:
    1. Direct Config object passed to constructor
    2. Environment variables
    3. Configuration file (YAML/JSON)
    4. Default values
    
    Attributes:
        llm_provider: The LLM provider to use (gemini, openai, anthropic, ollama)
        api_key: API key for the LLM provider
        model: Specific model to use (provider-dependent)
        output_dir: Directory for generated files
        include_audio: Whether to generate audio files
        include_video: Whether to generate the final video
        slide_count: Target number of slides (None for auto-determination)
        temp_cleanup: Whether to clean up temporary files after generation
        
        # Advanced LLM settings
        temperature: LLM temperature for content generation (0.0-2.0)
        max_tokens: Maximum tokens for LLM responses
        timeout: Timeout for LLM API calls in seconds
        max_retries: Maximum number of retry attempts for failed API calls
        
        # Media processing settings
        image_width: Width of generated slide images
        image_height: Height of generated slide images
        audio_format: Audio format for TTS generation (wav, mp3)
        video_fps: Frames per second for video generation
        
        # Provider-specific settings
        base_url: Base URL for local providers (e.g., Ollama)
        organization: Organization ID for providers that support it
        
        # Internal configuration tracking
        _config_sources: List of configuration sources used
    """
    
    # Core settings
    llm_provider: str = "gemini"
    api_key: Optional[str] = None
    model: Optional[str] = None
    output_dir: str = "./output"
    include_audio: bool = True
    include_video: bool = True
    slide_count: Optional[int] = None
    temp_cleanup: bool = True
    
    # Advanced LLM settings
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: float = 30.0
    max_retries: int = 3
    
    # Media processing settings
    image_width: int = 1920
    image_height: int = 1080
    audio_format: str = "wav"
    video_fps: int = 30
    
    # Provider-specific settings
    base_url: Optional[str] = None
    organization: Optional[str] = None
    
    # Internal tracking
    _config_sources: List[str] = field(default_factory=list, init=False, repr=False)
    _explicit_fields: set = field(default_factory=set, init=False, repr=False)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_basic_constraints()
    
    def _validate_basic_constraints(self):
        """Validate basic configuration constraints."""
        valid_providers = ["gemini", "openai", "anthropic", "ollama"]
        if self.llm_provider not in valid_providers:
            raise ValidationError(
                f"Invalid LLM provider: {self.llm_provider}",
                field="llm_provider",
                value=self.llm_provider,
                details=f"Must be one of: {valid_providers}"
            )
        
        if self.slide_count is not None:
            if self.slide_count < 1 or self.slide_count > 20:
                raise ValidationError(
                    "Slide count must be between 1 and 20",
                    field="slide_count",
                    value=str(self.slide_count)
                )
        
        if not self.output_dir.strip():
            raise ValidationError(
                "Output directory cannot be empty",
                field="output_dir",
                value=self.output_dir
            )
        
        if not 0 <= self.temperature <= 2:
            raise ValidationError(
                "Temperature must be between 0.0 and 2.0",
                field="temperature",
                value=str(self.temperature)
            )
        
        if self.max_tokens <= 0:
            raise ValidationError(
                "Max tokens must be positive",
                field="max_tokens",
                value=str(self.max_tokens)
            )
        
        if self.timeout <= 0:
            raise ValidationError(
                "Timeout must be positive",
                field="timeout",
                value=str(self.timeout)
            )
        
        if self.max_retries < 0:
            raise ValidationError(
                "Max retries must be non-negative",
                field="max_retries",
                value=str(self.max_retries)
            )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """
        Create configuration from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values
            
        Returns:
            Config instance
            
        Raises:
            ConfigurationError: If the dictionary contains invalid values
        """
        try:
            # Filter out keys that aren't valid Config fields
            valid_fields = {f.name for f in cls.__dataclass_fields__.values() if f.init}
            filtered_dict = {k: v for k, v in config_dict.items() if k in valid_fields}
            
            config = cls(**filtered_dict)
            config._config_sources.append("dictionary")
            return config
            
        except (TypeError, ValueError) as e:
            raise ConfigurationError(f"Invalid configuration dictionary: {e}")
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "Config":
        """
        Create configuration from a YAML file.
        
        Args:
            config_path: Path to the YAML configuration file
            
        Returns:
            Config instance
            
        Raises:
            ConfigurationError: If the file cannot be read or parsed
        """
        try:
            config_path = Path(config_path)
            if not config_path.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not isinstance(config_data, dict):
                raise ConfigurationError("Invalid YAML format: root should be a dictionary")
            
            config = cls.from_dict(config_data)
            config._config_sources.append(f"yaml:{config_path}")
            return config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML file: {e}")
        except IOError as e:
            raise ConfigurationError(f"Error reading configuration file: {e}")
    
    @classmethod
    def from_env(cls, prefix: str = "PRESENTATION_GENERATOR") -> "Config":
        """
        Create configuration from environment variables.
        
        Args:
            prefix: Prefix for environment variables (default: PRESENTATION_GENERATOR)
            
        Returns:
            Config instance with values from environment variables
        """
        load_dotenv()
        
        config_dict = {}
        
        # Map environment variables to config fields
        env_mappings = {
            f"{prefix}_PROVIDER": "llm_provider",
            f"{prefix}_API_KEY": "api_key",
            f"{prefix}_MODEL": "model",
            f"{prefix}_OUTPUT_DIR": "output_dir",
            f"{prefix}_INCLUDE_AUDIO": "include_audio",
            f"{prefix}_INCLUDE_VIDEO": "include_video",
            f"{prefix}_SLIDE_COUNT": "slide_count",
            f"{prefix}_TEMP_CLEANUP": "temp_cleanup",
            f"{prefix}_TEMPERATURE": "temperature",
            f"{prefix}_MAX_TOKENS": "max_tokens",
            f"{prefix}_TIMEOUT": "timeout",
            f"{prefix}_MAX_RETRIES": "max_retries",
            f"{prefix}_IMAGE_WIDTH": "image_width",
            f"{prefix}_IMAGE_HEIGHT": "image_height",
            f"{prefix}_AUDIO_FORMAT": "audio_format",
            f"{prefix}_VIDEO_FPS": "video_fps",
            f"{prefix}_BASE_URL": "base_url",
            f"{prefix}_ORGANIZATION": "organization",
        }
        
        for env_var, config_field in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion based on field type
                if config_field in ["include_audio", "include_video", "temp_cleanup"]:
                    config_dict[config_field] = value.lower() in ("true", "1", "yes", "on")
                elif config_field in ["slide_count", "max_tokens", "max_retries", "image_width", "image_height", "video_fps"]:
                    try:
                        config_dict[config_field] = int(value)
                    except ValueError:
                        raise ConfigurationError(f"Invalid integer value for {env_var}: {value}")
                elif config_field in ["temperature", "timeout"]:
                    try:
                        config_dict[config_field] = float(value)
                    except ValueError:
                        raise ConfigurationError(f"Invalid float value for {env_var}: {value}")
                else:
                    config_dict[config_field] = value
        
        config = cls.from_dict(config_dict) if config_dict else cls()
        config._config_sources.append("environment")
        return config
    
    def merge_with(self, other: "Config") -> "Config":
        """
        Merge this configuration with another, with the other taking precedence.
        
        Args:
            other: Another Config instance to merge with
            
        Returns:
            New Config instance with merged values
        """
        # Convert both configs to dictionaries
        self_dict = self.to_dict()
        other_dict = other.to_dict()
        
        # Merge dictionaries (other takes precedence)
        merged_dict = {**self_dict, **other_dict}
        
        # Create new config from merged dictionary
        merged_config = self.from_dict(merged_dict)
        merged_config._config_sources = self._config_sources + other._config_sources
        
        return merged_config
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        result = {}
        for field_name, field_def in self.__dataclass_fields__.items():
            if field_def.init:  # Only include fields that are part of initialization
                value = getattr(self, field_name)
                if value is not None:
                    result[field_name] = value
        return result
    
    def validate_for_generation(self) -> None:
        """
        Validate that the configuration is ready for presentation generation.
        
        Raises:
            ConfigurationError: If the configuration is invalid for generation
        """
        errors = []
        
        # Check API key requirements
        if self.requires_api_key() and not self.api_key:
            errors.append(f"API key is required for {self.llm_provider} provider")
        
        # Validate output directory
        try:
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            errors.append(f"Cannot create output directory '{self.output_dir}': {e}")
        
        # Validate provider-specific settings
        provider_errors = self._validate_provider_settings()
        errors.extend(provider_errors)
        
        # Validate media settings
        media_errors = self._validate_media_settings()
        errors.extend(media_errors)
        
        if errors:
            raise ConfigurationError(
                "Configuration validation failed",
                details="; ".join(errors)
            )
    
    def _validate_provider_settings(self) -> List[str]:
        """Validate provider-specific settings."""
        errors = []
        
        if self.llm_provider == "ollama":
            if not self.base_url:
                self.base_url = "http://localhost:11434"  # Set default
            if not self.model:
                self.model = "llama2"  # Set default model
        elif self.llm_provider == "gemini":
            if not self.model:
                self.model = "gemini-2.5-flash"
        elif self.llm_provider == "openai":
            if not self.model:
                self.model = "gpt-4"
        elif self.llm_provider == "anthropic":
            if not self.model:
                self.model = "claude-3-sonnet-20240229"
        
        return errors
    
    def _validate_media_settings(self) -> List[str]:
        """Validate media processing settings."""
        errors = []
        
        if self.image_width <= 0 or self.image_height <= 0:
            errors.append("Image dimensions must be positive")
        
        if self.audio_format not in ["wav", "mp3"]:
            errors.append("Audio format must be 'wav' or 'mp3'")
        
        if self.video_fps <= 0:
            errors.append("Video FPS must be positive")
        
        return errors
    
    def requires_api_key(self) -> bool:
        """
        Check if the current provider requires an API key.
        
        Returns:
            True if API key is required, False otherwise
        """
        return self.llm_provider != "ollama"
    
    def test_provider_connection(self) -> bool:
        """
        Test connection to the configured LLM provider.
        
        Returns:
            True if connection is successful, False otherwise
            
        Note:
            This is a basic validation. Actual connection testing
            should be implemented in the provider classes.
        """
        if self.requires_api_key():
            return bool(self.api_key and self.api_key.strip())
        
        # For Ollama, we could test the base_url connectivity
        # but for now, just return True if base_url is set
        return bool(self.base_url)
    
    def get_provider_config(self) -> Dict[str, Any]:
        """
        Get provider-specific configuration dictionary.
        
        Returns:
            Dictionary containing provider-specific settings
        """
        config = {
            "provider": self.llm_provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }
        
        if self.api_key:
            config["api_key"] = self.api_key
        
        if self.base_url:
            config["base_url"] = self.base_url
        
        if self.organization:
            config["organization"] = self.organization
        
        return config
    
    def get_media_config(self) -> Dict[str, Any]:
        """
        Get media processing configuration dictionary.
        
        Returns:
            Dictionary containing media processing settings
        """
        return {
            "image_width": self.image_width,
            "image_height": self.image_height,
            "audio_format": self.audio_format,
            "video_fps": self.video_fps,
            "include_audio": self.include_audio,
            "include_video": self.include_video,
        }
    
    def save_to_yaml(self, config_path: str) -> None:
        """
        Save configuration to a YAML file.
        
        Args:
            config_path: Path where to save the configuration
            
        Raises:
            ConfigurationError: If the file cannot be written
        """
        try:
            config_path = Path(config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
                
        except IOError as e:
            raise ConfigurationError(f"Error writing configuration file: {e}")
    
    def __str__(self) -> str:
        """String representation of the configuration."""
        return f"Config(provider={self.llm_provider}, model={self.model}, output_dir={self.output_dir})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the configuration."""
        sources = ", ".join(self._config_sources) if self._config_sources else "defaults"
        return f"Config(provider={self.llm_provider}, sources=[{sources}])"


def load_config(
    config_path: Optional[str] = None,
    env_prefix: str = "PRESENTATION_GENERATOR",
    override_dict: Optional[Dict[str, Any]] = None
) -> Config:
    """
    Load configuration from multiple sources with proper precedence.
    
    Configuration sources in order of precedence (highest to lowest):
    1. override_dict parameter (always applied)
    2. Explicit configuration file (if config_path provided)
    3. Environment variables (only if no explicit config file)
    4. Default config.yaml (only if exists and no explicit config)
    5. Default values
    
    This ensures that when a user provides an explicit config file,
    environment variables won't override their settings.
    
    Args:
        config_path: Optional path to YAML configuration file
        env_prefix: Prefix for environment variables
        override_dict: Optional dictionary to override specific values
        
    Returns:
        Fully configured Config instance
        
    Raises:
        ConfigurationError: If configuration loading or validation fails
    """
    # Start with default configuration
    config = Config()
    config._config_sources.append("defaults")
    
    # Track if user explicitly provided a config file
    user_provided_config = False
    
    # Load from explicitly specified config file (highest priority)
    if config_path:
        if Path(config_path).exists():
            file_config = Config.from_yaml(config_path)
            config = config.merge_with(file_config)
            user_provided_config = True
        else:
            raise ConfigurationError(f"Specified configuration file not found: {config_path}")
    
    # If no explicit config provided, check environment variables first
    if not user_provided_config:
        env_config = Config.from_env(env_prefix)
        if env_config._config_sources:  # Only merge if env vars were found
            config = config.merge_with(env_config)
    
    # Then check for default config.yaml (lowest priority among file sources)
    if not user_provided_config and Path("config.yaml").exists():
        file_config = Config.from_yaml("config.yaml")
        config = config.merge_with(file_config)
    
    # Apply direct overrides (always highest priority)
    if override_dict:
        override_config = Config.from_dict(override_dict)
        override_config._config_sources.append("overrides")
        config = config.merge_with(override_config)
    
    # Final validation
    config.validate_for_generation()
    
    return config


def create_default_config() -> Config:
    """
    Create a default configuration instance.
    
    Returns:
        Config instance with default values
    """
    config = Config()
    config._config_sources.append("defaults")
    return config


def validate_provider_credentials(config: Config) -> Dict[str, Any]:
    """
    Validate provider credentials and return status information.
    
    Args:
        config: Configuration to validate
        
    Returns:
        Dictionary containing validation results:
        - valid: bool indicating if credentials are valid
        - provider: str provider name
        - errors: list of error messages
        - warnings: list of warning messages
    """
    result = {
        "valid": False,
        "provider": config.llm_provider,
        "errors": [],
        "warnings": []
    }
    
    try:
        # Basic configuration validation
        config.validate_for_generation()
        
        # Provider-specific credential checking
        if config.llm_provider == "ollama":
            if not config.base_url:
                result["errors"].append("Base URL is required for Ollama provider")
            else:
                result["valid"] = True
                result["warnings"].append("Ollama connection not tested - ensure service is running")
        
        elif config.requires_api_key():
            if not config.api_key:
                result["errors"].append(f"API key is required for {config.llm_provider} provider")
            elif not config.api_key.strip():
                result["errors"].append("API key cannot be empty or whitespace only")
            else:
                # Basic API key format validation
                if len(config.api_key) < 10:
                    result["warnings"].append("API key seems unusually short")
                result["valid"] = True
        
        else:
            result["valid"] = True
        
    except (ConfigurationError, ValidationError) as e:
        result["errors"].append(str(e))
    
    return result