# Backend Dockerfile for Render
# Uses host requirements (no torch/transformers) to keep the image small.
# Set BUILD_REQUIRES=full in Render to use requirements.txt (local ML models).
FROM python:3.12-slim

WORKDIR /app

# System deps for audio processing (librosa, soundfile)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
ARG BUILD_REQUIRES=host
COPY backend/requirements-host.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source: backend/ and common/ at /app root so the sys.path
# ".." trick in services/* still resolves common/ correctly.
COPY backend/ /app/backend/
COPY common/ /app/common/

# runtime env: backend/ is the working dir, root is on PYTHONPATH for common/
WORKDIR /app/backend
ENV PYTHONPATH=/app/backend:/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

RUN mkdir -p /app/backend/uploads

# Render sets $PORT; uvicorn binds to it
CMD ["sh", "-c", "exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
