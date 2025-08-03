"""
Provider-specific prompts and system messages.
"""

class ProviderPrompts:
    """Centralized prompts for LLM provider operations."""
    
    @staticmethod
    def connection_test_prompt() -> str:
        """Simple prompt for testing provider connection."""
        return "Respond with exactly: 'Connection successful'"
    
    @staticmethod
    def system_prompt_presentation_generation() -> str:
        """System prompt for presentation generation tasks."""
        return """You are an expert presentation creator and content generator. Your role is to help create engaging, informative, and well-structured presentations.

Key principles:
- Create clear, concise, and engaging content
- Ensure logical flow between topics
- Use appropriate language for the target audience
- Focus on key points and avoid unnecessary details
- Maintain consistency in tone and style
- Generate content suitable for visual presentation

Always follow the specific requirements provided in each request."""

    @staticmethod
    def system_prompt_content_validation() -> str:
        """System prompt for content validation tasks."""
        return """You are a content quality evaluator for presentations. Your role is to assess the quality, clarity, and appropriateness of presentation content.

Evaluation criteria:
- Clarity and coherence
- Relevance to the topic
- Appropriate length and detail level
- Engaging and informative content
- Proper structure and formatting
- Consistency with requirements

Provide clear, constructive feedback when content needs improvement."""

    @staticmethod
    def error_recovery_prompt(original_prompt: str, error_context: str) -> str:
        """Generate a simplified prompt for error recovery."""
        return f"""The previous request encountered an issue. Please provide a simplified response to this request:

Original Request: {original_prompt}

Context: {error_context}

Please provide a basic, straightforward response that addresses the core requirement."""