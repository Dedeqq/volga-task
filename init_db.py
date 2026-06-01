"""Database initialization and migration utilities."""

import alembic.config
from app.database import engine, Base
from app.models import TranscriptionJob, JobStatus


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


if __name__ == "__main__":
    init_db()
