# Setup and Deployment Guide

This guide walks through setting up and deploying the Audio Transcription Service.

## Prerequisites

- Python 3.13+
- PostgreSQL 12+
- RabbitMQ 3.8+
- FFmpeg (for audio processing)
- (Optional) CUDA toolkit for GPU support with Whisper
- Docker and Docker Compose (for containerized setup)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rest-api-queue
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
# Using pip
pip install -e .

# Or using uv (if installed)
uv pip install -e .
```

### 4. Install System Dependencies

#### FFmpeg

**Windows:**

```bash
# Using chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

**macOS:**

```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt-get install ffmpeg
```

### 5. Set Up Environment

Copy the `.env.example` to `.env` and update with your configuration:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

- Database URL (PostgreSQL)
- RabbitMQ connection string
- AWS S3 or MinIO credentials
- Whisper model and device settings

## Local Development Setup

### Using Docker Compose

The easiest way to get all services running locally:

```bash
# Start all services (PostgreSQL, RabbitMQ, MinIO)
docker-compose up -d

# Initialize database
python init_db.py
```

### Manual Setup

If not using Docker Compose:

1. **PostgreSQL Setup**

```bash
# Create database
createdb transcription_db

# If using PostgreSQL locally, update CONNECTION in .env
# Default: postgresql://user:password@localhost:5432/transcription_db
```

1. **RabbitMQ Setup**

```bash
# Install and start RabbitMQ
# Windows: https://www.rabbitmq.com/install-windows.html
# macOS: brew install rabbitmq
# Linux: sudo apt-get install rabbitmq-server
```

1. **Initialize Database**

```bash
python init_db.py
```

## Running the Application

### Start the API Server

```bash
python run_server.py

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

- API documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### Start the Background Worker

In a separate terminal (with virtual environment activated):

```bash
python run_worker.py
```

The worker will:

- Connect to RabbitMQ
- Load the Whisper model
- Listen for transcription jobs
- Process jobs and store results

### Configure MinIO for Local S3 (Optional)

If using MinIO locally instead of AWS S3:

1. MinIO Web Interface: `http://localhost:9001`
   - Username: `minioadmin`
   - Password: `minioadmin`

2. Create bucket via web interface or:

```bash
# Using MinIO CLI
mc alias set minio http://localhost:9000 minioadmin minioadmin
mc mb minio/transcription-audio
```

1. Update `.env`:

```bash
S3_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET=transcription-audio
```

## API Usage

### Create a Transcription Job

```bash
curl -X POST "http://localhost:8000/api/transcriptions" \
  -F "file=@audio.mp3" \
  -F "language=en"
```

Response:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "audio.mp3",
  "status": "queued",
  "created_at": "2024-06-01T10:00:00",
  "updated_at": "2024-06-01T10:00:00"
}
```

### Get Job Status and Results

```bash
curl "http://localhost:8000/api/transcriptions/550e8400-e29b-41d4-a716-446655440000"
```

Response (while processing):

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
```

Response (after completion):

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "language": "en",
  "text": "Hello everyone welcome to the meeting",
  "segments": [
    {
      "start": 0.0,
      "end": 2.3,
      "text": "Hello everyone"
    },
    {
      "start": 2.3,
      "end": 5.8,
      "text": "welcome to the meeting"
    }
  ]
}
```

### Using the Example Client

```bash
# Edit example_client.py to point to your audio file
python example_client.py
```

## Health Check

```bash
curl "http://localhost:8000/health"
```

Response:

```json
{
  "status": "healthy",
  "service": "audio-transcription-service",
  "version": "0.1.0"
}
```

## Production Deployment

### Docker Build

```bash
# Build Docker image
docker build -t transcription-service:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e RABBITMQ_URL=amqp://... \
  transcription-service:latest
```

### Environment Variables for Production

Set the following environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `RABBITMQ_URL`: RabbitMQ connection string
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (e.g., us-east-1)
- `S3_BUCKET`: S3 bucket name
- `WHISPER_MODEL`: Model size (base, small, medium, large)
- `DEVICE`: Compute device (cpu or cuda for GPU)
- `DEBUG`: Set to False for production

### Scaling Workers

Run multiple worker instances to process jobs in parallel:

```bash
# Start multiple workers
python run_worker.py &
python run_worker.py &
python run_worker.py &
```

Or use a process manager like Supervisor or systemd.

## Troubleshooting

### Database Connection Error

```text
Error: could not translate host name "localhost" to address
```

Solution: Update `DATABASE_URL` in `.env` to match your PostgreSQL setup.

### RabbitMQ Connection Error

```text
Error: [Errno -2] Name or service not known
```

Solution: Ensure RabbitMQ is running and `RABBITMQ_URL` is correct in `.env`.

### S3 Connection Error

```text
Error: Unable to locate credentials
```

Solution: Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env`.

### FFmpeg Not Found

```text
Error: ffmpeg not found
```

Solution: Install FFmpeg (see Prerequisites section).

### Whisper Model Download

On first run, the selected Whisper model will be downloaded (~100MB+ depending on model size).

## Monitoring

### Database

Monitor job status:

```sql
SELECT job_id, status, created_at, updated_at FROM transcription_jobs
ORDER BY created_at DESC
LIMIT 10;
```

### RabbitMQ Management

Access RabbitMQ management console: `http://localhost:15672`

- Username: guest
- Password: guest

Monitor queue depth:

```bash
rabbitmqctl list_queues
```

### Logs

Check application logs:

- API server logs: stdout/stderr of `run_server.py`
- Worker logs: stdout/stderr of `run_worker.py`

## Configuration Reference

### Whisper Models

| Model  | VRAM  | Relative Speed | English-only | Multi-language |
| ------ | ----- | -------------- | ------------ | -------------- |
| tiny   | 1 GB  | 32x            | ✓            | ✓              |
| base   | 1 GB  | 16x            | ✓            | ✓              |
| small  | 2 GB  | 8x             | ✓            | ✓              |
| medium | 5 GB  | 4x             | ✓            | ✓              |
| large  | 10 GB | 1x             | ✗            | ✓              |

### Supported Audio Formats

- MP3 (.mp3)
- WAV (.wav)
- M4A (.m4a)
- AAC (.aac)
- FLAC (.flac)

All formats are automatically normalized to 16kHz mono WAV before transcription.

## Next Steps

1. Implement authentication (JWT, API keys)
2. Add rate limiting
3. Implement job expiration/cleanup
4. Add webhook notifications
5. Implement batch processing
6. Add speaker diarization
7. Add language detection
8. Implement result caching
