import base64
import json
import mimetypes
import os
import re
import struct
import sys
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from src.utils.exceptions import TTSGenerationError
from src.utils.logger import get_logger

class TTSClient:
    """A client for generating audio from text using the Google Generative AI API."""

    def __init__(self, api_key: str = None):
        """
        Initializes the TTSClient.

        Args:
            api_key: The API key for the Google Generative AI API. If not provided,
                it will be read from the GEMINI_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise TTSGenerationError("GEMINI_API_KEY or GOOGLE_API_KEY not provided.")
        self.client = genai.Client(api_key=self.api_key)
        self.logger = get_logger(__name__)

    def generate_audio(self, text: str, file_path: str):
        """
        Generates an audio file from the given text.

        Args:
            text: The text to convert to speech.
            file_path: The path to save the audio file.
        """
        try:
            model = "gemini-2.5-flash-preview-tts"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=text),
                    ],
                ),
            ]
            generate_content_config = types.GenerateContentConfig(
                temperature=1,
                response_modalities=["audio"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Puck"
                        )
                    )
                ),
            )

            file_index = 0
            for chunk in self.client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue
                if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                    file_name = f"{file_path}_{file_index}"
                    file_index += 1
                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    data_buffer = inline_data.data
                    file_extension = mimetypes.guess_extension(inline_data.mime_type)
                    if file_extension is None:
                        file_extension = ".wav"
                        data_buffer = self._convert_to_wav(inline_data.data, inline_data.mime_type)
                    self._save_binary_file(f"{file_name}{file_extension}", data_buffer)
                else:
                    self.logger.info(chunk.text)
        except Exception as e:
            raise TTSGenerationError(f"Error generating audio: {e}")

    def _save_binary_file(self, file_name, data):
        with open(file_name, "wb") as f:
            f.write(data)
        print(f"File saved to: {file_name}")

    def _convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        parameters = self._parse_audio_mime_type(mime_type)
        bits_per_sample = parameters["bits_per_sample"]
        sample_rate = parameters["rate"]
        num_channels = 1
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            chunk_size,
            b"WAVE",
            b"fmt ",
            16,
            1,
            num_channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b"data",
            data_size,
        )
        return header + audio_data

    def _parse_audio_mime_type(self, mime_type: str) -> dict[str, int | None]:
        bits_per_sample = 16
        rate = 24000

        parts = mime_type.split(";")
        for param in parts:
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate_str = param.split("=", 1)[1]
                    rate = int(rate_str)
                except (ValueError, IndexError):
                    pass
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass

        return {"bits_per_sample": bits_per_sample, "rate": rate}

    def process_presentation_json(self, json_file_path: str, output_dir: str = None) -> str:
        """
        Processes a presentation JSON file and generates audio files for all talking scripts.
        
        Args:
            json_file_path: Path to the presentation JSON file
            output_dir: Directory to save audio files (optional, defaults to same directory as JSON)
            
        Returns:
            str: Path to the updated JSON file with audio paths
            
        Raises:
            TTSGenerationError: If there's an error processing the JSON or generating audio
        """
        try:
            # Read the JSON file
            with open(json_file_path, 'r', encoding='utf-8') as f:
                presentation_data = json.load(f)
            
            # Set output directory
            if output_dir is None:
                output_dir = os.path.dirname(json_file_path)
            
            # Create audio subdirectory
            audio_dir = os.path.join(output_dir, "audio")
            os.makedirs(audio_dir, exist_ok=True)
            
            # Process each slide
            for i, slide in enumerate(presentation_data.get("slides", [])):
                talking_script = slide.get("talking_script", "")
                
                if talking_script.strip():
                    # Generate unique filename for this slide
                    safe_subject = re.sub(r'[^\w\s-]', '', slide.get("sub_subject", f"slide_{i}"))
                    safe_subject = re.sub(r'[-\s]+', '_', safe_subject)
                    audio_filename = f"slide_{i:02d}_{safe_subject}"
                    audio_path = os.path.join(audio_dir, audio_filename)
                    
                    self.logger.info(f"Generating audio for slide {i+1}: {slide.get('sub_subject', 'Unknown')}")
                    
                    # Generate audio file
                    self.generate_audio(talking_script, audio_path)
                    
                    # Find the generated audio file (it might have _0.wav suffix)
                    generated_files = []
                    for file in os.listdir(audio_dir):
                        if file.startswith(os.path.basename(audio_filename)):
                            generated_files.append(os.path.join(audio_dir, file))
                    
                    if generated_files:
                        # Use the first generated file (usually there's only one)
                        relative_audio_path = os.path.relpath(generated_files[0], output_dir)
                        slide["audio_path"] = relative_audio_path
                        self.logger.info(f"Audio saved: {relative_audio_path}")
                    else:
                        self.logger.warning(f"No audio file generated for slide {i+1}")
                else:
                    self.logger.warning(f"No talking script found for slide {i+1}")
            
            # Save updated JSON
            updated_json_path = json_file_path.replace('.json', '_with_audio.json')
            with open(updated_json_path, 'w', encoding='utf-8') as f:
                json.dump(presentation_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Updated presentation saved to: {updated_json_path}")
            return updated_json_path
            
        except FileNotFoundError:
            raise TTSGenerationError(f"JSON file not found: {json_file_path}")
        except json.JSONDecodeError as e:
            raise TTSGenerationError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise TTSGenerationError(f"Error processing presentation JSON: {e}")

    def process_multiple_presentations(self, json_files: list, output_dir: str = None) -> list:
        """
        Processes multiple presentation JSON files and generates audio for all.
        
        Args:
            json_files: List of paths to presentation JSON files
            output_dir: Directory to save audio files (optional)
            
        Returns:
            list: List of paths to updated JSON files with audio paths
            
        Raises:
            TTSGenerationError: If there's an error processing any JSON file
        """
        updated_files = []
        
        for i, json_file in enumerate(json_files, 1):
            try:
                self.logger.info(f"Processing file {i}/{len(json_files)}: {json_file}")
                updated_file = self.process_presentation_json(json_file, output_dir)
                updated_files.append(updated_file)
                
            except Exception as e:
                self.logger.error(f"Failed to process {json_file}: {e}")
                # Continue with other files instead of stopping
                continue
        
        return updated_files

if __name__ == '__main__':
    tts_client = TTSClient()
    tts = "היי זה בדיקה ראשונית!"
    tts_client.generate_audio(tts, "output")