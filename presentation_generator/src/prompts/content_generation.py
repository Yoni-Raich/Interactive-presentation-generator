"""
Prompts for content generation and slide topic creation.
"""

class ContentPrompts:
    """Centralized prompts for content generation operations."""
    
    @staticmethod
    def slide_topics_generation(main_topic: str, target_count: int, min_slides: int, max_slides: int) -> str:
        """Generate prompt for creating slide topics."""
        return f"""Generate {target_count} slide topics for a presentation about "{main_topic}".

Requirements:
- Create {min_slides}-{max_slides} distinct topics
- Each topic should be clear and specific (2-8 words)
- Topics should flow logically for a presentation
- Cover the most important aspects of {main_topic}
- Ensure topics are suitable for individual slides

Format as a numbered list, one topic per line.
DO-NOT write extra text
"""

    @staticmethod
    def slide_content_generation(topic: str, main_topic: str, slide_number: int, total_slides: int) -> str:
        """Generate prompt for creating slide content."""
        return f"""Create slide content for: "{topic}"

Context:
- Part of presentation about "{main_topic}"
- Slide {slide_number} of {total_slides}

Requirements:
- Keep content concise and visual-friendly
- Use bullet points or short paragraphs
- Focus on key points for this specific topic
- Make it engaging and informative
- Suitable for display on a slide

Generate only the slide content."""

    @staticmethod
    def slide_script_generation(
        topic: str, 
        content: str, 
        main_topic: str, 
        slide_number: int, 
        total_slides: int, 
        previous_topic: str = None
    ) -> str:
        """Generate prompt for creating slide narration script."""
        
        # Determine context for transitions
        if slide_number == 1:
            position_context = "This is the opening slide of the presentation."
        elif slide_number == total_slides:
            position_context = "This is the concluding slide of the presentation."
        else:
            position_context = f"This is slide {slide_number} of {total_slides}."
        
        previous_context = f"- Previous topic: {previous_topic}" if previous_topic else ""
        
        return f"""Create a narration script for this slide:

Topic: {topic}
Slide Content: {content}

Context:
- Main presentation topic: {main_topic}
- {position_context}
{previous_context}

Requirements:
- Conversational and engaging tone
- Expand on the slide content naturally
- Include smooth transitions where appropriate
- Natural speaking rhythm
- Minimum 100 words for adequate narration

Generate only the narration script."""

    @staticmethod
    def fallback_content_template(topic: str, main_topic: str) -> str:
        """Generate fallback content when AI generation fails."""
        return f"""• {topic}
• Key aspects and concepts
• Important principles
• Practical applications
• Relevance to {main_topic}"""

    @staticmethod
    def fallback_script_template(
        topic: str, 
        main_topic: str, 
        slide_number: int, 
        total_slides: int
    ) -> str:
        """Generate fallback script when AI generation fails."""
        
        if slide_number == 1:
            position_text = "Let's begin by exploring "
        elif slide_number == total_slides:
            position_text = "To conclude, let's examine "
        else:
            position_text = "Next, let's discuss "
        
        return f"""{position_text}{topic}. This is an important aspect of {main_topic} that we need to understand.

When we consider {topic}, we should focus on the key concepts and principles that make it significant. This topic encompasses several important elements that contribute to our overall understanding of {main_topic}.

The practical applications and real-world relevance of {topic} help us appreciate its importance in the broader context of our discussion. Understanding these aspects will enhance our comprehension of {main_topic} and its implications."""