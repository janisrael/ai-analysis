# AI Avatar Assistant - Production Docker Image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # For audio/speech recognition
    portaudio19-dev \
    alsa-utils \
    espeak \
    espeak-data \
    # For GUI dependencies (optional)
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libxft2 \
    libfreetype6 \
    # For building packages
    gcc \
    g++ \
    make \
    # For networking
    curl \
    wget \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional production dependencies
RUN pip install --no-cache-dir \
    gunicorn \
    uvicorn \
    websockets \
    redis \
    celery \
    supervisor

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p \
    /app/data \
    /app/logs \
    /app/reports \
    /app/temp \
    /var/log/supervisor

# Set proper permissions
RUN chmod +x scripts/start.sh scripts/health-check.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash ai_assistant && \
    chown -R ai_assistant:ai_assistant /app

# Copy supervisor configuration
COPY deployment/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports
EXPOSE 5555 8080 6379

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python scripts/health-check.py

# Switch to non-root user
USER ai_assistant

# Default command
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]