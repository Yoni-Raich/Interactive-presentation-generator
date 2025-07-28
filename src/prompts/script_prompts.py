"""
Prompt templates for talking script generation using LangChain and Gemini.

This module contains prompts designed to generate detailed, engaging talking scripts
that explain slide content in a human-like, conversational manner.
"""

from typing import Dict, Any, List


class ScriptPrompts:
    """Collection of prompt templates for talking script generation."""
    
    BASE_SYSTEM_PROMPT = """You are an expert presentation coach and public speaking specialist. Your task is to create engaging, detailed talking scripts that presenters can use to narrate their slides effectively.

Key requirements:
- Generate human-like, conversational narration that sounds natural when spoken
- Create detailed explanations that expand on the slide content
- Maintain consistency in tone and style across all scripts
- Use engaging language that keeps the audience interested
- Include smooth transitions and natural speech patterns
- Ensure scripts are comprehensive but not overly lengthy
- Make content accessible and easy to understand
- Use storytelling techniques where appropriate

Format your response as a natural, flowing script without stage directions or formatting instructions."""

    SCRIPT_GENERATION_PROMPT = """Main Topic: "{main_subject}"
Sub-subject: "{sub_subject}"
Slide Content: 
{slide_content}

Create a detailed talking script for this slide that:
- Expands on the slide content with additional context and explanation
- Uses natural, conversational language as if speaking to an audience
- Maintains an engaging and professional tone
- Provides smooth introduction to the sub-subject
- Explains key concepts in an accessible way
- Connects the content to the main topic
- Flows naturally when spoken aloud
- Is comprehensive but not overly lengthy (aim for 1-2 minutes of speaking time)

Generate a natural, engaging talking script that a presenter would use to explain this slide."""

    CONTEXTUAL_SCRIPT_PROMPT = """Main Topic: "{main_subject}"
Sub-subject: "{sub_subject}"
Slide Content:
{slide_content}

Previous Sub-subject: "{previous_subject}"
Next Sub-subject: "{next_subject}"
Slide Position: {slide_number} of {total_slides}

Create a talking script that:
- Provides smooth transition from the previous topic
- Thoroughly explains the current slide content
- Sets up connection to the next topic (if applicable)
- Maintains narrative flow throughout the presentation
- Uses natural, engaging speech patterns
- Expands on slide points with relevant details and examples
- Keeps the audience engaged with conversational tone

Generate a comprehensive talking script with appropriate transitions."""

    DETAILED_SCRIPT_PROMPT = """Main Topic: "{main_subject}"
Sub-subject: "{sub_subject}"
Slide Content:
{slide_content}

Audience: {audience}
Presentation Style: {style}
Duration Target: {duration} minutes

Create a talking script tailored to:
- The specified audience level and interests
- The desired presentation style and tone
- The target duration for this section
- Natural speech patterns and conversational flow
- Appropriate examples and explanations for the audience
- Engaging delivery that maintains attention

Generate a detailed, audience-appropriate talking script."""

    REVISION_SCRIPT_PROMPT = """Main Topic: "{main_subject}"
Sub-subject: "{sub_subject}"
Slide Content:
{slide_content}

Current Script:
{current_script}

Issues to address: {issues}

Please revise the talking script to address the specified issues while maintaining:
- Natural, conversational flow
- Comprehensive explanation of slide content
- Engaging and professional tone
- Appropriate length and pacing
- Consistency with overall presentation style

Generate an improved talking script that resolves the identified issues."""

    CONSISTENCY_SCRIPT_PROMPT = """Main Topic: "{main_subject}"
Sub-subject: "{sub_subject}"
Slide Content:
{slide_content}

Overall Presentation Tone: {tone}
Previous Scripts Style: {previous_style}

Create a talking script that:
- Maintains consistency with the established presentation tone
- Matches the style and approach of previous scripts
- Provides natural explanation of the slide content
- Uses similar language patterns and engagement techniques
- Flows seamlessly with the overall presentation narrative

Generate a consistent, engaging talking script."""

    @classmethod
    def get_generation_prompt(cls, main_subject: str, sub_subject: str, slide_content: str,
                            slide_number: int = None, total_slides: int = None,
                            previous_subject: str = None, next_subject: str = None) -> Dict[str, Any]:
        """
        Get the primary prompt for talking script generation.
        
        Args:
            main_subject: The main presentation topic
            sub_subject: The specific sub-subject for this slide
            slide_content: The slide content to create script for
            slide_number: Position of this slide in the presentation
            total_slides: Total number of slides in presentation
            previous_subject: Previous sub-subject for transitions
            next_subject: Next sub-subject for transitions
            
        Returns:
            Dictionary containing system and user prompts
        """
        if slide_number and total_slides and (previous_subject or next_subject):
            user_prompt = cls.CONTEXTUAL_SCRIPT_PROMPT.format(
                main_subject=main_subject,
                sub_subject=sub_subject,
                slide_content=slide_content,
                previous_subject=previous_subject or "Introduction",
                next_subject=next_subject or "Conclusion",
                slide_number=slide_number,
                total_slides=total_slides
            )
        else:
            user_prompt = cls.SCRIPT_GENERATION_PROMPT.format(
                main_subject=main_subject,
                sub_subject=sub_subject,
                slide_content=slide_content
            )
        
        return {
            "system_prompt": cls.BASE_SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "temperature": 0.7,
            "max_tokens": 800
        }
    
    @classmethod
    def get_detailed_prompt(cls, main_subject: str, sub_subject: str, slide_content: str,
                          audience: str = "general", style: str = "professional", 
                          duration: int = 2) -> Dict[str, Any]:
        """
        Get detailed prompt for audience and style-specific script generation.
        
        Args:
            main_subject: The main presentation topic
            sub_subject: The specific sub-subject for this slide
            slide_content: The slide content to create script for
            audience: Target audience description
            style: Presentation style (professional, casual, academic, etc.)
            duration: Target duration in minutes
            
        Returns:
            Dictionary containing system and user prompts
        """
        user_prompt = cls.DETAILED_SCRIPT_PROMPT.format(
            main_subject=main_subject,
            sub_subject=sub_subject,
            slide_content=slide_content,
            audience=audience,
            style=style,
            duration=duration
        )
        
        return {
            "system_prompt": cls.BASE_SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "temperature": 0.7,
            "max_tokens": 800
        }
    
    @classmethod
    def get_revision_prompt(cls, main_subject: str, sub_subject: str, slide_content: str,
                          current_script: str, issues: str) -> Dict[str, Any]:
        """
        Get prompt for revising existing talking script.
        
        Args:
            main_subject: The main presentation topic
            sub_subject: The specific sub-subject for this slide
            slide_content: The slide content
            current_script: Current script to be revised
            issues: Description of issues to address
            
        Returns:
            Dictionary containing revision prompt
        """
        user_prompt = cls.REVISION_SCRIPT_PROMPT.format(
            main_subject=main_subject,
            sub_subject=sub_subject,
            slide_content=slide_content,
            current_script=current_script,
            issues=issues
        )
        
        return {
            "system_prompt": cls.BASE_SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "temperature": 0.7,
            "max_tokens": 800
        }

    @classmethod
    def get_consistency_prompt(cls, main_subject: str, sub_subject: str, slide_content: str,
                             tone: str, previous_style: str) -> Dict[str, Any]:
        """
        Get prompt for maintaining consistency with previous scripts.
        
        Args:
            main_subject: The main presentation topic
            sub_subject: The specific sub-subject for this slide
            slide_content: The slide content
            tone: Overall presentation tone to maintain
            previous_style: Style characteristics from previous scripts
            
        Returns:
            Dictionary containing consistency prompt
        """
        user_prompt = cls.CONSISTENCY_SCRIPT_PROMPT.format(
            main_subject=main_subject,
            sub_subject=sub_subject,
            slide_content=slide_content,
            tone=tone,
            previous_style=previous_style
        )
        
        return {
            "system_prompt": cls.BASE_SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "temperature": 0.6,
            "max_tokens": 800
        }

    @classmethod
    def get_validation_prompt(cls, main_subject: str, sub_subject: str, 
                            slide_content: str, script: str) -> Dict[str, Any]:
        """
        Get prompt for validating generated talking script.
        
        Args:
            main_subject: The main presentation topic
            sub_subject: The specific sub-subject for this slide
            slide_content: The slide content
            script: Generated script to validate
            
        Returns:
            Dictionary containing validation prompt
        """
        validation_prompt = f"""Main Topic: "{main_subject}"
Sub-subject: "{sub_subject}"
Slide Content:
{slide_content}

Generated Talking Script:
{script}

Please evaluate this talking script and respond with "VALID" if it meets all criteria, or "INVALID" followed by specific issues.

Evaluation criteria:
1. Does the script naturally expand on the slide content?
2. Is the language conversational and suitable for speaking?
3. Does it maintain professional yet engaging tone?
4. Is the script comprehensive but appropriately paced?
5. Does it connect well to the main topic and sub-subject?
6. Would this sound natural when spoken aloud?
7. Is the length appropriate for presentation narration?

Response format: "VALID" or "INVALID: [specific issues]" """

        return {
            "system_prompt": "You are a presentation script quality evaluator. Assess scripts for natural flow and effectiveness.",
            "user_prompt": validation_prompt,
            "temperature": 0.3,
            "max_tokens": 300
        }

    @classmethod
    def get_flow_check_prompt(cls, main_subject: str, all_scripts: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Get prompt for checking narrative flow across all scripts.
        
        Args:
            main_subject: The main presentation topic
            all_scripts: List of dictionaries with 'sub_subject' and 'script' keys
            
        Returns:
            Dictionary containing flow check prompt
        """
        scripts_text = "\n\n---\n\n".join([
            f"Sub-subject: {script['sub_subject']}\nScript: {script['script']}" 
            for script in all_scripts
        ])
        
        flow_prompt = f"""Main Topic: "{main_subject}"
All Talking Scripts:
{scripts_text}

Please evaluate the narrative flow and consistency across all scripts and respond with "COHERENT" if they work well together, or "INCOHERENT" followed by specific issues.

Evaluation criteria:
1. Do all scripts maintain consistent tone and style?
2. Are transitions between scripts smooth and logical?
3. Is there good narrative progression throughout?
4. Do scripts complement each other without repetition?
5. Is the overall presentation story cohesive?
6. Do all scripts sound like they're from the same presenter?

Response format: "COHERENT" or "INCOHERENT: [specific issues]" """

        return {
            "system_prompt": "You are a presentation narrative flow evaluator.",
            "user_prompt": flow_prompt,
            "temperature": 0.3,
            "max_tokens": 400
        }