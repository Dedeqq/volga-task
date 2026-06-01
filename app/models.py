"""SQLAlchemy models for the transcription service."""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID, ENUM
import uuid

from app.database import Base


class JobStatus(str, Enum):
    """Job status enum."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptionJob(Base):
    """Model representing a transcription job."""

    __tablename__ = "transcription_jobs"

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)  # S3 path
    status = Column(ENUM(JobStatus), default=JobStatus.QUEUED, nullable=False)
    language = Column(String(10), nullable=True)  # ISO 639-1 code
    text = Column(Text, nullable=True)  # Full transcription text
    segments = Column(JSON, nullable=True)  # Array of segments with timestamps
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "job_id": str(self.job_id),
            "filename": self.filename,
            "status": self.status.value,
            "language": self.language,
            "text": self.text,
            "segments": self.segments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "error_message": self.error_message,
        }
