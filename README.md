# Presentation Generator Library

A clean Python library for generating complete video presentations from topics using AI. Transforms any topic into a structured presentation with slides, images, audio narration, and final video output.

## 🚀 Features

- **Complete Workflow**: Topic → Content → Slides → Images → Audio → Video
- **Multi-Provider LLM Support**: Choose from Gemini, Ollama, OpenAI, or Anthropic
- **Intelligent Content Generation**: Automatically breaks down topics into logical slides
- **Media Processing**: Generates slide images, TTS audio, and assembles final video
- **Simple API**: Clean Python library interface with minimal configuration
- **Error Recovery**: Robust error handling with retry mechanisms
- **Resource Management**: Automatic cleanup of temporary files
- **Programmatic Integration**: Easy to integrate into existing Python applications

## 🛠️ Supported LLM Providers

| Provider | Models | API Key Required | Best For |
|----------|--------|------------------|----------|
| **Google Gemini** | gemini-2.5-flash, gemini-1.5-pro | ✅ Yes | Fast, high-quality generation |
| **Ollama** | llama3.2, mistral, codellama | ❌ No | Privacy, offline, cost-free |
| **OpenAI** | gpt-4, gpt-3.5-turbo | ✅ Yes | Proven performance |
| **Anthropic** | claude-3-sonnet, claude-3-haiku | ✅ Yes | Thoughtful, nuanced content |

## 📦 Installation

```bash
pip install presentation-generator
```

Or for development:

```bash
git clone <repository-url>
cd presentation-generator
pip install -e .
```

## ⚙️ Configuration

### Environment Variables

#### For Gemini (Default)
```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=your_gemini_api_key_here
```

#### For Ollama (Local, Free)
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_BASE_URL=http://localhost:11434
```

#### For OpenAI
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_API_KEY=your_openai_api_key_here
```

#### For Anthropic
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
LLM_API_KEY=your_anthropic_api_key_here
```

### Advanced Configuration
```env
LLM_TEMPERATURE=0.7          # Creativity level (0.0-2.0)
LLM_MAX_TOKENS=2048          # Maximum response length
LLM_TIMEOUT=30.0             # Request timeout in seconds
MAX_SUB_SUBJECTS=8           # Maximum number of slides
MIN_SUB_SUBJECTS=3           # Minimum number of slides
SLIDE_TEXT_MAX_LENGTH=500    # Maximum slide content length
SCRIPT_MIN_LENGTH=200        # Minimum script length
```

## 🎯 Usage

### Quick Start

```python
from presentation_generator import PresentationGenerator

# Simple usage - generates complete video presentation
generator = PresentationGenerator()
result = generator.generate("Machine Learning Basics")
presentation = result.presentation

print(f"✅ Video created: {presentation.video_path}")
print(f"📊 Generated {len(presentation.slides)} slides")

# Access individual slide data
for i, slide in enumerate(presentation.slides, 1):
    print(f"Slide {i}: {slide.title}")
    print(f"  Image: {slide.image_path}")
    print(f"  Audio: {slide.audio_path}")
    print(f"  Duration: {slide.duration:.1f}s")
```

### Advanced Configuration

```python
from presentation_generator import PresentationGenerator, Config

# Configure with specific provider and settings
config = Config(
    llm_provider="gemini",
    api_key="your-api-key",
    model="gemini-2.5-flash",
    output_dir="./my_presentations",
    slide_count=6,
    temperature=0.7
)

generator = PresentationGenerator(config)
result = generator.generate("AI Ethics in Healthcare")
presentation = result.presentation
```

### Convenience Functions

```python
from presentation_generator import create_generator, quick_generate, get_supported_providers

# Quick generator creation
generator = create_generator("gemini", "your-api-key", slide_count=5)
presentation = generator.generate("Python Fundamentals")

# One-liner generation
result = quick_generate("Data Science Basics", "gemini", "your-api-key")

# Check supported providers
providers = get_supported_providers()
print(f"Available providers: {providers}")
```

### Error Handling

```python
from presentation_generator import (
    PresentationGenerator, 
    ConfigurationError,
    ContentGenerationError,
    MediaProcessingError
)

try:
    generator = PresentationGenerator()
    result = generator.generate("Advanced Topics")
    
except ConfigurationError as e:
    print(f"Configuration issue: {e}")
except ContentGenerationError as e:
    print(f"Content generation failed: {e}")
except MediaProcessingError as e:
    print(f"Media processing failed: {e}")
```

## 🚀 Quick Start Example

Run the included example to see the library in action:

```bash
# Set your API key (for Gemini, OpenAI, or Anthropic)
export LLM_API_KEY=your_api_key_here
export LLM_PROVIDER=gemini

# Run the example
python example.py
```

The example demonstrates:
- Basic usage patterns
- Advanced configuration
- Multiple provider setups
- Error handling
- Convenience functions

## 🔧 Setting Up Ollama (Local AI)

For local, privacy-focused AI:

1. **Install Ollama**: Download from https://ollama.ai
2. **Pull a model**: `ollama pull llama3.2`
3. **Start service**: `ollama serve`
4. **Configure**: Set `LLM_PROVIDER=ollama` in environment

```bash
# No API key needed for Ollama
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.2
python example.py
```

## 📁 Library Architecture

The library follows a clean, modular architecture:

```
presentation_generator/
├── __init__.py              # Public API exports and convenience functions
├── core/
│   ├── generator.py         # PresentationGenerator - main orchestrator
│   ├── content.py          # ContentGenerator - LLM content creation
│   └── workflow.py         # WorkflowManager - step coordination
├── providers/
│   ├── base.py             # Abstract LLMProvider interface
│   ├── gemini.py           # Google Gemini implementation
│   ├── openai.py           # OpenAI GPT implementation
│   ├── anthropic.py        # Anthropic Claude implementation
│   └── ollama.py           # Ollama local AI implementation
├── media/
│   ├── images.py           # Slide-to-image conversion
│   ├── audio.py            # Text-to-speech generation
│   └── video.py            # Video assembly and compilation
├── models/
│   └── data.py             # Slide, Presentation, Config data models
└── utils/
    ├── config.py           # Configuration management
    └── exceptions.py       # Custom exception classes
```

### Design Principles

- **Single Responsibility**: Each module has a clear, focused purpose
- **Provider Abstraction**: LLM providers are interchangeable via common interface
- **Clean API**: Internal complexity is hidden behind simple public methods
- **Error Recovery**: Robust error handling with meaningful error messages
- **Resource Management**: Automatic cleanup of temporary files and resources

## 🧪 Testing

```bash
# Run the test suite
pytest

# Run with coverage
pytest --cov=presentation_generator
```

## 📚 API Reference

### Core Classes

#### `PresentationGenerator`

The main class for generating presentations.

```python
class PresentationGenerator:
    def __init__(self, config: Config = None)
    def generate(self, topic: str, **options) -> PresentationResult
    def get_supported_providers(self) -> List[str]
```

**Methods:**
- `generate(topic, **options)`: Generate a complete presentation from a topic
- `get_supported_providers()`: Get list of available LLM providers

#### `Config`

Configuration class for customizing generation behavior.

```python
class Config:
    llm_provider: str = "gemini"           # LLM provider to use
    api_key: Optional[str] = None          # API key for provider
    model: Optional[str] = None            # Specific model name
    output_dir: str = "./output"           # Output directory
    slide_count: Optional[int] = None      # Number of slides (auto if None)
    temperature: float = 0.7               # LLM creativity (0.0-2.0)
    max_tokens: int = 2048                 # Maximum response tokens
    timeout: float = 30.0                  # Request timeout
```

**Methods:**
- `validate_for_generation()`: Validate configuration before generation
- `get_provider_config()`: Get provider-specific configuration
- `get_media_config()`: Get media processing configuration

### Data Models

#### `PresentationResult`

Result object returned by generation methods.

```python
@dataclass
class PresentationResult:
    presentation: Presentation             # The generated presentation
    json_path: Optional[str] = None       # Path to JSON serialization
```

#### `Presentation`

Complete presentation with all generated assets.

```python
@dataclass
class Presentation:
    topic: str                            # Original topic
    slides: List[Slide]                   # List of generated slides
    video_path: Optional[str] = None      # Path to final video (main output)
    metadata: Dict[str, Any]              # Additional metadata
    created_at: datetime                  # Creation timestamp
```

#### `Slide`

Individual slide with all associated media.

```python
@dataclass
class Slide:
    title: str                            # Slide title
    content: str                          # Slide content/text
    script: str                           # Narration script
    image_path: Optional[str] = None      # Path to slide image
    audio_path: Optional[str] = None      # Path to narration audio
    duration: Optional[float] = None      # Duration in seconds (auto-calculated)
```

### Convenience Functions

#### `create_generator(provider, api_key, **kwargs)`

Create a PresentationGenerator with simplified configuration.

```python
generator = create_generator("gemini", "your-api-key", slide_count=5)
```

#### `quick_generate(topic, provider, api_key, **kwargs)`

Generate a presentation with minimal setup.

```python
result = quick_generate("Python Basics", "gemini", "your-api-key")
```

#### `get_supported_providers()`

Get list of supported LLM providers.

```python
providers = get_supported_providers()  # ["gemini", "openai", "anthropic", "ollama"]
```

### Exception Classes

All exceptions inherit from `PresentationGeneratorError`:

- `ConfigurationError`: Configuration or setup issues
- `ContentGenerationError`: LLM content generation failures
- `MediaProcessingError`: Image, audio, or video processing failures
- `ProviderError`: LLM provider-specific errors
- `ValidationError`: Input validation failures
- `WorkflowError`: Workflow orchestration issues

## 📊 Output Structure

Generated presentations create the following file structure:

```
output/
└── presentations/
    └── {topic_slug}_{timestamp}/
        ├── presentation.json          # Serialized presentation data
        ├── slides/
        │   ├── slide_001.png         # Individual slide images
        │   ├── slide_002.png
        │   └── ...
        ├── audio/
        │   ├── slide_001.wav         # Individual narration files
        │   ├── slide_002.wav
        │   └── ...
        └── presentation.mp4          # Final video (main output)
```

## 🔍 Troubleshooting

### Common Issues

**"Provider not supported" Error**
```python
# Ensure provider is one of the supported options
from presentation_generator import get_supported_providers
print(get_supported_providers())  # ["gemini", "openai", "anthropic", "ollama"]
```

**"API key required" Error**
```python
# Set API key in Config or environment
config = Config(llm_provider="gemini", api_key="your-key")
# OR set environment variable
# export LLM_API_KEY=your-key
```

**"Connection failed" Error**
- **Ollama**: Ensure service is running (`ollama serve`)
- **Cloud providers**: Check API key and internet connection
- **Firewall**: Ensure outbound HTTPS connections are allowed

**"No slides generated" Error**
- Check if the topic is too vague or complex
- Try increasing `max_tokens` in configuration
- Verify LLM provider is responding correctly

**"Media processing failed" Error**
- Ensure FFmpeg is installed for video generation
- Check disk space in output directory
- Verify write permissions for output directory

**"Import Error" when using the library**
```bash
# Ensure the library is properly installed
pip install -e .
# OR
pip install presentation-generator
```

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from presentation_generator import PresentationGenerator
generator = PresentationGenerator()
# Debug output will show detailed execution steps
```

### Getting Help

1. Check the [example.py](example.py) file for working usage patterns
2. Verify your configuration with the provider's documentation
3. Test with a simple topic first (e.g., "Introduction to Python")
4. Check the generated output directory for partial results

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/) for LLM integration
- Supports [Ollama](https://ollama.ai/) for local AI models
- Thanks to all the open-source AI model providers

## 🔗 Integration Examples

### Web Application Integration

```python
from flask import Flask, request, jsonify
from presentation_generator import PresentationGenerator, Config

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate_presentation():
    topic = request.json.get('topic')
    
    config = Config(
        llm_provider="gemini",
        api_key=os.getenv("LLM_API_KEY"),
        output_dir="./web_presentations"
    )
    
    generator = PresentationGenerator(config)
    result = generator.generate(topic)
    
    return jsonify({
        'video_path': result.presentation.video_path,
        'slides': len(result.presentation.slides),
        'topic': result.presentation.topic
    })
```

### Batch Processing

```python
from presentation_generator import create_generator

def batch_generate(topics, provider="gemini", api_key=None):
    """Generate multiple presentations in batch."""
    generator = create_generator(provider, api_key)
    results = []
    
    for topic in topics:
        try:
            result = generator.generate(topic)
            results.append({
                'topic': topic,
                'success': True,
                'video_path': result.presentation.video_path
            })
        except Exception as e:
            results.append({
                'topic': topic,
                'success': False,
                'error': str(e)
            })
    
    return results

# Usage
topics = ["Python Basics", "Machine Learning", "Data Science"]
results = batch_generate(topics, "gemini", "your-api-key")
```

### Custom Configuration Management

```python
import yaml
from presentation_generator import Config, PresentationGenerator

def load_custom_config(config_file):
    """Load configuration from YAML file."""
    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)
    
    return Config(**config_data)

# config.yaml
# llm_provider: gemini
# api_key: your-key
# slide_count: 6
# temperature: 0.8

config = load_custom_config('config.yaml')
generator = PresentationGenerator(config)
```

## 📚 Additional Resources

- [example.py](example.py) - Complete usage examples and patterns
- [High-Level Design](HLD.md) - Technical architecture overview  
- [Product Requirements](PRD.md) - Feature specifications

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the existing code style and architecture
4. Add tests for new functionality
5. Update documentation as needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Setup

```bash
# Clone and install in development mode
git clone <repository-url>
cd presentation-generator
pip install -e .

# Run tests
pytest

# Run the example
python example.py
```

---

**Made with ❤️ for the AI community**