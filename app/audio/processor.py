"""Audio processing utilities."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class AudioProcessor:
    """Handle audio format conversion and normalization."""

    # Audio normalization target
    TARGET_SAMPLE_RATE = 16000
    TARGET_CHANNELS = 1  # Mono
    TARGET_FORMAT = "wav"

    @staticmethod
    def normalize_audio(input_path: str, output_path: str) -> bool:
        """
        Normalize audio file to 16kHz mono WAV format.

        Args:
            input_path: Path to input audio file
            output_path: Path to output audio file

        Returns:
            True if successful, False otherwise
        """
        try:
            command = [
                "ffmpeg",
                "-i",
                input_path,
                "-ar",
                str(AudioProcessor.TARGET_SAMPLE_RATE),
                "-ac",
                str(AudioProcessor.TARGET_CHANNELS),
                "-q:a",
                "9",  # Quality (0-9, lower is better)
                "-y",  # Overwrite output file
                output_path,
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                return False

            return os.path.exists(output_path)
        except subprocess.TimeoutExpired:
            print("Audio normalization timed out")
            return False
        except Exception as e:
            print(f"Error normalizing audio: {e}")
            return False

    @staticmethod
    def get_audio_duration(file_path: str) -> Optional[float]:
        """
        Get duration of audio file in seconds.

        Args:
            file_path: Path to audio file

        Returns:
            Duration in seconds or None if error
        """
        try:
            command = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1:nokey=1",
                file_path,
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception as e:
            print(f"Error getting audio duration: {e}")

        return None
