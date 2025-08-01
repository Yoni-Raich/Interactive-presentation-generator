#!/usr/bin/env python3
"""
Simple Example Script - Complete Presentation Workflow

This script demonstrates the full workflow:
1. Define a subject
2. Generate slides and JSON
3. Create images for each slide
4. Generate audio for each slide
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.content_generator import ContentGenerator
from src.core.json_serializer import JSONSerializer
from src.integrations.langchain_integration import LLMClient
from src.integrations.tts_client import TTSClient
from src.slide_to_image_converter import SlideProcessor, Config as SlideConfig
from src.utils.config import load_config
from src.video_generator import create_video_from_json


def main():
    """Main workflow demonstration."""
    print("🚀 Starting Complete Presentation Workflow Example")
    
    # Step 1: Define subject
    subject = """
    Advanced Python: Mastering Modern Libraries and Performance
    This course delves into advanced Python features, sophisticated library usage, and performance optimization techniques. We will explore concurrency, metaclasses, and advanced data structures to build efficient and scalable applications.
    """
    print(f"📝 Subject: {subject}")
    
    # Step 2: Load configuration and generate presentation
    print("\n🔧 Loading configuration...")
    config = load_config()
    
    print("🤖 Initializing AI components...")
    llm_client = LLMClient(config)
    content_generator = ContentGenerator(llm_client, config)
    
    print("🎯 Generating presentation...")
    presentation = content_generator.generate_presentation(subject)
    print(f"✅ Generated {presentation.total_slides} slides")
    
    # Step 3: Save JSON
    print("\n💾 Saving presentation JSON...")
    json_serializer = JSONSerializer(config.output_directory)
    json_data = json_serializer.serialize_presentation(presentation)
    json_file = json_serializer.save_to_file(json_data, "example_presentation.json")
    print(f"✅ JSON saved to: {json_file}")
    
    # Step 4: Generate slide images
    print("\n🖼️  Generating slide images...")
    slide_config = SlideConfig(
        width=1920,
        height=1080,
        browser="chromium"
    )
    slide_processor = SlideProcessor(slide_config)
    
    # Create images directory
    images_dir = Path(config.output_directory) / "images"
    images_dir.mkdir(exist_ok=True)
    
    # Process slides and add image paths to JSON
    image_results = slide_processor.process_presentation_with_update(
        json_file, 
        images_dir,
        save_updated_json=True
    )
    print(f"✅ Generated {image_results['successful']} slide images")
    
    # Step 5: Generate audio
    print("\n🎵 Generating audio files...")
    tts_client = TTSClient()
    
    # Process the updated JSON file to add audio
    updated_json_file = tts_client.process_presentation_json(json_file)
    print(f"✅ Audio generation completed")
    print(f"📁 Final presentation with images and audio: {updated_json_file}")
    
    create_video_from_json(json_file_path=updated_json_file)
    # Step 6: Show summary
    print("\n📋 Workflow Summary:")
    print(f"   Subject: {subject}")
    print(f"   Total Slides: {presentation.total_slides}")
    print(f"   Images Generated: {image_results['successful']}")
    print(f"   JSON File: {updated_json_file}")
    print(f"   Images Directory: {images_dir}")
    
    print("\n🎉 Complete workflow finished successfully!")
    print(f"📂 Check the output directory: {config.output_directory}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
