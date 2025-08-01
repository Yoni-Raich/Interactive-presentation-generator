#!/usr/bin/env python3
"""
Example demonstrating the new configuration management system.
"""

from presentation_generator import Config, load_config

def main():
    """Demonstrate configuration usage."""
    print("Presentation Generator - Configuration Examples")
    print("=" * 50)
    
    # Example 1: Basic configuration
    print("\n1. Basic Configuration:")
    config = Config(
        llm_provider="gemini",
        api_key="your-api-key-here",
        model="gemini-2.5-flash",
        slide_count=6
    )
    print(f"   Provider: {config.llm_provider}")
    print(f"   Model: {config.model}")
    print(f"   Slide count: {config.slide_count}")
    
    # Example 2: Configuration from environment variables
    print("\n2. Configuration from Environment Variables:")
    print("   Set these environment variables:")
    print("   PRESENTATION_GENERATOR_PROVIDER=openai")
    print("   PRESENTATION_GENERATOR_API_KEY=your-openai-key")
    print("   PRESENTATION_GENERATOR_MODEL=gpt-4")
    
    # Example 3: Load configuration with multiple sources
    print("\n3. Load Configuration (multiple sources):")
    try:
        # This will load from defaults, then env vars, then any overrides
        config = load_config(override_dict={
            "temperature": 0.8,
            "slide_count": 8
        })
        print(f"   Final config: {config}")
        print(f"   Sources: {config._config_sources}")
    except Exception as e:
        print(f"   Note: {e}")
    
    # Example 4: Provider-specific configurations
    print("\n4. Provider-Specific Configurations:")
    
    # Gemini
    gemini_config = Config(
        llm_provider="gemini",
        api_key="your-gemini-key",
        model="gemini-2.5-flash",
        temperature=0.7
    )
    print(f"   Gemini: {gemini_config.get_provider_config()}")
    
    # OpenAI
    openai_config = Config(
        llm_provider="openai", 
        api_key="your-openai-key",
        model="gpt-4",
        organization="your-org-id"
    )
    print(f"   OpenAI: {openai_config.get_provider_config()}")
    
    # Ollama (local)
    ollama_config = Config(
        llm_provider="ollama",
        model="llama2",
        base_url="http://localhost:11434"
    )
    print(f"   Ollama: {ollama_config.get_provider_config()}")
    
    # Example 5: Media configuration
    print("\n5. Media Configuration:")
    media_config = config.get_media_config()
    print(f"   Image size: {media_config['image_width']}x{media_config['image_height']}")
    print(f"   Audio format: {media_config['audio_format']}")
    print(f"   Video FPS: {media_config['video_fps']}")
    
    # Example 6: Configuration validation
    print("\n6. Configuration Validation:")
    try:
        config.validate_for_generation()
        print("   ✓ Configuration is valid for generation")
    except Exception as e:
        print(f"   ✗ Configuration error: {e}")
    
    print("\n" + "=" * 50)
    print("Configuration examples completed!")

if __name__ == "__main__":
    main()