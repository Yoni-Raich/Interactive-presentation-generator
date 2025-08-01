#!/usr/bin/env python3
"""
Simple example of creating video from JSON presentation
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.video_generator import create_video_from_json

def main():
    # Example JSON file path
    json_file = "output/example_presentation_with_audio.json"
    
    # Check if file exists
    if not os.path.exists(json_file):
        print(f"JSON file not found: {json_file}")
        return
    
    try:
        print(f"Creating video from: {json_file}")
        
        # Create video
        video_path = create_video_from_json(json_file)
        
        if video_path and os.path.exists(video_path):
            print(f"Video created successfully: {video_path}")
        else:
            print("Failed to create video")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()