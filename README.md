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

### Basic Usage

```python
from presentation_generator import PresentationGenerator

# Simple usage - generates complete video presentation
generator = PresentationGenerator()
presentation = generator.generate("Machine Learning Basics")
print(f"Video created: {presentation.video_path}")

# Access individual slide data
for slide in presentation.slides:
    print(f"Slide: {slide.title}")
    print(f"Image: {slide.image_path}")
    print(f"Audio: {slide.audio_path}")
    print(f"Duration: {slide.duration}s")
```

### Advanced Configuration

```python
from presentation_generator import PresentationGenerator, Config

# Configure with specific provider and settings
config = Config(
    llm_provider="gemini",
    api_key="your-key",
    output_dir="./presentations"
)

generator = PresentationGenerator(config)
presentation = generator.generate("AI Ethics")
```

## 🔧 Setting Up Ollama (Local AI)

For local, privacy-focused AI:

1. **Install Ollama**: Download from https://ollama.ai
2. **Pull a model**: `ollama pull llama3.2`
3. **Start service**: `ollama serve`
4. **Configure**: Set `LLM_PROVIDER=ollama` in environment

## 📁 Library Structure

```
presentation_generator/
├── __init__.py              # Public API exports
├── core/
│   ├── generator.py         # Main orchestrator class
│   ├── content.py          # Content generation logic
│   └── workflow.py         # Workflow management
├── providers/               # LLM provider implementations
├── media/                   # Image, audio, video processing
├── models/                  # Data models and types
└── utils/                   # Configuration and utilities
```

## 🧪 Testing

```bash
# Run the test suite
pytest

# Run with coverage
pytest --cov=presentation_generator
```

## 📊 Output Structure

The library returns a `Presentation` object with complete video and individual assets:

```python
@dataclass
class Presentation:
    topic: str
    slides: List[Slide]
    video_path: str              # Main output - complete video
    created_at: datetime

@dataclass  
class Slide:
    title: str
    content: str
    script: str
    image_path: str              # Generated slide image
    audio_path: str              # Generated narration audio
    duration: float              # Auto-calculated from audio
```

## 🔍 Troubleshooting

### Common Issues

**"Provider not supported" Error**
- Ensure `llm_provider` is one of: `gemini`, `ollama`, `openai`, `anthropic`

**"API key required" Error**
- Set API key in Config object or environment variables
- Ollama doesn't require an API key

**"Connection failed" Error**
- For Ollama: Ensure service is running (`ollama serve`)
- For cloud providers: Check API key and internet connection

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

## 📚 Additional Resources

- [Multi-Provider Setup Guide](MULTI_PROVIDER_GUIDE.md) - Detailed setup instructions
- [High-Level Design](HLD.md) - Technical architecture overview
- [Product Requirements](PRD.md) - Feature specifications

---

**Made with ❤️ for the AI community**