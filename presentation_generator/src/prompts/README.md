# Prompt Management

This directory contains all prompts used throughout the presentation generator library. Centralizing prompts makes them easier to maintain, version, and customize.

## Structure

- **`content_generation.py`**: Core prompts for generating slide topics, content, and scripts
- **`slide_generation.py`**: Slide-specific prompts for validation and enhancement
- **`provider_prompts.py`**: Provider-specific prompts and system messages
- **`validation_prompts.py`**: Content validation and quality assurance prompts

## Usage

```python
from src.prompts.content_generation import ContentPrompts

# Generate slide topics
prompt = ContentPrompts.slide_topics_generation(
    main_topic="Machine Learning",
    target_count=6,
    min_slides=4,
    max_slides=8
)

# Generate slide content
content_prompt = ContentPrompts.slide_content_generation(
    topic="Neural Networks",
    main_topic="Machine Learning", 
    slide_number=3,
    total_slides=6
)
```

## Best Practices

1. **Keep prompts focused**: Each prompt should have a single, clear purpose
2. **Use parameters**: Make prompts flexible with parameters rather than hardcoding values
3. **Include clear requirements**: Specify format, length, and quality expectations
4. **Provide context**: Give the LLM sufficient context for better results
5. **Version control**: Track changes to prompts as they affect output quality
6. **Test thoroughly**: Changes to prompts can significantly impact generation quality

## Adding New Prompts

When adding new prompts:

1. Choose the appropriate module based on functionality
2. Follow the existing naming convention (`verb_noun_prompt`)
3. Use static methods for stateless prompts
4. Include comprehensive docstrings
5. Add parameters for flexibility
6. Update the module's `__all__` list if needed

## Prompt Engineering Guidelines

- **Be specific**: Clear, detailed instructions produce better results
- **Use examples**: Show the desired format when helpful
- **Set constraints**: Specify length, format, and quality requirements
- **Provide context**: Include relevant background information
- **Use consistent language**: Maintain the same tone and terminology
- **Test variations**: Experiment with different phrasings for optimal results