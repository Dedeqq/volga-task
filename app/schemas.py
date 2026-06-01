"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TranscriptionSegment(BaseModel):
    """Schema for a single transcription segment."""

    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Segment text")


class CreateTranscriptionRequest(BaseModel):
    """Schema for creating a transcription job."""

    filename: str = Field(..., description="Name of the audio file")
    language: Optional[str] = Field(None, description="Language code (ISO 639-1)")


class TranscriptionJobResponse(BaseModel):
    """Schema for transcription job response."""

    job_id: UUID
    filename: str
    status: str = Field(
        ..., description="Job status: queued, processing, completed, failed"
    )
    language: Optional[str] = None
    text: Optional[str] = None
    segments: Optional[List[TranscriptionSegment]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class TranscriptionJobStatusResponse(BaseModel):
    """Schema for job status response."""

    job_id: UUID
    status: str = Field(..., description="Job status")
    language: Optional[str] = None
    text: Optional[str] = None
    segments: Optional[List[TranscriptionSegment]] = None
    error_message: Optional[str] = None
