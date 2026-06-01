"""Transcription service for handling job creation and management."""

import os
import tempfile
from datetime import datetime
from typing import Optional
from uuid import uuid4
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import TranscriptionJob, JobStatus
from app.storage.s3_client import S3Client
from app.queue.rabbitmq import RabbitMQClient
from app.config import settings


class TranscriptionService:
    """Service for managing transcription jobs."""

    def __init__(self, db: Session):
        """Initialize transcription service."""
        self.db = db
        self.s3_client = S3Client()
        self.rabbitmq_client = RabbitMQClient()

    async def create_job(
        self, file: UploadFile, language: Optional[str] = None
    ) -> TranscriptionJob:
        """
        Create a new transcription job.

        Args:
            file: Uploaded audio file
            language: Optional language code

        Returns:
            TranscriptionJob instance
        """
        # Create a new job record
        job_id = uuid4()
        s3_key = f"audio/{job_id}/{file.filename}"

        job = TranscriptionJob(
            job_id=job_id,
            filename=file.filename,
            file_path=s3_key,
            status=JobStatus.QUEUED,
            language=language,
        )

        # Save to database
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        # Upload file to S3
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_path = tmp_file.name

            # Upload to S3
            success = self.s3_client.upload_file(tmp_path, s3_key)

            # Clean up temporary file
            os.unlink(tmp_path)

            if not success:
                raise Exception("Failed to upload file to S3")

            # Queue job for processing
            await self.queue_job(job)

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            self.db.commit()
            raise

        return job

    async def queue_job(self, job: TranscriptionJob) -> bool:
        """
        Queue a job for processing.

        Args:
            job: TranscriptionJob instance

        Returns:
            True if successful, False otherwise
        """
        try:
            job_data = {
                "job_id": str(job.job_id),
                "filename": job.filename,
                "file_path": job.file_path,
                "language": job.language,
            }

            success = await self.rabbitmq_client.publish_job(job_data)

            if success:
                job.status = JobStatus.QUEUED
                self.db.commit()

            return success
        except Exception as e:
            print(f"Error queueing job: {e}")
            return False

    def get_job(self, job_id) -> Optional[TranscriptionJob]:
        """
        Retrieve a job by ID.

        Args:
            job_id: Job UUID

        Returns:
            TranscriptionJob or None
        """
        return (
            self.db.query(TranscriptionJob)
            .filter(TranscriptionJob.job_id == job_id)
            .first()
        )

    def update_job_status(
        self,
        job_id,
        status: JobStatus,
        text: Optional[str] = None,
        segments: Optional[list] = None,
        error_message: Optional[str] = None,
    ) -> Optional[TranscriptionJob]:
        """
        Update job status and results.

        Args:
            job_id: Job UUID
            status: New job status
            text: Transcription text
            segments: Transcription segments with timestamps
            error_message: Error message if failed

        Returns:
            Updated TranscriptionJob or None
        """
        job = self.get_job(job_id)
        if not job:
            return None

        job.status = status
        if text is not None:
            job.text = text
        if segments is not None:
            job.segments = segments
        if error_message is not None:
            job.error_message = error_message
        if status == JobStatus.COMPLETED:
            job.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(job)

        return job
