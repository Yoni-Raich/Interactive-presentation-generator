"""
Prompts for content validation and quality assurance.
"""

class ValidationPrompts:
    """Centralized prompts for validation operations."""
    
    @staticmethod
    def content_quality_check(content: str, topic: str, requirements: dict) -> str:
        """Generate prompt for checking content quality."""
        req_text = "\n".join([f"- {key}: {value}" for key, value in requirements.items()])
        
        return f"""Evaluate the quality of this content for the topic "{topic}":

Content:
{content}

Requirements:
{req_text}

Provide a quality score (1-10) and specific feedback on:
1. Relevance to topic
2. Clarity and readability
3. Completeness
4. Engagement level
5. Technical accuracy

Format: SCORE: [1-10] | FEEDBACK: [detailed feedback]"""

    @staticmethod
    def consistency_check(content1: str, content2: str, relationship: str) -> str:
        """Generate prompt for checking consistency between two pieces of content."""
        return f"""Check the consistency between these two pieces of content:

Content 1:
{content1}

Content 2:
{content2}

Relationship: {relationship}

Evaluate:
- Consistency in tone and style
- Logical connection
- Complementary information
- No contradictions
- Appropriate level of detail

Respond with "CONSISTENT" or "INCONSISTENT: [specific issues]"."""

    @staticmethod
    def completeness_check(content: str, topic: str, expected_elements: list) -> str:
        """Generate prompt for checking content completeness."""
        elements_text = "\n".join([f"- {element}" for element in expected_elements])
        
        return f"""Check if this content adequately covers the topic "{topic}":

Content:
{content}

Expected elements:
{elements_text}

Evaluate:
- Coverage of all expected elements
- Appropriate depth for each element
- Missing critical information
- Balance between elements

Respond with "COMPLETE" or "INCOMPLETE: [missing elements]"."""

    @staticmethod
    def presentation_flow_check(slides_info: list) -> str:
        """Generate prompt for checking overall presentation flow."""
        slides_text = "\n".join([f"{i+1}. {slide['title']}: {slide['summary']}" 
                                for i, slide in enumerate(slides_info)])
        
        return f"""Evaluate the flow and structure of this presentation:

Slides:
{slides_text}

Check for:
- Logical progression of topics
- Smooth transitions between slides
- Appropriate introduction and conclusion
- Balanced coverage of the subject
- Engaging narrative arc

Provide feedback on the overall flow and suggest improvements if needed."""