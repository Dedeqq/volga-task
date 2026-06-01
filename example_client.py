"""Example client for testing the transcription API."""

import asyncio
import aiohttp
import json
from pathlib import Path


class TranscriptionClient:
    """Client for interacting with the transcription API."""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    async def create_transcription(self, audio_file_path: str, language: str = None):
        """
        Create a new transcription job.

        Args:
            audio_file_path: Path to audio file
            language: Optional language code

        Returns:
            Job response
        """
        async with aiohttp.ClientSession() as session:
            with open(audio_file_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field("file", f, filename=Path(audio_file_path).name)
                if language:
                    data.add_field("language", language)

                async with session.post(
                    f"{self.base_url}/api/transcriptions", data=data
                ) as resp:
                    return await resp.json()

    async def get_job_status(self, job_id: str):
        """
        Get the status of a transcription job.

        Args:
            job_id: Job ID

        Returns:
            Job status response
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/transcriptions/{job_id}"
            ) as resp:
                return await resp.json()

    async def wait_for_completion(self, job_id: str, max_wait_seconds: int = 3600):
        """
        Wait for a job to complete.

        Args:
            job_id: Job ID
            max_wait_seconds: Maximum time to wait

        Returns:
            Final job result
        """
        elapsed = 0
        interval = 5

        while elapsed < max_wait_seconds:
            result = await self.get_job_status(job_id)
            status = result.get("status")

            print(f"[{elapsed}s] Job status: {status}")

            if status == "completed":
                print("Job completed!")
                return result
            elif status == "failed":
                print(f"Job failed: {result.get('error_message')}")
                return result

            await asyncio.sleep(interval)
            elapsed += interval

        raise TimeoutError(f"Job did not complete within {max_wait_seconds} seconds")


async def main():
    """Example usage of the client."""
    client = TranscriptionClient()

    # Example audio file path - replace with your own
    audio_file = "example_audio.mp3"

    if not Path(audio_file).exists():
        print(f"Error: {audio_file} not found")
        print("Please provide a valid audio file path")
        return

    try:
        # Create transcription job
        print("Creating transcription job...")
        result = await client.create_transcription(audio_file, language="en")
        print(f"Job created: {json.dumps(result, indent=2)}")

        job_id = result["job_id"]

        # Wait for completion
        print("\nWaiting for transcription to complete...")
        final_result = await client.wait_for_completion(job_id)
        print(f"\nFinal result: {json.dumps(final_result, indent=2)}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
