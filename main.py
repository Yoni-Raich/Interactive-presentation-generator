from presentation_generator import PresentationGenerator, Config
from presentation_generator.utils.config import load_config
from presentation_generator.core.workflow import WorkflowProgress

# Load configuration
config = load_config(config_path="config_ollama.yaml")

# Define progress callback function
def progress_callback(progress: WorkflowProgress):
    """Simple progress callback that shows current status"""
    print(f"Step: {progress.current_step}")
    print(f"Progress: {progress.progress_percentage:.1f}%")
    print(f"Completed: {len(progress.completed_steps)}/{progress.total_steps}")
    print(f"Time elapsed: {progress.elapsed_time:.1f} seconds")
    print("-" * 50)

# Create generator
generator = PresentationGenerator(config=config)

print("Starting presentation generation...")

# Generate presentation WITH progress callback
presentation = generator.generate(
    "basic python tutorial",
    progress_callback=progress_callback  # This is how you use the callback
)

print(f"\nDone! Generated {len(presentation.slides)} slides")
print(f"Output saved to: {config.output_dir}")

