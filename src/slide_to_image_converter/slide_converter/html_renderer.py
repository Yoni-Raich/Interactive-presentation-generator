"""
HTML to PNG renderer using Playwright.
"""

import asyncio
from pathlib import Path
from typing import Union

from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright

from .exceptions import RenderError


class HTMLRenderer:
    """Renders HTML content to PNG images using Playwright."""
    
    def __init__(self, width: int = 1920, height: int = 1080, 
                 browser: str = "chromium", timeout: int = 30000):
        """Initialize renderer with dimensions and browser settings."""
        self.width = width
        self.height = height
        self.browser = browser
        self.timeout = timeout
        
        if browser not in ["chromium", "firefox", "webkit"]:
            raise RenderError(
                f"Unsupported browser: {browser}",
                "Use chromium, firefox, or webkit"
            )
    
    def render_to_png(self, html_content: str, 
                     output_path: Union[str, Path]) -> None:
        """Render HTML content to PNG file synchronously."""
        if not html_content or not html_content.strip():
            raise RenderError(
                "HTML content cannot be empty",
                "Provide valid HTML content"
            )
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with sync_playwright() as p:
                browser = getattr(p, self.browser).launch(headless=True)
                page = browser.new_page()
                
                page.set_viewport_size({
                    "width": self.width, 
                    "height": self.height
                })
                
                page.set_content(
                    html_content, 
                    wait_until="networkidle",
                    timeout=self.timeout
                )
                
                page.screenshot(
                    path=str(output_path),
                    full_page=True,
                    type="png"
                )
                
                browser.close()
                
        except Exception as e:
            raise RenderError(f"HTML rendering failed: {e}")
    
    async def render_to_png_async(self, html_content: str,
                                 output_path: Union[str, Path]) -> None:
        """Render HTML content to PNG file asynchronously."""
        if not html_content or not html_content.strip():
            raise RenderError(
                "HTML content cannot be empty",
                "Provide valid HTML content"
            )
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with async_playwright() as p:
                browser = await getattr(p, self.browser).launch(headless=True)
                page = await browser.new_page()
                
                await page.set_viewport_size({
                    "width": self.width,
                    "height": self.height
                })
                
                await page.set_content(
                    html_content,
                    wait_until="networkidle", 
                    timeout=self.timeout
                )
                
                await page.screenshot(
                    path=str(output_path),
                    full_page=True,
                    type="png"
                )
                
                await browser.close()
                
        except Exception as e:
            raise RenderError(f"HTML rendering failed: {e}")