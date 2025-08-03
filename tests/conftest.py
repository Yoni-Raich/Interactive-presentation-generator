"""
Pytest configuration and fixtures for presentation-generator tests.

This module provides common test fixtures, configuration, and utilities
for all test modules in the presentation-generator test suite.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
import sys
from unittest.mock import Mock

# Add presentation_generator to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_markdown():
    """Provide sample Markdown content for testing."""
    return """
# Sample Test Slide

This is a **sample slide** with various Markdown elements for testing.

## Key Features

- **Bold text** and *italic text*
- `Inline code` and code blocks
- [Links](https://example.com) and references

### Code Example

```python
def hello_world():
    print("Hello, World!")
    return True
```

### Table Example

| Feature | Status | Notes |
|---------|--------|-------|
| Markdown | ✅ | Working |
| HTML | ✅ | Working |
| PNG | ✅ | Working |

> This is a blockquote with important information.

---

## Conclusion

This sample demonstrates various Markdown formatting options.
"""


@pytest.fixture
def sample_html():
    """Provide sample HTML content for testing."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Slide</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f0f0f0;
            margin: 0;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .slide-container {
            background: white;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            max-width: 800px;
            width: 100%;
        }
        h1 { color: #333; }
        p { color: #666; line-height: 1.6; }
        .slide-footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="slide-container">
        <h1>Test Slide Title</h1>
        <p>This is a test slide with sample content for HTML rendering tests.</p>
        <ul>
            <li>Feature 1: HTML to PNG conversion</li>
            <li>Feature 2: Configurable dimensions</li>
            <li>Feature 3: Browser automation</li>
        </ul>
        <div class="slide-footer">
            <span>Slide 1</span>
        </div>
    </div>
</body>
</html>
"""


@pytest.fixture
def sample_presentation_json():
    """Provide sample presentation JSON data for testing."""
    return {
        "title": "Test Presentation",
        "author": "Test Suite",
        "created_at": "2024-01-01T00:00:00Z",
        "sub_subjects": [
            {
                "sub_subject": "Introduction",
                "slide_text": """
# Introduction

Welcome to our **test presentation**!

## Overview

This presentation demonstrates:
- Markdown to HTML conversion
- HTML to PNG rendering
- Batch processing capabilities

> Let's get started!
"""
            },
            {
                "sub_subject": "Features",
                "slide_text": """
# Key Features

## Core Functionality

### 1. Markdown Processing
- Support for standard Markdown syntax
- Code blocks with syntax highlighting
- Tables and lists
- Links and images

### 2. HTML Rendering
- High-quality PNG output
- Configurable dimensions
- Multiple browser support

### 3. Batch Processing
- JSON-based presentations
- Progress tracking
- Error handling

```python
# Example usage
processor = SlideProcessor()
processor.process_presentation_json("slides.json", "output/")
```
"""
            },
            {
                "sub_subject": "Conclusion",
                "slide_text": """
# Conclusion

## Summary

We've covered:
- [x] Markdown conversion
- [x] HTML rendering
- [x] Batch processing
- [x] Error handling

## Next Steps

1. Try the examples
2. Customize templates
3. Integrate with your workflow

**Thank you for your attention!**

| Feature | Status |
|---------|--------|
| Complete | ✅ |
| Tested | ✅ |
| Ready | ✅ |
"""
            }
        ]
    }


@pytest.fixture
def create_test_json_file(temp_dir, sample_presentation_json):
    """Create a test JSON file with sample presentation data."""
    def _create_json_file(filename="test_presentation.json", data=None):
        if data is None:
            data = sample_presentation_json
        
        json_file = temp_dir / filename
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return json_file
    
    return _create_json_file


@pytest.fixture
def mock_browser_success():
    """Provide a mock browser that succeeds in rendering."""
    from unittest.mock import Mock, patch
    
    def _mock_browser():
        mock_context = Mock()
        mock_browser = Mock()
        mock_page = Mock()
        
        mock_browser.new_page.return_value = mock_page
        mock_browser.is_connected.return_value = True
        
        return mock_context, mock_browser, mock_page
    
    return _mock_browser


@pytest.fixture
def complex_markdown():
    """Provide complex Markdown content for stress testing."""
    return """
# Complex Markdown Test Document

## Introduction

This document contains **complex formatting** to test the *robustness* of our Markdown processor.

### Unicode and Special Characters

- Emojis: 🚀 🎯 💻 📊 ⚡
- Accented: café, naïve, résumé, piñata
- Math symbols: α, β, γ, π, Σ, ∞, ≤, ≥
- Currency: $, €, £, ¥, ₹, ₿

### Nested Lists

1. **First level item**
   1. Second level numbered
   2. Another second level
      - Third level bullet
      - Another third level
        - Fourth level bullet
          - Fifth level bullet
            > Blockquote in deep list
            > 
            > With multiple lines
   3. Back to second level

2. **Another first level**
   - Mixed with bullets
     1. Numbered in bullets
     2. More numbered
       - Back to bullets

### Complex Tables

| Feature | Description | Status | Priority | Notes |
|---------|-------------|--------|----------|-------|
| **Markdown** | Text formatting | ✅ Complete | High | Core feature |
| *HTML* | Web rendering | ✅ Complete | High | Required |
| `PNG` | Image output | ✅ Complete | High | Final format |
| Tables | Data display | ✅ Complete | Medium | This table! |
| Links | [Navigation](http://example.com) | ✅ Complete | Low | External refs |

### Code Blocks

#### Python Example
```python
class ComplexExample:
    \"\"\"
    A complex example class with various features.
    \"\"\"
    
    def __init__(self, name: str, data: list):
        self.name = name
        self.data = data or []
        self._processed = False
    
    def process_data(self) -> dict:
        \"\"\"Process the data and return results.\"\"\"
        if self._processed:
            return {"status": "already_processed"}
        
        results = {
            "name": self.name,
            "count": len(self.data),
            "sum": sum(x for x in self.data if isinstance(x, (int, float))),
            "items": [str(item).upper() for item in self.data]
        }
        
        self._processed = True
        return results

# Usage example
example = ComplexExample("test", [1, 2, 3, "hello", 4.5])
result = example.process_data()
print(f"Result: {result}")
```

#### JavaScript Example
```javascript
/**
 * Complex JavaScript example with modern features
 */
class DataProcessor {
    constructor(config = {}) {
        this.config = {
            timeout: 5000,
            retries: 3,
            ...config
        };
        this.cache = new Map();
    }
    
    async processData(data) {
        const key = this.generateKey(data);
        
        if (this.cache.has(key)) {
            return this.cache.get(key);
        }
        
        try {
            const result = await this.performProcessing(data);
            this.cache.set(key, result);
            return result;
        } catch (error) {
            console.error(`Processing failed: ${error.message}`);
            throw error;
        }
    }
    
    generateKey(data) {
        return btoa(JSON.stringify(data)).slice(0, 16);
    }
    
    async performProcessing(data) {
        // Simulate async processing
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    processed: data.map(item => item * 2),
                    timestamp: new Date().toISOString()
                });
            }, 100);
        });
    }
}

// Usage
const processor = new DataProcessor({ timeout: 10000 });
processor.processData([1, 2, 3, 4, 5])
    .then(result => console.log('Success:', result))
    .catch(error => console.error('Error:', error));
```

### Complex Blockquotes

> **Important Note**: This is a complex blockquote with multiple elements.
> 
> It contains:
> - **Bold text**
> - *Italic text*
> - `Inline code`
> - [Links](https://example.com)
> 
> > **Nested Quote**: This is a nested blockquote within the main quote.
> > 
> > ```bash
> > # Even code blocks in nested quotes
> > echo "This is getting complex!"
> > ls -la | grep "test"
> > ```
> > 
> > | Column | Value |
> > |--------|-------|
> > | Test   | Data  |
> 
> Back to the main quote with more content.

### Mixed Content Stress Test

Here's a paragraph with **bold**, *italic*, ***bold italic***, `inline code`, and [a link](https://example.com "Link Title").

---

#### Horizontal Rules and Separators

Above and below this text are horizontal rules.

***

#### Task Lists

- [x] **Completed task** with formatting
- [ ] Incomplete task
  - [x] Nested completed subtask
  - [ ] Nested incomplete subtask
    - [x] Deep nested completed
    - [ ] Deep nested incomplete
- [x] Another completed task with `code`
- [ ] Task with [link](https://example.com)

#### Definition Lists (if supported)

Term 1
:   Definition 1 with **formatting**

Term 2
:   Definition 2 with *emphasis*
:   Multiple definitions for same term

#### Footnotes (if supported)

This text has a footnote[^1] and another one[^2].

[^1]: This is the first footnote with **formatting**.
[^2]: This is the second footnote with `code`.

### Final Complex Table

| **Feature** | **Markdown** | **HTML** | **Rendering** | **Notes** |
|:------------|:-------------|:---------|:--------------|:----------|
| Headers | `# ## ###` | `<h1> <h2> <h3>` | ✅ Working | All levels |
| **Bold** | `**text**` | `<strong>` | ✅ Working | Emphasis |
| *Italic* | `*text*` | `<em>` | ✅ Working | Emphasis |
| `Code` | `` `code` `` | `<code>` | ✅ Working | Inline |
| Links | `[text](url)` | `<a href>` | ✅ Working | External |
| Lists | `- item` | `<ul><li>` | ✅ Working | Nested OK |
| Tables | `| col |` | `<table>` | ✅ Working | This one! |
| Quotes | `> text` | `<blockquote>` | ✅ Working | Nested OK |
| Code Blocks | ``` | `<pre><code>` | ✅ Working | Syntax HL |

---

## Conclusion

This complex document tests:

1. **All major Markdown features**
2. *Nested and mixed formatting*
3. `Complex code examples`
4. [External references](https://example.com)
5. Unicode and special characters: 🎉

> **Final thought**: If this renders correctly, our Markdown processor is robust! 💪

**Total complexity score**: ⭐⭐⭐⭐⭐ (5/5 stars)
"""


# Pytest markers for different test categories
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require browser setup)"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests (may take longer)"
    )
    config.addinivalue_line(
        "markers", "memory: marks tests as memory usage tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker to performance tests
        if "performance" in item.nodeid or "perf" in item.name.lower():
            item.add_marker(pytest.mark.performance)
        
        # Add memory marker to memory tests
        if "memory" in item.name.lower():
            item.add_marker(pytest.mark.memory)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["batch", "concurrent", "large", "stress"]):
            item.add_marker(pytest.mark.slow)


@pytest.fixture
def mock_config():
    """Provide a mock configuration for testing."""
    config = Mock()
    config.slide_count = 5
    config.max_retries = 3
    config.retry_delay = 0.1
    config.output_dir = "/tmp/test_output"
    config.llm_provider = "gemini"
    config.api_key = "test-api-key"
    config.model = "test-model"
    return config


@pytest.fixture
def sample_slide():
    """Provide a sample slide for testing."""
    from presentation_generator.models.data import Slide
    
    return Slide(
        title="Sample Test Slide",
        content="# Sample Slide\n\nThis is **sample content** for testing purposes.",
        script="This is a sample narration script for testing the slide functionality."
    )


@pytest.fixture
def sample_presentation():
    """Provide a sample presentation for testing."""
    from presentation_generator.models.data import Slide, Presentation
    
    slides = [
        Slide(
            title=f"Slide {i}",
            content=f"# Slide {i}\n\nContent for slide {i}",
            script=f"Narration script for slide {i}",
            image_path=f"/path/to/slide_{i}.png",
            audio_path=f"/path/to/audio_{i}.wav",
            duration=5.0 + i
        )
        for i in range(1, 4)
    ]
    
    return Presentation(
        topic="Sample Test Presentation",
        slides=slides,
        metadata={"test": True}
    )


@pytest.fixture(autouse=True)
def cleanup_global_state():
    """Clean up global state between tests."""
    yield
    
    # Clean up any global caches or state
    try:
        from presentation_generator.providers.base import ProviderFactory
        ProviderFactory.clear_cache()
    except ImportError:
        pass


# Skip integration tests if browser dependencies are not available
def pytest_runtest_setup(item):
    """Setup for individual test runs."""
    if "integration" in item.keywords:
        try:
            import playwright
        except ImportError:
            pytest.skip("Playwright not available for integration tests")
    
    # Skip media tests if external dependencies are not available
    if "media" in item.keywords or "test_media" in item.nodeid:
        try:
            import playwright
            from google.cloud import texttospeech
            import ffmpeg
        except ImportError as e:
            pytest.skip(f"Media processing dependencies not available: {e}")