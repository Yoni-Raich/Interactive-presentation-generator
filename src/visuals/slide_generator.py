"""
This module will contain the logic for creating an image from a Markdown string.
"""
from PIL import Image, ImageDraw, ImageFont

class SlideGenerator:
    """
    A class to generate a slide with a title and bullet points.
    """

    def __init__(self, width=800, height=600, bg_color='white'):
        """
        Initializes the SlideGenerator.

        Args:
            width (int): The width of the slide in pixels.
            height (int): The height of the slide in pixels.
            bg_color (str): The background color of the slide.
        """
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.image = Image.new('RGB', (self.width, self.height), color=self.bg_color)
        self.draw = ImageDraw.Draw(self.image)

    def add_title(self, title, font_path='arial.ttf', font_size=40, text_color='black', position=(50, 50)):
        """
        Adds a title to the slide.

        Args:
            title (str): The title text.
            font_path (str): The path to the font file.
            font_size (int): The size of the font.
            text_color (str): The color of the text.
            position (tuple): The (x, y) position of the top-left corner of the text.
        """
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            font = ImageFont.load_default()
        self.draw.text(position, title, font=font, fill=text_color)

    def add_bullet_points(self, bullet_points, font_path='arial.ttf', font_size=20, text_color='black', position=(50, 120), spacing=30):
        """
        Adds bullet points to the slide.

        Args:
            bullet_points (list): A list of strings, where each string is a bullet point.
            font_path (str): The path to the font file.
            font_size (int): The size of the font.
            text_color (str): The color of the text.
            position (tuple): The (x, y) position of the first bullet point.
            spacing (int): The vertical spacing between bullet points.
        """
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            font = ImageFont.load_default()

        y = position[1]
        for point in bullet_points:
            self.draw.text((position[0], y), f'• {point}', font=font, fill=text_color)
            y += spacing

    def save(self, file_path):
        """
        Saves the slide to a file.

        Args:
            file_path (str): The path to save the image file.
        """
        self.image.save(file_path)

def create_slide_from_markdown(markdown_text: str, output_path: str):
    """
    Creates a slide from a markdown string.

    Args:
        markdown_text (str): The markdown string.
        output_path (str): The path to save the image file.
    """
    lines = markdown_text.strip().split('\\n')
    title = lines[0].strip('# ')
    bullet_points = [line.strip('- ') for line in lines[1:] if line.strip()]

    slide = SlideGenerator()
    slide.add_title(title)
    slide.add_bullet_points(bullet_points)
    slide.save(output_path)
