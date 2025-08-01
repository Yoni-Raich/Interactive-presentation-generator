#!/usr/bin/env python3
"""
Debug video generation issues
"""

import os
import json
import sys

def debug_json_paths():
    """Debug the paths in JSON file"""
    
    json_file = "output/example_presentation_with_audio.json"
    
    if not os.path.exists(json_file):
        print(f"JSON file not found: {json_file}")
        return
    
    # Read JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"JSON file: {json_file}")
    print(f"Base directory: {os.path.dirname(json_file)}")
    print(f"Number of slides: {len(data.get('slides', []))}")
    print()
    
    base_dir = os.path.dirname(json_file)
    
    for i, slide in enumerate(data.get('slides', [])):
        print(f"=== Slide {i+1}: {slide.get('sub_subject', 'No title')} ===")
        
        # Check image path
        image_path = slide.get('image_path') or slide.get('slide_image_path')
        audio_path = slide.get('audio_path')
        
        print(f"Image path in JSON: {image_path}")
        print(f"Audio path in JSON: {audio_path}")
        
        if image_path:
            # Apply same fix as video generator
            if image_path.startswith("output\\") or image_path.startswith("output/"):
                image_path = image_path[7:]
            full_image_path = os.path.join(base_dir, image_path)
            print(f"Full image path: {full_image_path}")
            print(f"Image exists: {os.path.exists(full_image_path)}")
        else:
            print("No image path found")
        
        if audio_path:
            # Apply same fix as video generator
            if audio_path.startswith("output\\") or audio_path.startswith("output/"):
                audio_path = audio_path[7:]
            full_audio_path = os.path.join(base_dir, audio_path)
            print(f"Full audio path: {full_audio_path}")
            print(f"Audio exists: {os.path.exists(full_audio_path)}")
        else:
            print("No audio path found")
        
        print()

if __name__ == "__main__":
    debug_json_paths()