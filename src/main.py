#!/usr/bin/env python3
"""
Main CLI interface for the Interactive Presentation Generator.

This module provides a command-line interface using Click for generating
presentations from user input subjects using LangChain and Gemini AI.
"""

import sys
import os
import click
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.content_generator import ContentGenerator, GenerationProgress
from src.core.input_handler import InputHandler
from src.core.json_serializer import JSONSerializer
from src.integrations.langchain_integration import LLMClient
from src.utils.config import Config, load_config
from src.utils.logger import get_logger
from src.utils.exceptions import (
    PresentationGeneratorError,
    ContentGenerationError,
    ConfigurationError,
    InputValidationError
)

logger = get_logger(__name__)


class ProgressDisplay:
    """Handles progress display for CLI interface."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.last_progress = None
    
    def update_progress(self, progress: GenerationProgress):
        """Update progress display."""
        if not self.verbose and progress.current_step == self.last_progress:
            return
        
        # Create progress bar
        progress_bar = self._create_progress_bar(progress.progress_percentage)
        
        # Display current step
        click.echo(f"\r{progress_bar} {progress.current_step}", nl=False)
        
        # Show slide progress if available
        if progress.current_slide and progress.total_slides:
            slide_info = f" (Slide {progress.current_slide}/{progress.total_slides})"
            click.echo(slide_info, nl=False)
        
        # Show elapsed time
        if progress.elapsed_time > 0:
            elapsed = f" [{progress.elapsed_time:.1f}s]"
            click.echo(elapsed, nl=False)
        
        # New line for completed steps or verbose mode
        if progress.current_step == "Complete" or self.verbose:
            click.echo()
        
        self.last_progress = progress.current_step
    
    def _create_progress_bar(self, percentage: float, width: int = 30) -> str:
        """Create a visual progress bar."""
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage:.1f}%"


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def cli(ctx, version):
    """
    Interactive Presentation Generator
    
    Generate structured presentations with slides and narration scripts
    from any subject using AI-powered content generation.
    """
    if version:
        click.echo("Interactive Presentation Generator v1.0.0")
        click.echo("Powered by LangChain with multi-provider support")
        return
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument('subject', required=False)
@click.option('--output', '-o', 
              help='Output file path (default: auto-generated in output directory)')
@click.option('--verbose', '-v', is_flag=True, 
              help='Enable verbose output with detailed progress')
@click.option('--config-check', is_flag=True,
              help='Check configuration and exit')
def generate(subject: Optional[str], output: Optional[str], verbose: bool, config_check: bool):
    """
    Generate a presentation from a subject.
    
    SUBJECT: The main topic for your presentation (can be provided interactively)
    
    Examples:
    
        # Generate presentation interactively
        python -m src.main generate
        
        # Generate with subject as argument
        python -m src.main generate "Machine Learning Basics"
        
        # Generate with custom output file
        python -m src.main generate "AI Ethics" --output my_presentation.json
        
        # Generate with verbose progress
        python -m src.main generate "Climate Change" --verbose
    """
    try:
        # Load and validate configuration
        click.echo("🔧 Loading configuration...")
        config = load_config()
        
        if config_check:
            click.echo("✅ Configuration is valid!")
            click.echo(f"   Provider: {config.llm_provider}")
            click.echo(f"   Model: {config.llm_model}")
            click.echo(f"   Output directory: {config.output_directory}")
            click.echo(f"   Max sub-subjects: {config.max_sub_subjects}")
            return
        
        # Get subject input if not provided
        if not subject:
            subject = click.prompt(
                "\n📝 Enter your presentation subject",
                type=str,
                show_default=False
            )
        
        # Handle empty string input
        if not subject or not subject.strip():
            raise InputValidationError("Subject cannot be empty. Please provide a valid presentation topic.")
        
        # Validate input
        click.echo("\n🔍 Validating input...")
        input_handler = InputHandler()
        
        if not input_handler.validate_subject(subject):
            raise InputValidationError("Invalid subject provided")
        
        subject = input_handler.sanitize_input(subject)
        click.echo(f"   Subject: {subject}")
        
        # Initialize components
        click.echo(f"\n🚀 Initializing AI components ({config.llm_provider})...")
        llm_client = LLMClient(config)
        content_generator = ContentGenerator(llm_client, config)
        
        # Set up progress tracking
        progress_display = ProgressDisplay(verbose=verbose)
        content_generator.set_progress_callback(progress_display.update_progress)
        
        # Generate presentation
        click.echo(f"\n🎯 Generating presentation for: '{subject}'")
        click.echo("   This may take a few minutes...\n")
        
        presentation = content_generator.generate_presentation(subject)
        
        # Clear progress line and show completion
        click.echo("\n✅ Presentation generated successfully!")
        click.echo(f"   📊 Generated {presentation.total_slides} slides")
        click.echo(f"   ⏱️  Total time: {(datetime.now() - presentation.created_at).total_seconds():.1f} seconds")
        
        # Save to file
        click.echo("\n💾 Saving presentation...")
        json_serializer = JSONSerializer(config.output_directory)
        
        if not output:
            # Generate default filename
            safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_subject = safe_subject.replace(' ', '_').lower()[:50]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"presentation_{safe_subject}_{timestamp}.json"
        
        # Serialize presentation to JSON
        json_data = json_serializer.serialize_presentation(presentation)
        output_path = json_serializer.save_to_file(json_data, output)
        
        click.echo(f"✅ Presentation saved to: {output_path}")
        
        # Show summary
        click.echo("\n📋 Presentation Summary:")
        click.echo(f"   Main Subject: {presentation.main_subject}")
        click.echo(f"   Total Slides: {presentation.total_slides}")
        click.echo(f"   Created: {presentation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if verbose:
            click.echo("\n📑 Slide Topics:")
            for i, slide in enumerate(presentation.slides, 1):
                click.echo(f"   {i}. {slide.sub_subject}")
        
        click.echo(f"\n🎉 Your presentation is ready! Open {output_path} to view the complete content.")
        
    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Generation cancelled by user.")
        sys.exit(1)
        
    except ConfigurationError as e:
        click.echo(f"\n❌ Configuration Error: {e}", err=True)
        click.echo("\n💡 Please check your .env file and ensure LLM_PROVIDER and required API keys are set.", err=True)
        sys.exit(1)
        
    except InputValidationError as e:
        click.echo(f"\n❌ Input Error: {e}", err=True)
        click.echo("\n💡 Please provide a valid presentation subject.", err=True)
        sys.exit(1)
        
    except ContentGenerationError as e:
        click.echo(f"\n❌ Generation Error: {e}", err=True)
        if hasattr(e, 'generation_step'):
            click.echo(f"   Failed at step: {e.generation_step}", err=True)
        click.echo("\n💡 This might be a temporary API issue. Please try again.", err=True)
        sys.exit(1)
        
    except PresentationGeneratorError as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        if verbose and hasattr(e, 'details'):
            click.echo(f"   Details: {e.details}", err=True)
        sys.exit(1)
        
    except Exception as e:
        click.echo(f"\n❌ Unexpected Error: {e}", err=True)
        if verbose:
            import traceback
            click.echo("\n🔍 Full traceback:", err=True)
            click.echo(traceback.format_exc(), err=True)
        click.echo("\n💡 Please report this issue if it persists.", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--format', 'output_format', 
              type=click.Choice(['summary', 'detailed', 'json']),
              default='summary',
              help='Output format for viewing the presentation')
def view(file_path: str, output_format: str):
    """
    View a generated presentation file.
    
    FILE_PATH: Path to the JSON presentation file
    
    Examples:
    
        # View presentation summary
        python -m src.main view presentation.json
        
        # View detailed content
        python -m src.main view presentation.json --format detailed
        
        # View raw JSON
        python -m src.main view presentation.json --format json
    """
    try:
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if output_format == 'json':
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
            return
        
        # Display presentation info
        click.echo(f"📋 Presentation: {data['main_subject']}")
        click.echo(f"📅 Created: {data['created_at']}")
        click.echo(f"📊 Total Slides: {data['metadata']['total_slides']}")
        click.echo()
        
        if output_format == 'summary':
            click.echo("📑 Slide Topics:")
            for i, slide in enumerate(data['slides'], 1):
                click.echo(f"   {i}. {slide['sub_subject']}")
        
        elif output_format == 'detailed':
            for i, slide in enumerate(data['slides'], 1):
                click.echo(f"📄 Slide {i}: {slide['sub_subject']}")
                click.echo(f"   Content: {slide['slide_text'][:100]}...")
                click.echo(f"   Script: {slide['talking_script'][:100]}...")
                click.echo()
        
    except json.JSONDecodeError as e:
        click.echo(f"❌ Invalid JSON file: {e}", err=True)
        sys.exit(1)
    except KeyError as e:
        click.echo(f"❌ Invalid presentation file format: missing {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error reading file: {e}", err=True)
        sys.exit(1)


@cli.command()
def config():
    """Show current configuration and environment setup."""
    try:
        config = load_config()
        
        click.echo("🔧 Current Configuration:")
        click.echo(f"   Provider: {config.llm_provider}")
        click.echo(f"   Model: {config.llm_model}")
        click.echo(f"   Temperature: {config.llm_temperature}")
        click.echo(f"   Max Tokens: {config.llm_max_tokens}")
        click.echo(f"   Timeout: {config.llm_timeout}s")
        if config.llm_base_url:
            click.echo(f"   Base URL: {config.llm_base_url}")
        click.echo(f"   Output Directory: {config.output_directory}")
        click.echo(f"   Max Sub-subjects: {config.max_sub_subjects}")
        click.echo(f"   Min Sub-subjects: {config.min_sub_subjects}")
        click.echo(f"   Max Slide Length: {config.slide_text_max_length}")
        click.echo(f"   Min Script Length: {config.script_min_length}")
        click.echo(f"   Max Retries: {config.max_retries}")
        click.echo(f"   Rate Limit Delay: {config.rate_limit_delay}s")
        
        # Check API key (if required for the provider)
        if config.llm_provider in ["gemini", "openai", "anthropic"]:
            if config.llm_api_key:
                masked_key = config.llm_api_key[:8] + "..." + config.llm_api_key[-4:]
                click.echo(f"   API Key: {masked_key} ✅")
            else:
                click.echo("   API Key: Not set ❌")
        else:
            click.echo("   API Key: Not required for this provider ✅")
        
        # Check output directory
        output_path = Path(config.output_directory)
        if output_path.exists():
            click.echo(f"   Output Directory: Exists ✅")
        else:
            click.echo(f"   Output Directory: Will be created ⚠️")
        
    except ConfigurationError as e:
        click.echo(f"❌ Configuration Error: {e}", err=True)
        click.echo("\n💡 Please check your .env file and ensure all required variables are set.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error loading configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
def examples():
    """Show usage examples and tips."""
    click.echo("🎯 Interactive Presentation Generator - Usage Examples")
    click.echo()
    
    click.echo("📝 Basic Usage:")
    click.echo("   python -m src.main generate")
    click.echo("   python -m src.main generate \"Machine Learning Basics\"")
    click.echo()
    
    click.echo("⚙️  Advanced Options:")
    click.echo("   python -m src.main generate \"AI Ethics\" --output ethics_presentation.json")
    click.echo("   python -m src.main generate \"Climate Change\" --verbose")
    click.echo()
    
    click.echo("👀 Viewing Presentations:")
    click.echo("   python -m src.main view presentation.json")
    click.echo("   python -m src.main view presentation.json --format detailed")
    click.echo()
    
    click.echo("🔧 Configuration:")
    click.echo("   python -m src.main config")
    click.echo("   python -m src.main generate --config-check")
    click.echo()
    
    click.echo("💡 Tips:")
    click.echo("   • Use specific, focused subjects for better results")
    click.echo("   • The AI generates 3-8 sub-topics automatically")
    click.echo("   • Each slide includes both content and talking script")
    click.echo("   • Generated files are saved in JSON format")
    click.echo("   • Use --verbose to see detailed progress")
    click.echo()
    
    click.echo("🚀 Example Subjects:")
    click.echo("   • \"Introduction to Python Programming\"")
    click.echo("   • \"Sustainable Energy Solutions\"")
    click.echo("   • \"Digital Marketing Strategies\"")
    click.echo("   • \"Space Exploration History\"")
    click.echo("   • \"Healthy Cooking Techniques\"")


@cli.command()
@click.option('--provider', 
              type=click.Choice(['gemini', 'ollama', 'openai', 'anthropic']),
              help='LLM provider to configure')
@click.option('--list-providers', is_flag=True,
              help='List all supported providers and their requirements')
def setup(provider: Optional[str], list_providers: bool):
    """
    Setup and configure LLM providers.
    
    This command helps you configure different LLM providers by showing
    requirements and generating example .env configurations.
    
    Examples:
    
        # List all supported providers
        python -m src.main setup --list-providers
        
        # Get setup instructions for Ollama
        python -m src.main setup --provider ollama
        
        # Get setup instructions for OpenAI
        python -m src.main setup --provider openai
    """
    from src.integrations.llm_providers import LLMProviderFactory, LLMProvider
    
    if list_providers:
        click.echo("🔧 Supported LLM Providers:")
        click.echo()
        
        provider_info = LLMProviderFactory.get_provider_info()
        
        for provider_enum, info in provider_info.items():
            click.echo(f"📦 {info['name']} ({provider_enum.value})")
            click.echo(f"   Description: {info['description']}")
            click.echo(f"   Requires API Key: {'Yes' if info['requires_api_key'] else 'No'}")
            click.echo(f"   Default Models: {', '.join(info['default_models'])}")
            if 'default_base_url' in info:
                click.echo(f"   Default URL: {info['default_base_url']}")
            click.echo()
        
        return
    
    if not provider:
        click.echo("❌ Please specify a provider with --provider or use --list-providers")
        return
    
    provider_info = LLMProviderFactory.get_provider_info()
    provider_enum = LLMProvider(provider)
    info = provider_info[provider_enum]
    
    click.echo(f"🔧 Setting up {info['name']}")
    click.echo(f"   {info['description']}")
    click.echo()
    
    # Provider-specific setup instructions
    if provider == 'gemini':
        click.echo("📋 Setup Instructions:")
        click.echo("1. Get a Google AI API key from: https://makersuite.google.com/app/apikey")
        click.echo("2. Add to your .env file:")
        click.echo()
        click.echo("   LLM_PROVIDER=gemini")
        click.echo("   LLM_MODEL=gemini-2.5-flash")
        click.echo("   LLM_API_KEY=your_gemini_api_key_here")
        click.echo()
        click.echo("💡 Alternative models: gemini-1.5-pro, gemini-1.5-flash")
        
    elif provider == 'ollama':
        click.echo("📋 Setup Instructions:")
        click.echo("1. Install Ollama from: https://ollama.ai")
        click.echo("2. Pull a model: ollama pull llama3.2")
        click.echo("3. Start Ollama service: ollama serve")
        click.echo("4. Add to your .env file:")
        click.echo()
        click.echo("   LLM_PROVIDER=ollama")
        click.echo("   LLM_MODEL=llama3.2")
        click.echo("   LLM_BASE_URL=http://localhost:11434")
        click.echo()
        click.echo("💡 Popular models: llama3.2, mistral, codellama, phi3")
        click.echo("💡 No API key required - runs locally!")
        
    elif provider == 'openai':
        click.echo("📋 Setup Instructions:")
        click.echo("1. Get an OpenAI API key from: https://platform.openai.com/api-keys")
        click.echo("2. Add to your .env file:")
        click.echo()
        click.echo("   LLM_PROVIDER=openai")
        click.echo("   LLM_MODEL=gpt-4")
        click.echo("   LLM_API_KEY=your_openai_api_key_here")
        click.echo()
        click.echo("💡 Alternative models: gpt-3.5-turbo, gpt-4-turbo")
        
    elif provider == 'anthropic':
        click.echo("📋 Setup Instructions:")
        click.echo("1. Get an Anthropic API key from: https://console.anthropic.com")
        click.echo("2. Add to your .env file:")
        click.echo()
        click.echo("   LLM_PROVIDER=anthropic")
        click.echo("   LLM_MODEL=claude-3-sonnet-20240229")
        click.echo("   LLM_API_KEY=your_anthropic_api_key_here")
        click.echo()
        click.echo("💡 Alternative models: claude-3-haiku-20240307, claude-3-opus-20240229")
    
    click.echo()
    click.echo("🧪 Test your configuration:")
    click.echo("   python -m src.main generate --config-check")
    click.echo()
    click.echo("🚀 Generate your first presentation:")
    click.echo("   python -m src.main generate \"Your Topic Here\"")


@cli.command()
def test_providers():
    """
    Test connection to all configured LLM providers.
    
    This command attempts to connect to and test all available
    LLM providers based on your current configuration.
    """
    from src.integrations.llm_providers import LLMProviderFactory, LLMProvider, LLMConfig
    
    click.echo("🧪 Testing LLM Provider Connections")
    click.echo()
    
    # Test current configuration
    try:
        config = load_config()
        click.echo(f"📋 Current Provider: {config.llm_provider}")
        
        llm_client = LLMClient(config)
        
        click.echo("   Testing connection...", nl=False)
        if llm_client.test_connection():
            click.echo(" ✅ Success!")
            
            # Show provider info
            provider_info = llm_client.get_provider_info()
            click.echo(f"   Model: {provider_info['current_model']}")
            click.echo(f"   Circuit Breaker: {provider_info['circuit_breaker_state']}")
        else:
            click.echo(" ❌ Failed!")
            
    except Exception as e:
        click.echo(f" ❌ Error: {e}")
    
    click.echo()
    click.echo("💡 Use 'python -m src.main setup --list-providers' to see all available providers")
    click.echo("💡 Use 'python -m src.main setup --provider <name>' for setup instructions")


if __name__ == '__main__':
    cli()