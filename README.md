# Audio Transcription Service

A scalable audio transcription backend built with **FastAPI**, **Whisper (Faster-Whisper)**, and a **distributed worker architecture**. The system converts uploaded audio into text with timestamps and is designed to handle concurrent uploads and long-running transcription jobs.

---

## Overview

This service provides an API for:

* Uploading audio files (WAV, MP3, M4A, etc.)
* Asynchronous transcription using Whisper
* Returning timestamped transcript segments
* Tracking job status
* Retrieving results once processing is complete

---

## Architecture

The system is designed around an **asynchronous job pipeline** to ensure scalability and responsiveness.

```text
Client
  |
  | Upload audio / create job
  v
FastAPI Service
  |
  | Store file (S3) + create job record
  | Push job to queue
  v
RabbitMQ (Job Queue)
  |
  v
Worker Fleet (AI model inference)
  |
  | Fetch audio from storage
  | Run transcription
  v
Post-processing Layer
  |
  v
Database (PostgreSQL)
  |
  | 6. Store transcript + status
  v
Object Storage (S3)
  |
  | 7. Store original + normalized audio
  |
  v
Client Retrieval API
```

---

## Tech Stack

### Backend API

* **FastAPI** – high-performance async API framework
* **Pydantic** – request validation
* **Uvicorn** – ASGI server

### Speech-to-Text

* **Faster-Whisper** – optimized Whisper inference (CPU/GPU)
* Optional: OpenAI Whisper models (base, small, large-v3)

### Task Queue

* **RabbitMQ**

  * Job scheduling
  * Worker distribution
  * Retry handling

### Storage

* **Object Storage (S3)**

  * Stores raw and normalized audio files

### Database

* **PostgreSQL**

  * Job metadata
  * Transcript storage
  * Status tracking

### Processing Tools

* **FFmpeg**

  * Audio normalization (sampling rate, mono conversion)
  * Format standardization

---

## API Design

### 1. Create Transcription Job

```http
POST /api/transcriptions
```

**Response:**

```json
{
  "job_id": "abc123",
  "status": "queued"
}
```

---

### 2. Get Job Status / Result

```http
GET /api/transcriptions/{job_id}
```

### Response (processing)

```json
{
  "job_id": "abc123",
  "status": "processing"
}
```

### Response (completed)

```json
{
  "job_id": "abc123",
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

---

## Processing Flow

1. Client uploads audio file
2. API creates job record
3. Audio stored in object storage
4. Job is queued in RabbitMQ
5. Worker fetches job
6. Audio is normalized using FFmpeg
7. Whisper model transcribes audio
8. Segments + metadata generated
9. Results stored in database
10. Client retrieves results via API or webhook

---

## Handling Audio Formats

All input audio formats are normalized before transcription:

Supported:

* `.mp3`
* `.wav`
* `.m4a`
* `.aac`
* `.flac`

Normalization:

* Convert to **mono**
* Resample to **16kHz WAV**

This ensures consistent Whisper performance.

---

## Handling Long Audio Files

To support long recordings:

### 1. Chunking

Audio is split into smaller segments:

* improves memory usage
* enables parallel processing

### 2. Background Workers

Long jobs are processed asynchronously to avoid API blocking.

### 3. Horizontal Scaling

Multiple workers can process different chunks simultaneously.

---

## Failure Handling & Retries

The system includes:

* Automatic retries with exponential backoff
* Job state tracking:

  * `queued`
  * `processing`
  * `completed`
  * `failed`
* Dead-letter queue for persistent failures
* Idempotent job processing using `job_id`
