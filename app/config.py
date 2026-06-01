"""Configuration module for the audio transcription service."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/transcription_db"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    TRANSCRIPTION_QUEUE: str = "transcription_jobs"

    # S3 / Object Storage
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "transcription-audio"
    S3_ENDPOINT_URL: Optional[str] = None  # For MinIO or other S3-compatible services

    # Whisper Model
    WHISPER_MODEL: str = "base"  # base, small, medium, large
    DEVICE: str = "cpu"  # cpu or cuda

    # Application
    API_TITLE: str = "Audio Transcription Service"
    API_VERSION: str = "0.1.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
