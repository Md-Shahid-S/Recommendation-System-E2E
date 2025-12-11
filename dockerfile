# 1. Use a slim Python image
FROM python:3.11-slim

# 2. Install dependencies needed for downloading/unzipping
# We need 'curl' for downloading and 'unzip' for decompressing
RUN apt-get update && apt-get install -y curl unzip

# 3. Set the working directory
WORKDIR /app

# 4. Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- ARTIFACT DOWNLOAD STEP (NEW) ---
# Define the URL of your uploaded zip file from the GitHub Release
# You must paste your exact, public download link here!
ENV ARTIFACT_URL="YOUR_PUBLIC_GITHUB_RELEASE_ZIP_URL"

# Create the models folder and download the artifacts
RUN mkdir models
# Download the zip file and save it as artifacts.zip
RUN curl -L $ARTIFACT_URL -o artifacts.zip
# Unzip the contents into the 'models' directory
RUN unzip artifacts.zip -d models/ 
# ------------------------------------

# 5. Copy the application code
COPY app/backend/main.py /app/
COPY app/backend/recommender.py /app/
# ... (any other code files) ...

# 6. Expose the port and command
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]