"""
Backward compatibility module.

This module provides backward compatibility by importing from the new unified client.
"""

# Import everything from the new unified client
from .llm_client import LLMClient, UnifiedLLMClient, LangChainGeminiClient

# Re-export for backward compatibility
__all__ = ['LLMClient', 'UnifiedLLMClient', 'LangChainGeminiClient']


