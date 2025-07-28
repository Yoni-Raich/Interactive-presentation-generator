"""
JSON serialization and file handling for presentation data.

This module provides functionality to serialize presentation data to JSON format
and handle file I/O operations with proper error handling and validation.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile

from ..models.data_models import PresentationData, SlideData
from ..utils.logger import get_logger
from ..utils.exceptions import JSONSerializationError, FileOperationError

logger = get_logger(__name__)


class JSONSerializer:
    """
    Handles JSON serialization of presentation data and file operations.
    
    This class provides methods to convert PresentationData objects to JSON format,
    validate JSON structure, and save data to files with error handling and backup
    mechanisms.
    """
    
    def __init__(self, output_directory: str = "./output"):
        """
        Initialize the JSON serializer.
        
        Args:
            output_directory: Directory where JSON files will be saved
        """
        self.output_directory = Path(output_directory)
        self.backup_directory = Path(tempfile.gettempdir()) / "presentation_backups"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create output and backup directories if they don't exist."""
        try:
            self.output_directory.mkdir(parents=True, exist_ok=True)
            self.backup_directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directories exist: {self.output_directory}, {self.backup_directory}")
        except OSError as e:
            logger.error(f"Failed to create directories: {e}")
            raise FileOperationError(f"Cannot create required directories: {e}")
    
    def serialize_presentation(self, presentation: PresentationData) -> str:
        """
        Convert PresentationData to JSON string with proper structure.
        
        Args:
            presentation: The presentation data to serialize
            
        Returns:
            JSON string representation of the presentation
            
        Raises:
            SerializationError: If serialization fails
        """
        try:
            logger.info(f"Serializing presentation: {presentation.main_subject}")
            
            # Create the JSON structure according to design specification
            json_data = {
                "main_subject": presentation.main_subject,
                "created_at": presentation.created_at.isoformat(),
                "slides": [
                    {
                        "sub_subject": slide.sub_subject,
                        "slide_text": slide.slide_text,
                        "talking_script": slide.talking_script
                    }
                    for slide in presentation.slides
                ],
                "metadata": self._generate_metadata(presentation)
            }
            
            # Convert to JSON string with proper formatting
            json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
            
            # Validate the generated JSON
            if not self.validate_json_structure(json_string):
                raise JSONSerializationError("Generated JSON failed validation")
            
            logger.info(f"Successfully serialized presentation with {len(presentation.slides)} slides")
            return json_string
            
        except (TypeError, ValueError) as e:
            logger.error(f"JSON serialization failed: {e}")
            raise JSONSerializationError(f"Failed to serialize presentation data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during serialization: {e}")
            raise JSONSerializationError(f"Unexpected serialization error: {e}")
    
    def _generate_metadata(self, presentation: PresentationData) -> Dict[str, Any]:
        """
        Generate comprehensive metadata for the presentation.
        
        Args:
            presentation: The presentation data
            
        Returns:
            Dictionary containing metadata information
        """
        base_metadata = presentation.metadata.copy() if presentation.metadata else {}
        
        # Add generation-specific metadata
        generation_metadata = {
            "total_slides": len(presentation.slides),
            "generation_timestamp": datetime.now().isoformat(),
            "serializer_version": "1.0.0",
            "format_version": "1.0",
            "total_characters": sum(
                len(slide.slide_text) + len(slide.talking_script) 
                for slide in presentation.slides
            ),
            "average_slide_length": sum(len(slide.slide_text) for slide in presentation.slides) // len(presentation.slides) if presentation.slides else 0,
            "average_script_length": sum(len(slide.talking_script) for slide in presentation.slides) // len(presentation.slides) if presentation.slides else 0
        }
        
        # Merge metadata, with generation metadata taking precedence
        base_metadata.update(generation_metadata)
        return base_metadata
    
    def validate_json_structure(self, json_string: str) -> bool:
        """
        Validate that the JSON string has proper syntax and expected structure.
        
        Args:
            json_string: The JSON string to validate
            
        Returns:
            True if JSON is valid and has expected structure, False otherwise
        """
        try:
            # Parse JSON to check syntax
            data = json.loads(json_string)
            
            # Validate required top-level fields
            required_fields = ["main_subject", "created_at", "slides", "metadata"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate slides structure
            if not isinstance(data["slides"], list):
                logger.error("Slides field must be a list")
                return False
            
            # Validate each slide has required fields
            slide_required_fields = ["sub_subject", "slide_text", "talking_script"]
            for i, slide in enumerate(data["slides"]):
                if not isinstance(slide, dict):
                    logger.error(f"Slide {i} must be a dictionary")
                    return False
                
                for field in slide_required_fields:
                    if field not in slide:
                        logger.error(f"Slide {i} missing required field: {field}")
                        return False
                    
                    if not isinstance(slide[field], str) or not slide[field].strip():
                        logger.error(f"Slide {i} field '{field}' must be a non-empty string")
                        return False
            
            # Validate metadata structure
            if not isinstance(data["metadata"], dict):
                logger.error("Metadata field must be a dictionary")
                return False
            
            # Validate created_at is a valid ISO format
            try:
                datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
            except ValueError:
                logger.error("created_at field must be a valid ISO format datetime")
                return False
            
            logger.info("JSON structure validation passed")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON syntax: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during JSON validation: {e}")
            return False
    
    def save_to_file(self, json_data: str, filename: Optional[str] = None) -> str:
        """
        Save JSON data to file with error handling and backup mechanisms.
        
        Args:
            json_data: The JSON string to save
            filename: Optional custom filename. If not provided, generates one based on timestamp
            
        Returns:
            Path to the saved file
            
        Raises:
            FileOperationError: If file operations fail
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"presentation_{timestamp}.json"
        
        # Ensure filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        primary_path = self.output_directory / filename
        backup_path = self.backup_directory / filename
        
        try:
            # Validate file permissions and disk space
            self._validate_file_operations(primary_path)
            
            # Save to primary location
            logger.info(f"Saving presentation to: {primary_path}")
            with open(primary_path, 'w', encoding='utf-8') as f:
                f.write(json_data)
            
            # Verify the file was written correctly
            if not self._verify_file_integrity(primary_path, json_data):
                raise FileOperationError("File integrity check failed")
            
            # Create backup copy
            try:
                shutil.copy2(primary_path, backup_path)
                logger.info(f"Backup created at: {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
                # Don't fail the operation if backup fails
            
            logger.info(f"Successfully saved presentation to {primary_path}")
            return str(primary_path)
            
        except FileOperationError:
            raise
        except Exception as e:
            logger.error(f"Failed to save to primary location: {e}")
            
            # Try backup location
            try:
                logger.info(f"Attempting to save to backup location: {backup_path}")
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                
                if not self._verify_file_integrity(backup_path, json_data):
                    raise FileOperationError("Backup file integrity check failed")
                
                logger.warning(f"Saved to backup location: {backup_path}")
                return str(backup_path)
                
            except Exception as backup_error:
                logger.error(f"Failed to save to backup location: {backup_error}")
                raise FileOperationError(
                    f"Failed to save to both primary ({e}) and backup ({backup_error}) locations"
                )
    
    def _validate_file_operations(self, file_path: Path) -> None:
        """
        Validate that file operations can be performed.
        
        Args:
            file_path: Path where file will be saved
            
        Raises:
            FileOperationError: If validation fails
        """
        try:
            # Check if directory is writable
            if not os.access(file_path.parent, os.W_OK):
                raise FileOperationError(f"Directory not writable: {file_path.parent}")
            
            # Check available disk space (require at least 10MB)
            stat = shutil.disk_usage(file_path.parent)
            available_mb = stat[2] / (1024 * 1024)  # stat[2] is free space
            if available_mb < 10:
                raise FileOperationError(f"Insufficient disk space: {available_mb:.1f}MB available")
            
            # Check if file exists and is writable
            if file_path.exists() and not os.access(file_path, os.W_OK):
                raise FileOperationError(f"File exists but is not writable: {file_path}")
            
            logger.debug(f"File operation validation passed for: {file_path}")
            
        except FileOperationError:
            raise
        except Exception as e:
            raise FileOperationError(f"File validation error: {e}")
    
    def _verify_file_integrity(self, file_path: Path, expected_content: str) -> bool:
        """
        Verify that the file was written correctly by reading it back.
        
        Args:
            file_path: Path to the file to verify
            expected_content: The content that should be in the file
            
        Returns:
            True if file content matches expected content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                actual_content = f.read()
            
            if actual_content == expected_content:
                logger.debug(f"File integrity verified: {file_path}")
                return True
            else:
                logger.error(f"File integrity check failed: content mismatch in {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"File integrity verification failed: {e}")
            return False