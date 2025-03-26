# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /opt/transcricao-whisper-v1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    curl \
    python3-pip \
    python3-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Clone the repository and setup
RUN git clone https://github.com/jsKahne/Transcricao.git && \
    cd Transcricao && \
    mkdir -p temp && \
    chmod 777 temp

# Set working directory to Transcricao
WORKDIR /opt/transcricao-whisper-v1/Transcricao

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir torch==2.2.0+cpu --index-url https://download.pytorch.org/whl/cpu && \
    pip3 install --no-cache-dir \
    'pydantic>=2.7.0' \
    'pydantic-settings>=2.8.1' \
    'fastapi>=0.104.1' \
    'uvicorn>=0.24.0' \
    'python-multipart>=0.0.6' \
    'python-dotenv>=1.0.0' \
    'google-api-python-client>=2.108.0' \
    'google-auth-oauthlib>=1.1.0' \
    'numpy>=1.26.2' \
    'decorator>=4.4.2' \
    'imageio>=2.5' \
    'imageio-ffmpeg>=0.4.9' \
    'tqdm>=4.66.1' \
    'proglog>=0.1.10' \
    'requests>=2.31.0' \
    'moviepy>=1.0.3' \
    'aiohttp>=3.9.1' && \
    pip3 install --no-cache-dir git+https://github.com/openai/whisper.git

# Set environment variables
ENV PYTHONPATH=/opt/transcricao-whisper-v1/Transcricao
ENV TZ=America/Sao_Paulo
ENV WHISPER_MODEL=tiny
ENV PROJECT_NAME="Video Transcription API"
ENV VERSION="1.0.0"

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]