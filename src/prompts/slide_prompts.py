"""
Prompt templates for slide content generation using LangChain and Gemini.

This module contains prompts designed to generate concise, presentation-appropriate
slide content from sub-subjects while maintaining context consistency.
"""

from typing import Dict, Any, List


class SlidePrompts:
    """Collection of prompt templates for slide content generation."""
    
    BASE_SYSTEM_PROMPT = """You are an expert presentation designer specializing in creating clear, engaging slide content. Your task is to generate concise, impactful slide text that effectively communicates key information to an audience.

Key requirements:
- Create slide text that is concise and presentation-appropriate
- Use bullet points, short phrases, and key concepts
- Avoid long paragraphs or dense text blocks
- Focus on the most important information for the sub-subject
- Ensure content is visually scannable and easy to read
- Maintain professional tone appropriate for presentations
- Keep slide text under 150 words total

Format your response as clean slide content without additional explanation or formatting instructions."""

    SLIDE_GENERATION_PROMPT = """Main Topic: "{main_subject}"
Sub-subject: "{sub_subject}"
Context: This slide is part of a presentation about "{main_subject}"

Generate slide content for the sub-subject "{sub_subject}" that:
- Clearly explains the key concepts related to this sub-subject
- Uses bullet points or short phrases for readability
- Highlights the most important information
- Connects logically to the main topic
- Is appropriate for a presentation slide format
- Engages the audience with clear, impactful content

Create slide content that would effectively communicate this sub-subject to an audience."""

    CONTEXTUAL_SLIDE_PROMPT = """Main Topic: "{main_subject}"
Sub-subject: "{sub_subject}"
Previous Sub-subjects: {previous_subjects}
Presentation Flow: This is slide {slide_number} of approximately {total_slides} slides

Generate slide content for "{sub_subject}" considering:
- How this sub-subject builds on previous topics covered
- The logical progression of the overall presentation
- Key points that need emphasis for this specific sub-subject
- Appropriate level of detail for slide format
- Connection to the main topic and presentation flow

Create concise, engaging slide content using bullet points and key phrases."""

    DETAILED_SLIDE_PROMPT = """Main Topic: "{main_subject}"
Sub-subject: "{sub_subject}"
Target Audience: {audience}
Presentation Purpose: {purpose}

Create slide content for "{sub_subject}" that:
- Is tailored to the specified audience level and interests
- Serves the overall presentation purpose
- Presents information in a clear, logical structure
- Uses appropriate terminology and examples
- Emphasizes the most relevant points for this audience
- Maintains engagement through clear, impactful content

Generate slide text using bullet points, key phrases, and structured content."""

    REVISION_PROMPT = """Main Topic: "{main_subject}"
Sub-subject: "{sub_subject}"
Current Slide Content: 
{current_content}

Issues to address: {issues}

Please revise the slide content to address the specified issues while maintaining:
- Clear, concise presentation format
- Relevance to the sub-subject and main topic
- Appropriate length and structure for slides
- Professional presentation tone
- Visual scannability and readability

Generate improved slide content that resolves the identified issues."""

    @classmethod
    def get_generation_prompt(cls, main_subject: str, sub_subject: str, 
                            slide_number: int = None, total_slides: int = None,
                            previous_subjects: List[str] = None) -> Dict[str, Any]:
        """
        Get the primary prompt for slide content generation.
        
        Args:
            main_subject: The main presentation topic
            sub_subject: The specific sub-subject for this slide
            slide_number: Position of this slide in the presentation
            total_slides: Total number of slides in presentation
            previous_subjects: List of previously covered sub-subjects
            
        Returns:
            Dictionary containing system and user prompts
        """
        if slide_number and total_slides and previous_subjects:
            prev_subjects_text = ", ".join(previous_subjects) if previous_subjects else "None"
            user_prompt = cls.CONTEXTUAL_SLIDE_PROMPT.format(
                main_subject=main_subject,
                sub_subject=sub_subject,
                previous_subjects=prev_subjects_text,
                slide_number=slide_number,
                total_slides=total_slides
            )
        else:
            user_prompt = cls.SLIDE_GENERATION_PROMPT.format(
                main_subject=main_subject,
                sub_subject=sub_subject
            )
        
        return {
            "system_prompt": cls.BASE_SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "temperature": 0.6,
            "max_tokens": 300
        }
    
    @classmethod
    def get_detailed_prompt(cls, main_subject: str, sub_subject: str,
                          audience: str = "general", purpose: str = "informational") -> Dict[str, Any]:
        """
        Get detailed prompt for audience-specific slide content.
        
        Args:
            main_subject: The main presentation topic
            sub_subject: The specific sub-subject for this slide
            audience: Target audience description
            purpose: Purpose of the presentation
            
        Returns:
            Dictionary containing system and user prompts
        """
        user_prompt = cls.DETAILED_SLIDE_PROMPT.format(
            main_subject=main_subject,
            sub_subject=sub_subject,
            audience=audience,
            purpose=purpose
        )
        
        return {
            "system_prompt": cls.BASE_SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "temperature": 0.6,
            "max_tokens": 300
        }
    
    @classmethod
    def get_revision_prompt(cls, main_subject: str, sub_subject: str,
                          current_content: str, issues: str) -> Dict[str, Any]:
        """
        Get prompt for revising existing slide content.
        
        Args:
            main_subject: The main presentation topic
            sub_subject: The specific sub-subject for this slide
            current_content: Current slide content to be revised
            issues: Description of issues to address
            
        Returns:
            Dictionary containing revision prompt
        """
        user_prompt = cls.REVISION_PROMPT.format(
            main_subject=main_subject,
            sub_subject=sub_subject,
            current_content=current_content,
            issues=issues
        )
        
        return {
            "system_prompt": cls.BASE_SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "temperature": 0.7,
            "max_tokens": 300
        }

    @classmethod
    def get_validation_prompt(cls, main_subject: str, sub_subject: str, 
                            slide_content: str) -> Dict[str, Any]:
        """
        Get prompt for validating generated slide content.
        
        Args:
            main_subject: The main presentation topic
            sub_subject: The specific sub-subject for this slide
            slide_content: Generated slide content to validate
            
        Returns:
            Dictionary containing validation prompt
        """
        validation_prompt = f"""Main Topic: "{main_subject}"
Sub-subject: "{sub_subject}"
Generated Slide Content:
{slide_content}

Please evaluate this slide content and respond with "VALID" if it meets all criteria, or "INVALID" followed by specific issues.

Evaluation criteria:
1. Is the content relevant to the sub-subject and main topic?
2. Is it appropriately concise for a presentation slide?
3. Is it well-structured and visually scannable?
4. Does it effectively communicate key information?
5. Is the tone professional and appropriate?
6. Is the length appropriate (under 150 words)?

Response format: "VALID" or "INVALID: [specific issues]" """

        return {
            "system_prompt": "You are a presentation content quality evaluator. Assess slide content for clarity and effectiveness.",
            "user_prompt": validation_prompt,
            "temperature": 0.3,
            "max_tokens": 200
        }

    @classmethod
    def get_consistency_check_prompt(cls, main_subject: str, all_slides: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Get prompt for checking consistency across all slides.
        
        Args:
            main_subject: The main presentation topic
            all_slides: List of dictionaries with 'sub_subject' and 'content' keys
            
        Returns:
            Dictionary containing consistency check prompt
        """
        slides_text = "\n\n".join([
            f"Slide: {slide['sub_subject']}\nContent: {slide['content']}" 
            for slide in all_slides
        ])
        
        consistency_prompt = f"""Main Topic: "{main_subject}"
All Slide Contents:
{slides_text}

Please evaluate the consistency across all slides and respond with "CONSISTENT" if they work well together, or "INCONSISTENT" followed by specific issues.

Evaluation criteria:
1. Do all slides maintain consistent tone and style?
2. Is there logical flow and progression between slides?
3. Do slides complement each other without unnecessary repetition?
4. Is the level of detail consistent across slides?
5. Do all slides contribute to the overall presentation narrative?

Response format: "CONSISTENT" or "INCONSISTENT: [specific issues]" """

        return {
            "system_prompt": "You are a presentation flow and consistency evaluator.",
            "user_prompt": consistency_prompt,
            "temperature": 0.3,
            "max_tokens": 300
        }