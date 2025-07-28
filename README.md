# Interactive Presentation Generator

A powerful AI-powered presentation generator that creates structured presentations with slides and narration scripts from any subject using multiple LLM providers.

## 🚀 Features

- **Multi-Provider LLM Support**: Choose from Gemini, Ollama, OpenAI, or Anthropic
- **Intelligent Content Generation**: Automatically breaks down topics into logical sub-subjects
- **Comprehensive Output**: Generates both slide content and detailed talking scripts
- **Local & Cloud Options**: Use free local models (Ollama) or cloud-based services
- **Progress Tracking**: Real-time progress updates during generation
- **Error Recovery**: Robust error handling with retry mechanisms
- **CLI Interface**: Easy-to-use command-line interface
- **JSON Export**: Structured output for easy integration

## 🛠️ Supported LLM Providers

| Provider | Models | API Key Required | Best For |
|----------|--------|------------------|----------|
| **Google Gemini** | gemini-2.5-flash, gemini-1.5-pro | ✅ Yes | Fast, high-quality generation |
| **Ollama** | llama3.2, mistral, codellama | ❌ No | Privacy, offline, cost-free |
| **OpenAI** | gpt-4, gpt-3.5-turbo | ✅ Yes | Proven performance |
| **Anthropic** | claude-3-sonnet, claude-3-haiku | ✅ Yes | Thoughtful, nuanced content |

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd interactive-presentation-generator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your environment**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred provider settings
   ```

## ⚙️ Configuration

### Quick Setup Commands

```bash
# List all available providers
python -m src.main setup --list-providers

# Get setup instructions for a specific provider
python -m src.main setup --provider ollama
python -m src.main setup --provider openai
```

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

```bash
# Interactive mode
python -m src.main generate

# Direct subject input
python -m src.main generate "Machine Learning Basics"

# With custom output file
python -m src.main generate "AI Ethics" --output my_presentation.json

# Verbose mode with detailed progress
python -m src.main generate "Climate Change" --verbose
```

### Configuration Management

```bash
# Check current configuration
python -m src.main config

# Test provider connection
python -m src.main test-providers

# Validate configuration
python -m src.main generate --config-check
```

### Viewing Generated Presentations

```bash
# View presentation summary
python -m src.main view presentation.json

# View detailed content
python -m src.main view presentation.json --format detailed

# View raw JSON
python -m src.main view presentation.json --format json
```

## 🔧 Setting Up Ollama (Local AI)

1. **Install Ollama**
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows: Download from https://ollama.ai
   ```

2. **Pull a model**
   ```bash
   ollama pull llama3.2
   # or try: mistral, codellama, phi3
   ```

3. **Start Ollama service**
   ```bash
   ollama serve
   ```

4. **Configure environment**
   ```env
   LLM_PROVIDER=ollama
   LLM_MODEL=llama3.2
   LLM_BASE_URL=http://localhost:11434
   ```

## 📁 Project Structure

```
├── src/
│   ├── core/                    # Core business logic
│   │   ├── content_generator.py # Main generation orchestrator
│   │   ├── input_handler.py     # Input validation and sanitization
│   │   └── json_serializer.py   # JSON output handling
│   ├── integrations/            # LLM provider integrations
│   │   ├── llm_client.py        # Unified LLM client (all providers)
│   │   └── langchain_integration.py # Legacy compatibility
│   ├── prompts/                 # AI prompts and templates
│   ├── utils/                   # Utilities and configuration
│   └── main.py                  # CLI interface
├── tests/                       # Test suite
├── docs/                        # Documentation
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🧪 Testing

```bash
# Run the test suite
python test_providers.py

# Test specific provider
python -m src.main test-providers

# Generate a test presentation
python -m src.main generate "Test Topic" --verbose
```

## 📊 Output Format

Generated presentations are saved as JSON files with the following structure:

```json
{
  "main_subject": "Your Topic",
  "created_at": "2024-01-01T12:00:00",
  "metadata": {
    "total_slides": 5,
    "generation_time": 45.2,
    "llm_provider": "gemini",
    "llm_model": "gemini-2.5-flash"
  },
  "slides": [
    {
      "slide_number": 1,
      "sub_subject": "Introduction",
      "slide_text": "• Key points for the slide...",
      "talking_script": "Welcome to this presentation about..."
    }
  ]
}
```

## 🔍 Troubleshooting

### Common Issues

**"Provider not supported" Error**
- Ensure `LLM_PROVIDER` is one of: `gemini`, `ollama`, `openai`, `anthropic`

**"API key required" Error**
- Set `LLM_API_KEY` for cloud providers
- Ollama doesn't require an API key

**"Connection failed" Error**
- For Ollama: Ensure service is running (`ollama serve`)
- For cloud providers: Check API key and internet connection

**"Model not found" Error**
- For Ollama: Pull the model first (`ollama pull model-name`)
- For cloud providers: Verify model name is correct

### Getting Help

```bash
# Show usage examples
python -m src.main examples

# Get provider-specific setup help
python -m src.main setup --provider <provider-name>

# Check configuration
python -m src.main config
```

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
- CLI powered by [Click](https://click.palletsprojects.com/)
- Thanks to all the open-source AI model providers

## 📚 Additional Resources

- [Multi-Provider Setup Guide](MULTI_PROVIDER_GUIDE.md) - Detailed setup instructions
- [High-Level Design](HLD.md) - Technical architecture overview
- [Product Requirements](PRD.md) - Feature specifications

---

**Made with ❤️ for the AI community**