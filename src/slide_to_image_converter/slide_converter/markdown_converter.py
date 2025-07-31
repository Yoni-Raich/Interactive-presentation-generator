"""
Markdown to HTML converter.
"""

import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

import markdown2
from jinja2 import Environment, FileSystemLoader, Template

from .exceptions import MarkdownError


class MarkdownConverter:
    """Converts Markdown text to HTML using templates."""
    
    def __init__(self, template_path: Optional[Path] = None):
        """Initialize converter with optional template."""
        self.template_path = template_path
        self._template_cache: Dict[str, Template] = {}
        
        # Markdown processor with common extensions
        self.markdown_extras = [
            'fenced-code-blocks',
            'tables', 
            'strike',
            'task_list'
        ]
    
    def convert_to_html(self, markdown_text: str, slide_number: int = 1) -> str:
        """Convert Markdown text to HTML."""
        if not markdown_text or not markdown_text.strip():
            raise MarkdownError(
                "Markdown text cannot be empty",
                "Provide valid Markdown content"
            )
        
        if slide_number < 1:
            raise MarkdownError(
                "Slide number must be positive",
                "Use slide number >= 1"
            )
        
        try:
            # Convert Markdown to HTML
            html_content = markdown2.markdown(
                markdown_text, 
                extras=self.markdown_extras
            )
            
            # Apply template
            template = self._get_template()
            return template.render(
                content=html_content,
                slide_number=slide_number
            )
            
        except Exception as e:
            raise MarkdownError(f"Markdown conversion failed: {e}")
    
    def _get_template(self) -> Template:
        """Get template, using cache if available."""
        if self.template_path:
            cache_key = str(self.template_path)
            
            if cache_key not in self._template_cache:
                env = Environment(
                    loader=FileSystemLoader(self.template_path.parent),
                    autoescape=True
                )
                self._template_cache[cache_key] = env.get_template(
                    self.template_path.name
                )
            
            return self._template_cache[cache_key]
        
        # Use default template
        return self._get_default_template()
    
    def _get_default_template(self) -> Template:
        """Get default HTML template."""
        template_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide {{ slide_number }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            margin: 0;
        }
        .slide-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            width: 100%;
            max-width: 1200px;
            min-height: 700px;
            display: flex;
            flex-direction: column;
        }
        .slide-content {
            flex: 1;
            padding: 60px 80px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .slide-footer {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 20px 80px;
            color: white;
            border-radius: 0 0 20px 20px;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-bottom: 1rem;
        }
        p, li {
            color: #555;
            line-height: 1.6;
            margin-bottom: 1rem;
        }
        code {
            background: #f8f9fa;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
        }
        pre {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <div class="slide-container">
        <div class="slide-content">
            {{ content|safe }}
        </div>
        <div class="slide-footer">
            <span class="slide-number">Slide {{ slide_number }}</span>
        </div>
    </div>
</body>
</html>"""
        
        env = Environment(autoescape=True)
        return env.from_string(template_html)