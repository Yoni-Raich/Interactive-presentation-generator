"""
Main slide processor orchestrating the conversion pipeline.
"""

import json
import re
from pathlib import Path
from typing import Union, Dict, Any, List

from .config import Config
from .markdown_converter import MarkdownConverter
from .html_renderer import HTMLRenderer
from .exceptions import SlideConverterError, ValidationError


class SlideProcessor:
    """Main processor for converting slides from Markdown to PNG."""
    
    def __init__(self, config: Config = None, **kwargs):
        """Initialize processor with configuration."""
        if config is None:
            config = Config(**kwargs)
        
        self.config = config
        self.markdown_converter = MarkdownConverter(config.template_path)
        self.html_renderer = HTMLRenderer(
            width=config.width,
            height=config.height,
            browser=config.browser,
            timeout=config.timeout
        )
    
    def process_single_slide(self, markdown_text: str, 
                           output_path: Union[str, Path],
                           slide_number: int = 1) -> None:
        """Process a single slide from Markdown to PNG."""
        try:
            # Convert Markdown to HTML
            html_content = self.markdown_converter.convert_to_html(
                markdown_text, slide_number
            )
            
            # Render HTML to PNG
            self.html_renderer.render_to_png(html_content, output_path)
            
        except Exception as e:
            raise SlideConverterError(f"Slide processing failed: {e}")
    
    def process_presentation(self, json_path: Union[str, Path],
                           output_dir: Union[str, Path]) -> Dict[str, Any]:
        """Process a presentation from JSON file and add image paths to slides."""
        json_path = Path(json_path)
        output_dir = Path(output_dir)
        
        if not json_path.exists():
            raise ValidationError(
                f"JSON file not found: {json_path}",
                "Check the file path"
            )
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Load and validate JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            slides = self._extract_slides(data)
            
            # Find the slides array in the original data structure
            slide_list_ref = None
            if 'slides' in data:
                slide_list_ref = data['slides']
            elif 'sub_subjects' in data:
                slide_list_ref = data['sub_subjects']
            elif 'presentation' in data and 'slides' in data['presentation']:
                slide_list_ref = data['presentation']['slides']
            
            # Process each slide
            results = {
                'total_slides': len(slides),
                'successful': 0,
                'failed': 0,
                'generated_files': [],
                'updated_presentation': data  # Include the updated JSON data
            }
            
            for i, slide_info in enumerate(slides, 1):
                try:
                    output_filename = self._generate_filename(
                        i, slide_info['subject']
                    )
                    output_path = output_dir / output_filename
                    
                    self.process_single_slide(
                        slide_info['text'], output_path, i
                    )
                    
                    # Add image path to the original slide object
                    if slide_list_ref and i <= len(slide_list_ref):
                        slide_list_ref[i-1]['slide_image_path'] = str(output_path)
                    
                    results['generated_files'].append(str(output_path))
                    results['successful'] += 1
                    
                except Exception as e:
                    print(f"Failed to process slide {i}: {e}")
                    results['failed'] += 1
            
            return results
            
        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Invalid JSON format: {e}",
                "Check JSON syntax"
            )
        except Exception as e:
            raise SlideConverterError(f"Presentation processing failed: {e}")
    
    def _extract_slides(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract slide information from JSON data."""
        slides = []
        
        # Try different JSON structures
        slide_list = None
        if 'slides' in data:
            slide_list = data['slides']
        elif 'sub_subjects' in data:
            slide_list = data['sub_subjects']
        elif 'presentation' in data and 'slides' in data['presentation']:
            slide_list = data['presentation']['slides']
        
        if not slide_list:
            raise ValidationError(
                "No slides found in JSON",
                "Ensure JSON contains 'slides' or 'sub_subjects' array"
            )
        
        for slide in slide_list:
            if not isinstance(slide, dict):
                raise ValidationError(
                    "Each slide must be an object",
                    "Check slide structure"
                )
            
            slide_text = slide.get('slide_text')
            if not slide_text:
                raise ValidationError(
                    "Missing 'slide_text' field",
                    "Each slide must have 'slide_text' field"
                )
            
            subject = slide.get('sub_subject', slide.get('title', 'slide'))
            
            slides.append({
                'text': slide_text,
                'subject': subject
            })
        
        return slides
    
    def _generate_filename(self, slide_number: int, subject: str) -> str:
        """Generate safe filename for slide."""
        # Clean subject for filename
        clean_subject = re.sub(r'[<>:"/\\|?*]', '_', subject)
        clean_subject = re.sub(r'\s+', '_', clean_subject)
        clean_subject = re.sub(r'_+', '_', clean_subject).strip('_')
        
        if not clean_subject:
            clean_subject = 'slide'
        
        # Limit length
        if len(clean_subject) > 50:
            clean_subject = clean_subject[:50].rstrip('_')
        
        return f"slide_{slide_number:02d}_{clean_subject.lower()}.png"
    
    def process_presentation_with_update(self, json_path: Union[str, Path],
                                       output_dir: Union[str, Path],
                                       save_updated_json: bool = True) -> Dict[str, Any]:
        """Process presentation and optionally save updated JSON with image paths."""
        results = self.process_presentation(json_path, output_dir)
        
        if save_updated_json and 'updated_presentation' in results:
            # Save the updated JSON back to the original file
            json_path = Path(json_path)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results['updated_presentation'], f, 
                         indent=2, ensure_ascii=False)
            
            print(f"Updated JSON saved to: {json_path}")
        
        return results