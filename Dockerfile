# Multi-stage build for efficient Docker image

# Stage 1: Build stage
FROM python:3.13-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir --user .

# Stage 2: Runtime stage
FROM python:3.13-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application
COPY . .

# Add local python packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Default command (can be overridden)
CMD ["python", "run_server.py"]
