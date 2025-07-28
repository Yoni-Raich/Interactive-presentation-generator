"""
Prompt templates for sub-subject generation using LangChain and Gemini.

This module contains prompts designed to generate relevant sub-subjects from a main topic,
ensuring logical structure and comprehensive coverage for presentation creation.
"""

from typing import Dict, Any


class SubSubjectPrompts:
    """Collection of prompt templates for sub-subject generation."""
    
    BASE_SYSTEM_PROMPT = """You are an expert presentation designer and content strategist. Your task is to analyze a given topic and break it down into logical, comprehensive sub-subjects that would make an excellent presentation structure.

Key requirements:
- Generate between 3-8 sub-subjects based on topic complexity
- Each sub-subject must be distinct and relevant to the main topic
- Sub-subjects should follow a logical progression or flow
- Ensure comprehensive coverage of the main topic
- Sub-subjects should be suitable for individual slides
- Use clear, concise language appropriate for presentation titles

Format your response as a numbered list of sub-subjects only, without additional explanation."""

    DETAILED_GENERATION_PROMPT = """Main Topic: "{subject}"

Please analyze this topic and generate a comprehensive list of sub-subjects that would create an engaging and informative presentation. Consider:

1. What are the key concepts or components of this topic?
2. What logical sequence would best help an audience understand this subject?
3. What essential points must be covered for complete understanding?
4. What aspects would be most interesting or valuable to the audience?

Generate {min_subjects} to {max_subjects} sub-subjects that:
- Cover the topic comprehensively
- Follow a logical flow from introduction to conclusion
- Are specific enough for individual slide content
- Are broad enough to allow detailed explanation
- Appeal to the target audience's interests and needs

Respond with only the numbered list of sub-subjects."""

    CONTEXT_AWARE_PROMPT = """Main Topic: "{subject}"
Presentation Context: {context}

Based on the main topic and considering the presentation context, generate sub-subjects that will create a well-structured presentation. 

The sub-subjects should:
- Be appropriate for the given context and audience
- Build upon each other logically
- Provide comprehensive coverage of the main topic
- Be engaging and informative
- Allow for detailed slide content and narration

Generate between {min_subjects} and {max_subjects} sub-subjects as a numbered list."""

    REFINEMENT_PROMPT = """Main Topic: "{subject}"
Previous sub-subjects generated: {previous_subjects}

The previous sub-subjects need refinement. Please generate an improved list that:
- Addresses any gaps in topic coverage
- Improves logical flow and progression
- Ensures each sub-subject is distinct and valuable
- Maintains focus on the main topic
- Creates better presentation structure

Generate {min_subjects} to {max_subjects} refined sub-subjects as a numbered list."""

    @classmethod
    def get_generation_prompt(cls, subject: str, min_subjects: int = 3, max_subjects: int = 8, 
                            context: str = None) -> Dict[str, Any]:
        """
        Get the primary prompt for sub-subject generation.
        
        Args:
            subject: The main presentation topic
            min_subjects: Minimum number of sub-subjects to generate
            max_subjects: Maximum number of sub-subjects to generate
            context: Optional context about the presentation
            
        Returns:
            Dictionary containing system and user prompts
        """
        if context:
            user_prompt = cls.CONTEXT_AWARE_PROMPT.format(
                subject=subject,
                context=context,
                min_subjects=min_subjects,
                max_subjects=max_subjects
            )
        else:
            user_prompt = cls.DETAILED_GENERATION_PROMPT.format(
                subject=subject,
                min_subjects=min_subjects,
                max_subjects=max_subjects
            )
        
        return {
            "system_prompt": cls.BASE_SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "temperature": 0.7,
            "max_tokens": 500
        }
    
    @classmethod
    def get_refinement_prompt(cls, subject: str, previous_subjects: list, 
                            min_subjects: int = 3, max_subjects: int = 8) -> Dict[str, Any]:
        """
        Get prompt for refining previously generated sub-subjects.
        
        Args:
            subject: The main presentation topic
            previous_subjects: List of previously generated sub-subjects
            min_subjects: Minimum number of sub-subjects to generate
            max_subjects: Maximum number of sub-subjects to generate
            
        Returns:
            Dictionary containing system and user prompts
        """
        previous_list = "\n".join([f"{i+1}. {subj}" for i, subj in enumerate(previous_subjects)])
        
        user_prompt = cls.REFINEMENT_PROMPT.format(
            subject=subject,
            previous_subjects=previous_list,
            min_subjects=min_subjects,
            max_subjects=max_subjects
        )
        
        return {
            "system_prompt": cls.BASE_SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "temperature": 0.8,
            "max_tokens": 500
        }

    @classmethod
    def get_validation_prompt(cls, subject: str, sub_subjects: list) -> Dict[str, Any]:
        """
        Get prompt for validating generated sub-subjects.
        
        Args:
            subject: The main presentation topic
            sub_subjects: List of generated sub-subjects to validate
            
        Returns:
            Dictionary containing validation prompt
        """
        subjects_list = "\n".join([f"{i+1}. {subj}" for i, subj in enumerate(sub_subjects)])
        
        validation_prompt = f"""Main Topic: "{subject}"
Generated Sub-subjects:
{subjects_list}

Please evaluate these sub-subjects and respond with "VALID" if they meet all criteria, or "INVALID" followed by specific issues if they don't.

Evaluation criteria:
1. Are all sub-subjects relevant to the main topic?
2. Do they provide comprehensive coverage?
3. Is there logical flow and progression?
4. Are they distinct from each other (no significant overlap)?
5. Are they appropriate for individual slide content?
6. Is the number of sub-subjects appropriate for the topic complexity?

Response format: "VALID" or "INVALID: [specific issues]" """

        return {
            "system_prompt": "You are a presentation quality evaluator. Assess sub-subjects for presentation structure quality.",
            "user_prompt": validation_prompt,
            "temperature": 0.3,
            "max_tokens": 200
        }