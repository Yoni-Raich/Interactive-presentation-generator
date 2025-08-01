"""
Image processing component for slide-to-image conversion.

Consolidates slide-to-image conversion functionality from the existing
slide_to_image_converter module into a clean, library-focused component.
"""

import re
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any

import markdown2
from jinja2 import Environment, Template
from playwright.sync_api import sync_playwright

from ..models.data import Slide
from ..utils.exceptions import MediaProcessingError
from ..utils.config import Config


class ImageProcessor:
    """
    Processes slide content to generate PNG images.
    
    Consolidates functionality from the slide_to_image_converter module
    and integrates with the new Slide data model.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the image processor.
        
        Args:
            config: Configuration object with image settings
        """
        self.config = config
        self.width = config.image_width
        self.height = config.image_height
        
        # Markdown processor with common extensions
        self.markdown_extras = [
            'fenced-code-blocks',
            'tables', 
            'strike',
            'task_list'
        ]
    
    def generate_image(self, slide: Slide, output_path: str) -> None:
        """
        Generate image for a single slide.
        
        Args:
            slide: Slide object to generate image for
            output_path: Full path where to save the image
            
        Raises:
            MediaProcessingError: If image generation fails
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                
                # Convert slide content to HTML
                html_content = self._convert_to_html(slide.content, 1)
                
                # Render HTML to PNG
                self._render_to_png(browser, html_content, output_path)
                
                browser.close()
                
        except Exception as e:
            raise MediaProcessingError(f"Image generation failed: {e}")
    
    def process_slides(self, slides: List[Slide], output_dir: Path) -> None:
        """
        Process all slides to generate images and populate image_path.
        
        Args:
            slides: List of slides to process
            output_dir: Directory to save generated images
            
        Raises:
            MediaProcessingError: If image generation fails
        """
        output_dir = Path(output_dir)
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                
                for i, slide in enumerate(slides, 1):
                    try:
                        # Generate filename
                        filename = self._generate_filename(i, slide.title)
                        image_path = images_dir / filename
                        
                        # Convert slide content to HTML
                        html_content = self._convert_to_html(slide.content, i)
                        
                        # Render HTML to PNG
                        self._render_to_png(browser, html_content, image_path)
                        
                        # Update slide with image path (relative to output_dir)
                        slide.image_path = str(image_path.relative_to(output_dir))
                        
                    except Exception as e:
                        raise MediaProcessingError(
                            f"Failed to generate image for slide {i}: {e}"
                        )
                
                browser.close()
                
        except Exception as e:
            raise MediaProcessingError(f"Image processing failed: {e}")
    
    def _convert_to_html(self, content: str, slide_number: int) -> str:
        """
        Convert slide content to HTML using template.
        
        Args:
            content: Slide content (supports Markdown)
            slide_number: Slide number for display
            
        Returns:
            Complete HTML document
        """
        if not content or not content.strip():
            raise MediaProcessingError("Slide content cannot be empty")
        
        try:
            # Convert Markdown to HTML if needed
            if self._is_markdown(content):
                html_content = markdown2.markdown(content, extras=self.markdown_extras)
            else:
                html_content = content
            
            # Apply template
            template = self._get_template()
            return template.render(
                content=html_content,
                slide_number=slide_number
            )
            
        except Exception as e:
            raise MediaProcessingError(f"HTML conversion failed: {e}")
    
    def _render_to_png(self, browser, html_content: str, output_path: Path) -> None:
        """
        Render HTML content to PNG using Playwright.
        
        Args:
            browser: Playwright browser instance
            html_content: Complete HTML document
            output_path: Path to save the PNG file
        """
        try:
            page = browser.new_page()
            
            page.set_viewport_size({
                "width": self.width,
                "height": self.height
            })
            
            page.set_content(
                html_content,
                wait_until="networkidle",
                timeout=30000
            )
            
            page.screenshot(
                path=str(output_path),
                full_page=True,
                type="png"
            )
            
            page.close()
            
        except Exception as e:
            raise MediaProcessingError(f"PNG rendering failed: {e}")
    
    def _generate_filename(self, slide_number: int, title: str) -> str:
        """
        Generate safe filename for slide image.
        
        Args:
            slide_number: Slide number
            title: Slide title
            
        Returns:
            Safe filename with .png extension
        """
        # Clean title for filename
        clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        clean_title = re.sub(r'\s+', '_', clean_title)
        clean_title = re.sub(r'_+', '_', clean_title).strip('_')
        
        if not clean_title:
            clean_title = 'slide'
        
        # Limit length
        if len(clean_title) > 50:
            clean_title = clean_title[:50].rstrip('_')
        
        return f"slide_{slide_number:02d}_{clean_title.lower()}.png"
    
    def _is_markdown(self, content: str) -> bool:
        """
        Check if content appears to be Markdown.
        
        Args:
            content: Content to check
            
        Returns:
            True if content appears to be Markdown
        """
        markdown_indicators = [
            r'^#{1,6}\s',  # Headers
            r'^\*\s',      # Bullet points
            r'^\d+\.\s',   # Numbered lists
            r'\*\*.*\*\*', # Bold text
            r'`.*`',       # Code
            r'^\|.*\|',    # Tables
        ]
        
        for pattern in markdown_indicators:
            if re.search(pattern, content, re.MULTILINE):
                return True
        
        return False
    
    def _get_template(self) -> Template:
        """
        Get HTML template for slide rendering.
        
        Returns:
            Jinja2 template for slide HTML
        """
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
            line-height: 1.2;
        }
        h1 { font-size: 2.5rem; }
        h2 { font-size: 2rem; }
        h3 { font-size: 1.5rem; }
        p, li {
            color: #555;
            line-height: 1.6;
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }
        ul, ol {
            padding-left: 2rem;
        }
        li {
            margin-bottom: 0.5rem;
        }
        code {
            background: #f8f9fa;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9rem;
        }
        pre {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
        }
        pre code {
            background: none;
            padding: 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        blockquote {
            border-left: 4px solid #667eea;
            padding-left: 1rem;
            margin: 1rem 0;
            font-style: italic;
            color: #666;
        }
        .slide-number {
            font-weight: bold;
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