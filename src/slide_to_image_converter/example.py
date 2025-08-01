#!/usr/bin/env python3
"""
Simple example demonstrating the slide converter.
"""

import json
from pathlib import Path
from slide_converter import SlideProcessor, Config

def main():
    """Run example conversions."""
    print("Slide Converter Example")
    print("=" * 30)
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Example 1: Single slide with default settings
    print("\n1. Single slide (default settings)")
    processor = SlideProcessor()
    
    markdown_content = """# Welcome to Slide Converter

## A Clean, Minimal Solution

This slide demonstrates the **slide-to-image-converter** capabilities:

### Key Features:
- **Simple API**: Easy to use and integrate
- **Markdown Support**: Rich formatting with tables, code, lists
- **Multiple Formats**: Support for different image dimensions
- **Browser Engines**: Chromium, Firefox, and WebKit support

### Example Code:
```python
from slide_converter import SlideProcessor

processor = SlideProcessor()
processor.process_single_slide(markdown_text, "slide.png")
```

> Clean, professional, and efficient!
"""
    
    processor.process_single_slide(
        markdown_content, 
        output_dir / "welcome.png"
    )
    print("   ✓ Generated: output/welcome.png")
    
    # Example 2: Custom configuration
    print("\n2. Custom configuration (HD, Firefox)")
    config = Config(
        width=1280,
        height=720,
        browser="chromium"  # Use chromium as it's most reliable
    )
    
    hd_processor = SlideProcessor(config)
    hd_processor.process_single_slide(
        "# HD Slide\n\nThis slide is rendered in 1280x720 resolution.",
        output_dir / "hd_slide.png"
    )
    print("   ✓ Generated: output/hd_slide.png")
    
    # Example 3: Presentation from JSON
    print("\n3. Presentation from JSON")
    
    # Create sample presentation
    presentation = {
        "slides": [
            {
                "slide_text": "# Introduction\n\nWelcome to our presentation!",
                "sub_subject": "Introduction"
            },
            {
                "slide_text": "# Features\n\n- Easy to use\n- Professional output\n- Multiple formats",
                "sub_subject": "Features"
            },
            {
                "slide_text": "# Thank You\n\nQuestions?",
                "sub_subject": "Conclusion"
            }
        ]
    }
    
    # Save JSON
    json_path = output_dir / "presentation.json"
    with open(json_path, 'w') as f:
        json.dump(presentation, f, indent=2)
    
    # Process presentation
    results = processor.process_presentation(
        json_path,
        output_dir / "presentation"
    )
    
    print(f"   ✓ Generated {results['successful']} slides:")
    for file_path in results['generated_files']:
        print(f"     - {Path(file_path).name}")
    
    print(f"\n✓ All examples completed!")
    print(f"  Check the 'output' directory for generated files.")

if __name__ == "__main__":
    json_path = r"C:\Users\SHIRA\Documents\AI\Auto_curs\output\presentation_data_structures_20250728_174615.json"
    output_dir = Path("output")
    processor = SlideProcessor()
    processor.process_presentation_with_update(
        json_path,
        output_dir / "presentation_2"
    )
