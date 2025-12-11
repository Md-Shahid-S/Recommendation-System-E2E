# Dockerfile - use this when models are committed under app/models/
FROM python:3.11-slim

# Environment settings
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system deps required by numpy/scipy/scikit-learn and common build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      curl \
      unzip \
      gfortran \
      libgfortran5 \
      libopenblas-dev \
      liblapack-dev \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the app (optional but recommended)
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory (root of project inside container)
WORKDIR /app

# Copy backend requirements first to leverage Docker layer caching
COPY app/backend/requirements.txt /app/backend/requirements.txt

# Install python dependencies for backend
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy committed models from the repository into the image
# (Place your model files under app/models/ in the repo)
COPY app/models /app/models

# Copy the backend application code into the image
COPY app/backend /app/backend

# If you also need frontend inside same image (not recommended for production),
# copy it and install its deps, otherwise run frontend separately.
# COPY app/frontend /app/frontend
# RUN pip install --no-cache-dir -r /app/frontend/requirements.txt

# Fix ownership for non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set working directory to backend (so uvicorn can import main)
WORKDIR /app/backend

# Use Render's PORT env var when available, with fallback to 8000 for local runs.
# This uses shell form so ${PORT} is expanded at runtime.
ENTRYPOINT ["sh", "-c"]
CMD ["uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info"]

# Expose the default port (Render will set PORT env var)
EXPOSE 8000
