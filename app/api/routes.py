"""API routes for the transcription service."""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
import os

from app.database import get_db
from app.models import TranscriptionJob, JobStatus
from app.schemas import (
    CreateTranscriptionRequest,
    TranscriptionJobResponse,
    TranscriptionJobStatusResponse,
)
from app.services.transcription import TranscriptionService
from app.storage.s3_client import S3Client

router = APIRouter(prefix="/api/transcriptions", tags=["transcriptions"])


@router.post("", response_model=TranscriptionJobResponse)
async def create_transcription(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Create a new transcription job by uploading an audio file."""
    try:
        # Validate file type
        allowed_extensions = {".mp3", ".wav", ".m4a", ".aac", ".flac"}
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_ext} not supported. Supported: {allowed_extensions}",
            )

        # Save file to temporary location and upload to S3
        transcription_service = TranscriptionService(db)
        job = await transcription_service.create_job(file, language)

        return {
            "job_id": job.job_id,
            "filename": job.filename,
            "status": job.status.value,
            "language": job.language,
            "text": job.text,
            "segments": job.segments,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "completed_at": job.completed_at,
            "error_message": job.error_message,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{job_id}", response_model=TranscriptionJobStatusResponse)
async def get_transcription(job_id: UUID, db: Session = Depends(get_db)):
    """Get the status and results of a transcription job."""
    try:
        job = (
            db.query(TranscriptionJob).filter(TranscriptionJob.job_id == job_id).first()
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        # Parse segments if they exist
        segments = None
        if job.segments:
            segments = job.segments

        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "language": job.language,
            "text": job.text,
            "segments": segments,
            "error_message": job.error_message,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
