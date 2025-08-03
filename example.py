#!/usr/bin/env python3
"""
Minimal usage example for the Presentation Generator library.

This example demonstrates the core functionality of generating complete
video presentations from topics using different LLM providers.
"""

import os
from presentation_generator import (
    PresentationGenerator, 
    Config, 
    create_generator,
    quick_generate,
    get_supported_providers
)

def basic_usage():
    """Demonstrate basic library usage."""
    print("🎯 Basic Usage Example")
    print("-" * 40)
    
    # Simple usage - uses default configuration (Gemini)
    generator = PresentationGenerator()
    
    try:
        # Generate a complete presentation
        result = generator.generate("Introduction to Python Programming")
        presentation = result.presentation
        
        print(f"✅ Generated presentation: {presentation.topic}")
        print(f"📹 Video created: {presentation.video_path}")
        print(f"📊 Number of slides: {len(presentation.slides)}")
        
        # Show slide details
        for i, slide in enumerate(presentation.slides, 1):
            print(f"   Slide {i}: {slide.title}")
            print(f"     Image: {slide.image_path}")
            print(f"     Audio: {slide.audio_path}")
            print(f"     Duration: {slide.duration:.1f}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you have configured your LLM provider credentials")

def advanced_configuration():
    """Demonstrate advanced configuration options."""
    print("\n🔧 Advanced Configuration Example")
    print("-" * 40)
    
    # Create configuration with specific settings
    config = Config(
        llm_provider="gemini",  # or "openai", "anthropic", "ollama"
        api_key=os.getenv("LLM_API_KEY"),  # Set this environment variable
        model="gemini-2.5-flash",
        output_dir="./my_presentations",
        slide_count=5,
        temperature=0.7
    )
    
    generator = PresentationGenerator(config)
    
    try:
        result = generator.generate("Machine Learning Fundamentals")
        presentation = result.presentation
        
        print(f"✅ Generated with custom config: {presentation.topic}")
        print(f"📁 Output directory: {config.output_dir}")
        print(f"🎬 Final video: {presentation.video_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def convenience_functions():
    """Demonstrate convenience functions for quick usage."""
    print("\n⚡ Convenience Functions Example")
    print("-" * 40)
    
    # Show supported providers
    providers = get_supported_providers()
    print(f"📋 Supported providers: {', '.join(providers)}")
    
    # Quick generator creation
    try:
        generator = create_generator(
            provider="gemini",
            api_key=os.getenv("LLM_API_KEY"),
            slide_count=4
        )
        
        print("✅ Created generator with convenience function")
        
        # Quick generation (one-liner)
        # Uncomment to test:
        # result = quick_generate(
        #     "Data Science Basics",
        #     provider="gemini",
        #     api_key=os.getenv("LLM_API_KEY")
        # )
        # print(f"⚡ Quick generation result: {result.presentation.video_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def provider_examples():
    """Show configuration for different providers."""
    print("\n🌐 Multi-Provider Examples")
    print("-" * 40)
    
    # Gemini (Google)
    print("🔹 Gemini Configuration:")
    print("   export LLM_PROVIDER=gemini")
    print("   export LLM_API_KEY=your_gemini_api_key")
    print("   export LLM_MODEL=gemini-2.5-flash")
    
    # Ollama (Local)
    print("\n🔹 Ollama Configuration (Local, Free):")
    print("   1. Install Ollama: https://ollama.ai")
    print("   2. Pull model: ollama pull llama3.2")
    print("   3. Start service: ollama serve")
    print("   4. Set: export LLM_PROVIDER=ollama")
    
    # OpenAI
    print("\n🔹 OpenAI Configuration:")
    print("   export LLM_PROVIDER=openai")
    print("   export LLM_API_KEY=your_openai_api_key")
    print("   export LLM_MODEL=gpt-4")
    
    # Anthropic
    print("\n🔹 Anthropic Configuration:")
    print("   export LLM_PROVIDER=anthropic")
    print("   export LLM_API_KEY=your_anthropic_api_key")
    print("   export LLM_MODEL=claude-3-sonnet-20240229")

def error_handling_example():
    """Demonstrate error handling patterns."""
    print("\n🛡️ Error Handling Example")
    print("-" * 40)
    
    from presentation_generator import (
        ConfigurationError,
        ContentGenerationError,
        MediaProcessingError
    )
    
    try:
        # This will likely fail without proper configuration
        config = Config(llm_provider="invalid_provider")
        generator = PresentationGenerator(config)
        
    except ConfigurationError as e:
        print(f"⚠️ Configuration Error: {e}")
    except ContentGenerationError as e:
        print(f"⚠️ Content Generation Error: {e}")
    except MediaProcessingError as e:
        print(f"⚠️ Media Processing Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def main():
    """Run all examples."""
    print("🎬 Presentation Generator Library - Usage Examples")
    print("=" * 60)
    
    # Check if API key is set
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("💡 Set LLM_API_KEY environment variable to run generation examples")
        print("   For Ollama (local), no API key is needed")
        print()
    
    # Run examples
    basic_usage()
    advanced_configuration()
    convenience_functions()
    provider_examples()
    error_handling_example()
    
    print("\n" + "=" * 60)
    print("✨ Examples completed!")
    print("\n📚 Next steps:")
    print("   1. Set up your preferred LLM provider")
    print("   2. Configure API keys or install Ollama")
    print("   3. Try generating your first presentation!")
    print("   4. Check the output directory for generated files")

if __name__ == "__main__":
    main()