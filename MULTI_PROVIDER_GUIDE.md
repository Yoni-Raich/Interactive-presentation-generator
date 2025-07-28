# Multi-Provider LLM Support Guide

The Interactive Presentation Generator now supports multiple LLM providers, giving you flexibility to choose the AI service that best fits your needs.

## Supported Providers

### 🤖 Google Gemini (Default)
- **Provider**: `gemini`
- **Models**: `gemini-2.5-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`
- **Requires API Key**: Yes
- **Best For**: Fast, high-quality content generation with good reasoning

### 🦙 Ollama (Local)
- **Provider**: `ollama`
- **Models**: `llama3.2`, `mistral`, `codellama`, `phi3`, and many more
- **Requires API Key**: No (runs locally)
- **Best For**: Privacy, offline usage, cost-free operation

### 🧠 OpenAI
- **Provider**: `openai`
- **Models**: `gpt-4`, `gpt-3.5-turbo`, `gpt-4-turbo`
- **Requires API Key**: Yes
- **Best For**: Proven performance, extensive model options

### 🎭 Anthropic Claude
- **Provider**: `anthropic`
- **Models**: `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`, `claude-3-opus-20240229`
- **Requires API Key**: Yes
- **Best For**: Thoughtful, nuanced content generation

## Quick Setup

### 1. Using the Setup Command
```bash
# List all available providers
python -m src.main setup --list-providers

# Get setup instructions for a specific provider
python -m src.main setup --provider ollama
python -m src.main setup --provider openai
```

### 2. Environment Configuration

#### Gemini (Default)
```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=your_gemini_api_key_here
```

#### Ollama (Local)
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_BASE_URL=http://localhost:11434
```

#### OpenAI
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_API_KEY=your_openai_api_key_here
```

#### Anthropic
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
LLM_API_KEY=your_anthropic_api_key_here
```

## Detailed Setup Instructions

### Setting up Ollama (Recommended for Local Use)

1. **Install Ollama**
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows: Download from https://ollama.ai
   ```

2. **Pull a Model**
   ```bash
   ollama pull llama3.2
   # or
   ollama pull mistral
   ollama pull codellama
   ```

3. **Start Ollama Service**
   ```bash
   ollama serve
   ```

4. **Configure Environment**
   ```env
   LLM_PROVIDER=ollama
   LLM_MODEL=llama3.2
   LLM_BASE_URL=http://localhost:11434
   ```

### Setting up OpenAI

1. **Get API Key**
   - Visit [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create a new API key
   - Copy the key

2. **Configure Environment**
   ```env
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4
   LLM_API_KEY=sk-your-openai-key-here
   ```

### Setting up Anthropic

1. **Get API Key**
   - Visit [Anthropic Console](https://console.anthropic.com)
   - Create a new API key
   - Copy the key

2. **Configure Environment**
   ```env
   LLM_PROVIDER=anthropic
   LLM_MODEL=claude-3-sonnet-20240229
   LLM_API_KEY=your-anthropic-key-here
   ```

## Advanced Configuration

### Model-Specific Settings
```env
# Temperature (creativity): 0.0 (deterministic) to 2.0 (very creative)
LLM_TEMPERATURE=0.7

# Maximum tokens per response
LLM_MAX_TOKENS=2048

# Request timeout in seconds
LLM_TIMEOUT=30.0

# For local providers like Ollama
LLM_BASE_URL=http://localhost:11434
```

### Provider-Specific API Keys
You can also use provider-specific environment variables:
```env
# Instead of LLM_API_KEY, you can use:
GOOGLE_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

## Testing Your Setup

### Test Current Configuration
```bash
python -m src.main generate --config-check
```

### Test Provider Connection
```bash
python -m src.main test-providers
```

### View Current Configuration
```bash
python -m src.main config
```

## Usage Examples

### Generate with Different Providers
```bash
# Using Ollama (local)
LLM_PROVIDER=ollama python -m src.main generate "Machine Learning Basics"

# Using OpenAI
LLM_PROVIDER=openai python -m src.main generate "AI Ethics"

# Using Anthropic
LLM_PROVIDER=anthropic python -m src.main generate "Climate Change"
```

### Switching Providers
Simply update your `.env` file:
```env
# Switch from Gemini to Ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
# LLM_API_KEY not needed for Ollama
```

## Troubleshooting

### Common Issues

#### "Provider not supported" Error
- Check that `LLM_PROVIDER` is one of: `gemini`, `ollama`, `openai`, `anthropic`
- Ensure the provider name is lowercase

#### "API key required" Error
- Set `LLM_API_KEY` for cloud providers (Gemini, OpenAI, Anthropic)
- Ollama doesn't require an API key

#### "Connection failed" Error
- For Ollama: Ensure the service is running (`ollama serve`)
- For cloud providers: Check your API key and internet connection
- Verify the base URL for local providers

#### "Model not found" Error
- For Ollama: Pull the model first (`ollama pull model-name`)
- For cloud providers: Check the model name is correct

### Getting Help
```bash
# List all available providers and models
python -m src.main setup --list-providers

# Get setup instructions for a specific provider
python -m src.main setup --provider ollama

# Test your current configuration
python -m src.main test-providers
```

## Performance Comparison

| Provider | Speed | Quality | Cost | Privacy | Offline |
|----------|-------|---------|------|---------|---------|
| Gemini   | Fast  | High    | Low  | Cloud   | No      |
| Ollama   | Medium| Good    | Free | Local   | Yes     |
| OpenAI   | Fast  | High    | Medium| Cloud  | No      |
| Anthropic| Medium| High    | Medium| Cloud  | No      |

## Best Practices

1. **For Development**: Use Ollama for cost-free experimentation
2. **For Production**: Use Gemini or OpenAI for reliability
3. **For Privacy**: Use Ollama for sensitive content
4. **For Quality**: Try different providers and compare results
5. **For Speed**: Gemini and OpenAI are typically fastest

## Migration from Legacy Setup

If you're upgrading from the Gemini-only version:

### Old Configuration
```env
GOOGLE_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
```

### New Configuration (Backward Compatible)
```env
# New format (recommended)
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=your_key

# Old format still works
GOOGLE_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
```

The system automatically detects and uses legacy configuration if new format isn't provided.