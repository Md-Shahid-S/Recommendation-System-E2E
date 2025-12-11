# 1. Use a standard Python image for stability with scientific libraries
FROM python:3.11 

# 2. Install dependencies (Download/Unzip tools AND Scientific Libraries)
# libgfortran5 and libatlas-base-dev are CRITICAL for Scipy/Scikit-learn execution.
RUN apt-get update && \
    apt-get install -y \
    curl \
    unzip \
    libgfortran5 \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/* # Clean up to keep image small

# 3. Set the working directory
WORKDIR /app

# 4. Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- ARTIFACT DOWNLOAD STEP ---
# NOTE: You MUST replace this value with the direct link to the asset 
# (It must contain /download/ in the URL, not /tag/)
ENV ARTIFACT_URL="https://github.com/Md-Shahid-S/Recommendation-System-E2E/releases/download/v1.0.0/ml_artifacts_v1.zip.zip"

# Create the models folder
RUN mkdir models
# Download the zip file (using -L to follow redirects)
RUN curl -L $ARTIFACT_URL -o artifacts.zip
# Unzip the contents into the 'models' directory
RUN unzip artifacts.zip -d models/ 
# ------------------------------

# 5. Copy the application code
# These files must be copied after the artifacts are downloaded
COPY app/backend/main.py /app/
COPY app/backend/recommender.py /app/

# 6. Expose the port and define the startup command
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
