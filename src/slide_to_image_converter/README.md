# Slide to Image Converter

A clean, minimal Python utility for converting Markdown slides to PNG images.

## Features

- Convert Markdown text to styled PNG images
- Process entire presentations from JSON files
- Customizable dimensions and browser engines
- Professional default template with clean styling
- Simple, intuitive API

## Installation

```bash
pip install markdown2 playwright jinja2
playwright install
```

## Quick Start

### Single Slide

```python
from slide_converter import SlideProcessor

processor = SlideProcessor()
processor.process_single_slide(
    markdown_text="# Hello World\n\nMy first slide!",
    output_path="slide.png"
)
```

### Presentation from JSON

```python
processor = SlideProcessor()
results = processor.process_presentation(
    json_path="presentation.json",
    output_dir="output/"
)
print(f"Generated {results['successful']} slides")
```

### Presentation with Image Path Updates

```python
# Process presentation and automatically add image paths to JSON
processor = SlideProcessor()
results = processor.process_presentation_with_update(
    json_path="presentation.json",
    output_dir="output/",
    save_updated_json=True  # Saves updated JSON with slide_image_path fields
)

# Each slide in the JSON will now have a 'slide_image_path' field
# pointing to the generated PNG file
```

### Custom Configuration

```python
from slide_converter import SlideProcessor, Config

config = Config(
    width=1280,
    height=720,
    browser="firefox"
)

processor = SlideProcessor(config)
```

## JSON Format

### Input Format
```json
{
  "slides": [
    {
      "slide_text": "# Slide Title\n\nSlide content in Markdown",
      "sub_subject": "Optional slide name",
      "talking_script": "Optional speaker notes"
    }
  ]
}
```

### Output Format (after processing with image paths)
```json
{
  "slides": [
    {
      "slide_text": "# Slide Title\n\nSlide content in Markdown",
      "sub_subject": "Optional slide name", 
      "talking_script": "Optional speaker notes",
      "slide_image_path": "output/slide_01_slide_title.png"
    }
  ]
}
```

The `slide_image_path` field is automatically added when using `process_presentation_with_update()`.

## API Reference

### SlideProcessor

Main class for processing slides.

**Methods:**
- `process_single_slide(markdown_text, output_path, slide_number=1)`
- `process_presentation(json_path, output_dir)` - Process presentation and return results
- `process_presentation_with_update(json_path, output_dir, save_updated_json=True)` - Process presentation and add image paths to JSON

### Config

Configuration class for customizing behavior.

**Parameters:**
- `width`: Image width in pixels (default: 1920)
- `height`: Image height in pixels (default: 1080)  
- `browser`: Browser engine - "chromium", "firefox", or "webkit" (default: "chromium")
- `timeout`: Browser timeout in milliseconds (default: 30000)
- `template_path`: Path to custom HTML template (optional)

### Exceptions

- `SlideConverterError`: Base exception
- `MarkdownError`: Markdown conversion errors
- `RenderError`: HTML rendering errors
- `ValidationError`: Input validation errors

## License

MIT License