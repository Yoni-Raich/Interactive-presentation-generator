import base64
import mimetypes
import os
import re
import struct
from google import genai
from google.genai import types

from src.utils.exceptions import TTSGenerationError

class TTSClient:
    """A client for generating audio from text using the Google Generative AI API."""

    def __init__(self, api_key: str = None):
        """
        Initializes the TTSClient.

        Args:
            api_key: The API key for the Google Generative AI API. If not provided,
                it will be read from the GEMINI_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise TTSGenerationError("GEMINI_API_KEY not provided.")
        self.client = genai.Client(api_key=self.api_key)

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
                    print(chunk.text)
        except Exception as e:
            raise TTSGenerationError(f"Error generating audio: {e}")

    def _save_binary_file(self, file_name, data):
        with open(file_name, "wb") as f:
            f.write(data)
        print(f"File saved to to: {file_name}")

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
