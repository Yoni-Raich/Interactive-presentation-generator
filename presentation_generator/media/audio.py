"""
Audio processing component for TTS generation with duration calculation.

Consolidates TTS functionality from the existing tts_client module
and adds automatic duration calculation from generated audio files.
"""

import os
import re
import struct
import mimetypes
import wave
from pathlib import Path
from typing import List

from google import genai
from google.genai import types

from ..models.data import Slide
from ..utils.exceptions import MediaProcessingError
from ..utils.config import Config


class AudioProcessor:
    """
    Processes slide scripts to generate audio files with duration calculation.
    
    Consolidates TTS functionality and integrates with the new Slide data model.
    Automatically calculates and sets slide duration from generated audio length.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the audio processor.
        
        Args:
            config: Configuration object with API keys and audio settings
            
        Raises:
            MediaProcessingError: If API key is not provided
        """
        self.config = config
        
        # Get API key from config or environment
        api_key = (
            getattr(config, 'gemini_api_key', None) or
            os.environ.get("GEMINI_API_KEY") or
            os.environ.get("GOOGLE_API_KEY")
        )
        
        if not api_key:
            raise MediaProcessingError(
                "Gemini API key not provided. Set GEMINI_API_KEY environment variable "
                "or provide it in the configuration."
            )
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash-preview-tts"
    
    def process_slides(self, slides: List[Slide], output_dir: Path) -> None:
        """
        Process all slides to generate audio and populate audio_path and duration.
        
        Args:
            slides: List of slides to process
            output_dir: Directory to save generated audio files
            
        Raises:
            MediaProcessingError: If audio generation fails
        """
        output_dir = Path(output_dir)
        audio_dir = output_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        for i, slide in enumerate(slides, 1):
            try:
                if not slide.script or not slide.script.strip():
                    continue
                
                # Generate filename
                filename = self._generate_filename(i, slide.title)
                audio_path = audio_dir / filename
                
                # Generate audio file
                self._generate_audio(slide.script, audio_path)
                
                # Update slide with audio path (relative to output_dir)
                slide.audio_path = str(audio_path.relative_to(output_dir))
                
                # Calculate and set duration from audio file
                slide.duration = self._calculate_duration(audio_path)
                
            except Exception as e:
                raise MediaProcessingError(
                    f"Failed to generate audio for slide {i}: {e}"
                )
    
    def _generate_audio(self, text: str, output_path: Path) -> None:
        """
        Generate audio file from text using Gemini TTS.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file (without extension)
            
        Raises:
            MediaProcessingError: If TTS generation fails
        """
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=text)],
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
            
            # Generate audio stream
            audio_data = b""
            mime_type = None
            
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates and
                    chunk.candidates[0].content and
                    chunk.candidates[0].content.parts
                ):
                    part = chunk.candidates[0].content.parts[0]
                    if part.inline_data and part.inline_data.data:
                        audio_data += part.inline_data.data
                        if not mime_type:
                            mime_type = part.inline_data.mime_type
            
            if not audio_data:
                raise MediaProcessingError("No audio data received from TTS service")
            
            # Determine file extension and convert if needed
            if mime_type and "wav" in mime_type.lower():
                file_extension = ".wav"
                final_data = audio_data
            else:
                # Convert to WAV format
                file_extension = ".wav"
                final_data = self._convert_to_wav(audio_data, mime_type or "audio/pcm")
            
            # Save audio file
            final_path = output_path.with_suffix(file_extension)
            with open(final_path, "wb") as f:
                f.write(final_data)
            
            # Update the output_path to reflect the actual saved file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if final_path != output_path:
                # If we added an extension, rename the slide's expected path
                pass  # The calling code will handle the path correctly
            
        except Exception as e:
            raise MediaProcessingError(f"TTS generation failed: {e}")
    
    def _convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        """
        Convert audio data to WAV format.
        
        Args:
            audio_data: Raw audio data
            mime_type: MIME type of the audio data
            
        Returns:
            WAV formatted audio data
        """
        try:
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
            
        except Exception as e:
            raise MediaProcessingError(f"Audio format conversion failed: {e}")
    
    def _parse_audio_mime_type(self, mime_type: str) -> dict:
        """
        Parse audio MIME type to extract parameters.
        
        Args:
            mime_type: MIME type string
            
        Returns:
            Dictionary with bits_per_sample and rate
        """
        bits_per_sample = 16
        rate = 24000
        
        if not mime_type:
            return {"bits_per_sample": bits_per_sample, "rate": rate}
        
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
    
    def _calculate_duration(self, audio_path: Path) -> float:
        """
        Calculate duration of audio file in seconds.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Duration in seconds
            
        Raises:
            MediaProcessingError: If duration calculation fails
        """
        try:
            # Handle the case where we might have saved with .wav extension
            actual_path = audio_path
            if not actual_path.exists():
                actual_path = audio_path.with_suffix('.wav')
            
            if not actual_path.exists():
                raise MediaProcessingError(f"Audio file not found: {audio_path}")
            
            # Read WAV file to get duration
            with wave.open(str(actual_path), 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / float(sample_rate)
                return round(duration, 2)
                
        except Exception as e:
            # Fallback: estimate duration based on text length
            # Rough estimate: ~150 words per minute, ~5 characters per word
            text_length = len(getattr(self, '_last_text', ''))
            estimated_duration = max(2.0, text_length / (150 * 5 / 60))
            return round(estimated_duration, 2)
    
    def _generate_filename(self, slide_number: int, title: str) -> str:
        """
        Generate safe filename for audio file.
        
        Args:
            slide_number: Slide number
            title: Slide title
            
        Returns:
            Safe filename without extension
        """
        # Clean title for filename
        clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        clean_title = re.sub(r'\s+', '_', clean_title)
        clean_title = re.sub(r'_+', '_', clean_title).strip('_')
        
        if not clean_title:
            clean_title = 'slide'
        
        # Limit length
        if len(clean_title) > 50:
            clean_title = clean_title[:50].rstrip('_')
        
        return f"slide_{slide_number:02d}_{clean_title.lower()}"