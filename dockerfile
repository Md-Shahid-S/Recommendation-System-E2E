# Use an official Python runtime image
FROM python:3.11

# Prevent interactive prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install system packages required for numerical/scientific Python.
# libopenblas-dev + liblapack-dev provide BLAS/LAPACK; libgfortran5 required by many wheels.
# build-essential gives compilers if a wheel needs to be compiled.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      unzip \
      ca-certificates \
      build-essential \
      gfortran \
      libgfortran5 \
      libopenblas-dev \
      liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/backend/requirements.txt
# --- ARTIFACT DOWNLOAD STEP ---
# NOTE: ensure ARTIFACT_URL points to a direct downloadable zip (contains /download/ or is a raw link).
ENV ARTIFACT_URL="https://github.com/Md-Shahid-S/Recommendation-System-E2E/releases/download/v1.0.0/ml_artifacts_v1.zip"

# Create models folder and download+unzip artifact in a single layer for smaller image
RUN mkdir -p /app/models && \
    curl -fsSL "$ARTIFACT_URL" -o /tmp/artifacts.zip && \
    unzip /tmp/artifacts.zip -d /app/models && \
    rm -f /tmp/artifacts.zip

# Copy application code (do this after installing deps and artifacts so rebuilds are faster)
COPY app/backend/ /app/

# Expose port and set start command
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
