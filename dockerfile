# ---- Dockerfile (copy-paste) ----
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system deps needed for scientific packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl unzip build-essential gfortran libgfortran5 \
      libopenblas-dev liblapack-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# create app user (optional, but good practice)
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app

# Copy backend requirements first to leverage caching
# Adjust path if you want root-level requirements instead
COPY app/backend/requirements.txt /app/backend/requirements.txt

# Upgrade pip and install backend deps
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Optionally copy models if present in the repo (recommended)
# If you commit models under app/models, they will be copied here
COPY app/models /app/models

# If models are not committed, attempt to download artifact.
# Replace ARTIFACT_URL with exact release asset url if you use releases.
ARG ARTIFACT_URL="https://github.com/Md-Shahid-S/Recommendation-System-E2E/releases/download/v1.0.0/ml_artifacts_v1.zip.zip"
RUN if [ ! -d "/app/models" ] || [ -z "$(ls -A /app/models 2>/dev/null)" ]; then \
      if [ -n "$ARTIFACT_URL" ]; then \
        echo "No committed models found — attempting to download artifact..."; \
        mkdir -p /tmp/artifacts && \
        curl -fsSL "$ARTIFACT_URL" -o /tmp/artifacts/artifacts.zip && \
        unzip /tmp/artifacts/artifacts.zip -d /app/models && rm -rf /tmp/artifacts; \
      else \
        echo "No models found and no ARTIFACT_URL provided — continuing without models."; \
      fi \
    else \
      echo "Models found in repo; skipping artifact download."; \
    fi

# Copy the backend source files
COPY app/backend/ /app/backend/

# If you also want to run a frontend in the same container (not recommended),
# copy frontend files and install its requirements as needed.
# COPY app/frontend/ /app/frontend/

# Ensure proper ownership (if using non-root user)
RUN chown -R appuser:appuser /app

USER appuser
WORKDIR /app/backend

# Use the PORT environment variable that Render sets; provide fallback 8000 locally.
# Note: use shell form to expand ${PORT}
ENTRYPOINT ["sh", "-c"]
CMD ["uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info"]

EXPOSE 8000
