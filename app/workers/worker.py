"""Background worker for processing transcription jobs."""

import asyncio
import json
import tempfile
import os
from uuid import UUID
from datetime import datetime

from faster_whisper import WhisperModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import TranscriptionJob, JobStatus
from app.audio.processor import AudioProcessor
from app.storage.s3_client import S3Client
from app.queue.rabbitmq import RabbitMQClient


class TranscriptionWorker:
    """Worker for processing transcription jobs."""

    def __init__(self):
        """Initialize worker."""
        # Initialize database
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Initialize services
        self.s3_client = S3Client()
        self.rabbitmq_client = RabbitMQClient()

        # Initialize Whisper model
        print(
            f"Loading Whisper model '{settings.WHISPER_MODEL}' on device '{settings.DEVICE}'..."
        )
        self.model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.DEVICE,
            compute_type="default",
        )
        print("Whisper model loaded successfully")

    async def process_job(self, job_data: dict):
        """
        Process a single transcription job.

        Args:
            job_data: Job data from queue
        """
        db = self.SessionLocal()
        try:
            job_id = UUID(job_data["job_id"])

            # Get job from database
            job = (
                db.query(TranscriptionJob)
                .filter(TranscriptionJob.job_id == job_id)
                .first()
            )

            if not job:
                print(f"Job {job_id} not found in database")
                return

            # Update status to processing
            job.status = JobStatus.PROCESSING
            db.commit()

            # Download audio from S3
            print(f"Downloading audio for job {job_id}...")
            with tempfile.TemporaryDirectory() as temp_dir:
                input_path = os.path.join(temp_dir, "input_audio")
                normalized_path = os.path.join(temp_dir, "normalized_audio.wav")

                success = self.s3_client.download_file(job.file_path, input_path)
                if not success:
                    raise Exception("Failed to download audio from S3")

                # Normalize audio
                print(f"Normalizing audio for job {job_id}...")
                success = AudioProcessor.normalize_audio(input_path, normalized_path)
                if not success:
                    raise Exception("Failed to normalize audio")

                # Transcribe audio
                print(f"Transcribing audio for job {job_id}...")
                segments, info = self.model.transcribe(
                    normalized_path,
                    language=job.language or None,
                )

                # Process segments
                transcript_text = ""
                segments_data = []

                for segment in segments:
                    segment_dict = {
                        "start": float(round(segment.start, 2)),
                        "end": float(round(segment.end, 2)),
                        "text": segment.text.strip(),
                    }
                    segments_data.append(segment_dict)
                    transcript_text += " " + segment.text

                # Update job with results
                job.status = JobStatus.COMPLETED
                job.text = transcript_text.strip()
                job.segments = segments_data
                job.language = info.language if info else job.language
                job.completed_at = datetime.utcnow()
                db.commit()

                print(f"Job {job_id} completed successfully")

        except Exception as e:
            print(f"Error processing job {job_data.get('job_id')}: {e}")
            job = (
                db.query(TranscriptionJob)
                .filter(TranscriptionJob.job_id == UUID(job_data["job_id"]))
                .first()
            )
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                db.commit()

        finally:
            db.close()

    async def run(self):
        """Run the worker."""
        print("Transcription worker starting...")

        # Connect to RabbitMQ
        await self.rabbitmq_client.connect()

        try:
            # Consume jobs
            await self.rabbitmq_client.consume_jobs(self.process_job)
        except KeyboardInterrupt:
            print("Worker interrupted")
        finally:
            await self.rabbitmq_client.disconnect()


async def main():
    """Entry point for worker."""
    worker = TranscriptionWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
