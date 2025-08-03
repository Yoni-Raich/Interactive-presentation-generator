"""
Prompts for slide-specific generation tasks.
"""

class SlidePrompts:
    """Centralized prompts for slide generation operations."""
    
    @staticmethod
    def slide_validation_prompt(content: str, topic: str) -> str:
        """Generate prompt for validating slide content quality."""
        return f"""Evaluate the quality of this slide content for the topic "{topic}":

Content: {content}

Check for:
- Clarity and relevance to the topic
- Appropriate length for a slide
- Visual-friendly formatting
- Engaging presentation
- Completeness of key points

Respond with "VALID" if acceptable, or "INVALID: [reason]" if not."""

    @staticmethod
    def script_validation_prompt(script: str, content: str, topic: str) -> str:
        """Generate prompt for validating script quality."""
        return f"""Evaluate the quality of this narration script:

Topic: {topic}
Slide Content: {content}
Script: {script}

Check for:
- Consistency with slide content
- Appropriate length for narration
- Natural speaking flow
- Engaging tone
- Proper expansion of slide points

Respond with "VALID" if acceptable, or "INVALID: [reason]" if not."""

    @staticmethod
    def content_enhancement_prompt(content: str, topic: str, feedback: str) -> str:
        """Generate prompt for enhancing slide content based on feedback."""
        return f"""Improve this slide content based on the feedback provided:

Original Content: {content}
Topic: {topic}
Feedback: {feedback}

Requirements:
- Address the specific feedback points
- Maintain slide-appropriate formatting
- Keep content concise and visual-friendly
- Ensure relevance to the topic

Generate the improved slide content."""

    @staticmethod
    def script_enhancement_prompt(script: str, content: str, topic: str, feedback: str) -> str:
        """Generate prompt for enhancing script based on feedback."""
        return f"""Improve this narration script based on the feedback provided:

Original Script: {script}
Slide Content: {content}
Topic: {topic}
Feedback: {feedback}

Requirements:
- Address the specific feedback points
- Maintain natural speaking flow
- Ensure consistency with slide content
- Keep engaging and conversational tone

Generate the improved narration script."""

    @staticmethod
    def topic_refinement_prompt(topics: list, main_topic: str, feedback: str) -> str:
        """Generate prompt for refining slide topics based on feedback."""
        topics_text = "\n".join([f"{i+1}. {topic}" for i, topic in enumerate(topics)])
        
        return f"""Refine these slide topics for a presentation about "{main_topic}":

Current Topics:
{topics_text}

Feedback: {feedback}

Requirements:
- Address the specific feedback
- Maintain logical flow
- Ensure comprehensive coverage of {main_topic}
- Keep topics clear and specific
- Suitable for individual slides

Generate the refined topic list as a numbered list."""