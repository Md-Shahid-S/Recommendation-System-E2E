# 🎬 End-to-End Movie Recommendation System

## Project Overview

This is a comprehensive, end-to-end Machine Learning project demonstrating the full MLOps lifecycle: data ingestion, feature engineering, model training, artifact versioning (DVC), model serving via a high-performance API (FastAPI), and a user interface (Streamlit).

The core of the system is an **Item-Item Collaborative Filtering** model used to recommend movies based on user preferences.

### Core Architecture

The system is split into three decoupled services:

1.  **ML Pipeline :** Data cleaning, feature engineering, and model training.
2.  **Model Serving (FastAPI):** A high-performance, containerized API that loads the model artifacts and returns recommendations as JSON.
3.  **Frontend (Streamlit):** A user-friendly web application that consumes the FastAPI endpoint and displays rich movie details.

## ⚙️ Technical Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Model** | `scikit-learn` (NearestNeighbors) | Item-Item Collaborative Filtering using Cosine Similarity. |
| **Data/Feature Prep**| `Pandas`, `SciPy` (CSR Matrix) | Cleans and merges MovieLens ratings with TMDB metadata. |
| **MLOps/Versioning**| **DVC (Data Version Control)** | Tracks and versions large model artifacts (`.joblib`, `.pkl`) outside of Git. |
| **Backend API** | **FastAPI** | High-performance API for serving prediction requests. |
| **Containerization** | **Docker** | Packages the FastAPI service for reproducible deployment on Render. |
| **Frontend UI** | **Streamlit** | Interactive web application for user input and results display. |
| **Deployment** | **Render** (FastAPI) & **Streamlit Cloud** (Frontend) | Cloud hosting of the decoupled services. |

## 💾 Dataset

The project uses a hybrid of the MovieLens and TMDB datasets to provide rich metadata:

* **`ratings_small.csv`:** Provides the user-item interaction matrix (who rated what).
* **`movies_metadata.csv` & `credits.csv` & `keywords.csv`:** Provides titles, genres, overview, cast, and crew for display.

A critical preprocessing step involves using the **`links_small.csv`** file to correctly map MovieLens IDs to TMDB IDs for merging all files.

## 🚀 Getting Started (Local Development)

### Prerequisites

You must have Python 3.9+ and Git installed.

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Md-Shahid-S/Recommendation-System-E2EL
    cd Recommendation-System-E2E
    ```
2.  **Setup Environment and Install Tools:**
    ```bash
    uv venv
    .\.venv\Scripts\activate
    uv pip install -r requirements.txt
    uv pip install dvc # Install DVC for artifact handling
    ```
3.  **Download Data:** Place `ratings_small.csv`, `movies_metadata.csv`, `links_small.csv`, `credits.csv`, and `keywords.csv` inside the **`data/raw/`** directory.

### Phase 1: Data and Model Pipeline

Run the scripts sequentially to process data and train the model.

1.  **Run Preprocessing (Notebook):** Execute the steps in your preprocessing notebook to generate the sparse matrix and lookup tables, saving them to the `models/` directory.

2.  **Run Model Training:** Train and save the K-NN model.
    ```bash
    python src/model_training.py
    ```

3.  **Version Artifacts with DVC:** Track the generated model files.
    ```bash
    dvc add models/
    git add models.dvc
    git commit -m "Trained and DVC-tracked K-NN model artifacts"
    # Note: Use 'dvc pull' and 'dvc push' for collaboration.
    ```

### Phase 2: Run the API and Frontend

1.  **Start the FastAPI Backend (API):**
    Navigate to the backend folder and start Uvicorn.
    ```bash
    cd app/backend
    uvicorn main:app --reload
    # API accessible at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    ```

2.  **Start the Streamlit Frontend (UI):**
    In a **new terminal window**, navigate to the frontend folder.
    ***Ensure the FastAPI API is running first, as the frontend depends on it.***
    ```bash
    cd app/frontend
    streamlit run streamlit_app.py
    ```

## ☁️ Deployment Instructions (Render & Streamlit Cloud)

### 1. Model Artifact Preparation (GitHub Releases)

To ensure Render can access the models, the final model artifacts must be stored on a public URL:

1.  Zip all files from the `models/` folder into a single file (e.g., `ml_artifacts.zip`).
2.  Upload this zip file as a **Release Asset** on your GitHub repository.
3.  Get the public download URL for this asset.

### 2. FastAPI Deployment (Render)

The `Dockerfile` is configured to download the model artifacts directly from the public GitHub Release URL.

1.  **Update `app/backend/Dockerfile`:** Replace `YOUR_PUBLIC_GITHUB_RELEASE_ZIP_URL` with your actual URL.
2.  Deploy the repository to Render, specifying the **Docker** runtime and port **8000**.
3.  Once deployed, copy the Render public URL (e.g., `https://my-recommender-api.onrender.com`).

### 3. Streamlit Frontend Deployment (Streamlit Cloud)

1.  **Update `app/frontend/streamlit_app.py`:** Change the `API_URL` variable to your live Render URL.
2.  Push changes to GitHub.
3.  Deploy the application on Streamlit Cloud, pointing to the file path `app/frontend/streamlit_app.py`.

## 🤝 Next Steps & Future Work

* **Hybrid Modeling:** Integrate the `cast`, `crew`, and `keywords` data (currently cleaned but not used in the model) to build a **Content-Based Filtering** component.
* **A/B Testing:** Compare the K-NN model's performance against a simpler model (e.g., Average Popularity).
* **User Interface:** Integrate movie poster images using the `tmdbId` to enhance the user experience.
