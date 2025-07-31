"""
Configuration for slide converter.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Configuration for slide converter."""
    
    # Image settings
    width: int = 1920
    height: int = 1080
    
    # Browser settings
    browser: str = "chromium"
    timeout: int = 30000
    
    # Template settings
    template_path: Optional[Path] = None
    
    def __post_init__(self):
        """Validate configuration."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Width and height must be positive")
        
        if self.browser not in ["chromium", "firefox", "webkit"]:
            raise ValueError("Browser must be chromium, firefox, or webkit")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        if self.template_path and not Path(self.template_path).exists():
            raise ValueError(f"Template file not found: {self.template_path}")