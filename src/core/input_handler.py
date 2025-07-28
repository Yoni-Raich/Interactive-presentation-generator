"""
Input handler module for presentation generator.

This module provides input validation and sanitization functionality
to ensure safe and valid user input processing.
"""

import re
import html
from typing import Optional
from src.utils.exceptions import InputValidationError


class InputHandler:
    """Handles input validation and sanitization for presentation subjects."""
    
    # Maximum allowed length for subject input
    MAX_SUBJECT_LENGTH = 500
    
    # Minimum allowed length for subject input
    MIN_SUBJECT_LENGTH = 3
    
    # Patterns for potentially malicious input
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',               # JavaScript protocol
        r'on\w+\s*=',                # Event handlers
        r'<iframe[^>]*>.*?</iframe>', # Iframe tags
        r'<object[^>]*>.*?</object>', # Object tags
        r'<embed[^>]*>',             # Embed tags (self-closing)
        r'<link[^>]*>',              # Link tags (self-closing)
        r'<meta[^>]*>',              # Meta tags (self-closing)
        r'<style[^>]*>.*?</style>',  # Style tags
    ]
    
    def validate_subject(self, subject: str) -> bool:
        """
        Validate that the subject input meets basic requirements.
        
        Args:
            subject: The subject string to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails with specific error details
        """
        if not isinstance(subject, str):
            raise InputValidationError("Subject must be a string", subject)
        
        # Check for empty or whitespace-only input
        if not subject or not subject.strip():
            raise InputValidationError("Subject cannot be empty", subject)
        
        # Check minimum length
        if len(subject.strip()) < self.MIN_SUBJECT_LENGTH:
            raise InputValidationError(
                f"Subject must be at least {self.MIN_SUBJECT_LENGTH} characters long",
                subject
            )
        
        # Check maximum length
        if len(subject) > self.MAX_SUBJECT_LENGTH:
            raise InputValidationError(
                f"Subject cannot exceed {self.MAX_SUBJECT_LENGTH} characters",
                subject
            )
        
        # Check for potentially malicious patterns
        subject_lower = subject.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, subject_lower, re.IGNORECASE | re.DOTALL):
                raise InputValidationError("Subject contains potentially unsafe content", subject)
        
        # Check for excessive special characters (potential injection attempt)
        special_char_count = len(re.findall(r'[<>{}[\]\\|`~!@#$%^&*()+=]', subject))
        if special_char_count > len(subject) * 0.3:  # More than 30% special chars
            raise InputValidationError("Subject contains too many special characters", subject)
        
        return True 
   
    def sanitize_input(self, subject: str) -> str:
        """
        Sanitize input to prevent injection attacks while preserving valid content.
        
        Args:
            subject: The subject string to sanitize
            
        Returns:
            str: Sanitized subject string
        """
        if not isinstance(subject, str):
            return ""
        
        # Remove leading/trailing whitespace
        sanitized = subject.strip()
        
        # Remove or replace dangerous patterns BEFORE HTML escaping
        for pattern in self.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # HTML escape to prevent XSS
        sanitized = html.escape(sanitized)
        
        # Remove null bytes and control characters (except newlines and tabs)
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        # Normalize whitespace (replace multiple spaces with single space)
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Remove excessive punctuation repetition
        sanitized = re.sub(r'([.!?]){3,}', r'\1\1', sanitized)
        
        return sanitized.strip()
    
    def process_subject(self, subject: str) -> str:
        """
        Process subject input by sanitizing and validating it.
        
        Args:
            subject: Raw subject input from user
            
        Returns:
            str: Processed and validated subject
            
        Raises:
            ValidationError: If the processed subject fails validation
        """
        # First sanitize the input
        sanitized_subject = self.sanitize_input(subject)
        
        # Then validate the sanitized input
        if self.validate_subject(sanitized_subject):
            return sanitized_subject
        
        # This should not be reached due to validation raising exceptions
        raise InputValidationError("Subject processing failed", subject)