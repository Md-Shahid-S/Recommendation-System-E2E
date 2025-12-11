# app/frontend/streamlit_app.py

import streamlit as st
import requests
import json
from typing import List
import pandas as pd
import joblib 
import os 

# Define the relative path to the models directory
MODELS_DIR = 'app/models/' 
INDEX_MAP_PATH = os.path.join(MODELS_DIR, 'movie_index_map.pkl')

# --- Load the full list of titles once when the app starts ---
@st.cache_resource
def load_all_movie_titles():
    """Loads the full list of movie titles used in the K-NN model."""
    try:
        
        return joblib.load(INDEX_MAP_PATH) 
    except Exception as e:
        st.error(f"Error loading movie list: {e}")
        return []

FULL_MOVIE_LIST = load_all_movie_titles()
if not FULL_MOVIE_LIST:
    st.stop()  # Stop execution if titles couldn't be loaded

# IMPORTANT: API_URL needs to be updated when deployed to Render!
# For local testing, use the Uvicorn address:
API_URL = "https://recommendation-system-e2e-1.onrender.com/recommendations/user/"

st.set_page_config(
    page_title="Item-Item Movie Recommender",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Define the API Call Function ---
def get_recommendations_from_api(liked_titles: List[str], n: int = 10):
    """Sends user input to the FastAPI backend and returns the results."""
    
    # 1. Prepare the JSON payload based on the UserInput Pydantic model
    payload = {
        "liked_movie_titles": liked_titles,
        "n_recommendations": n
    }
    
    try:
        # 2. Make the POST request to the deployed API endpoint
        response = requests.post(API_URL, json=payload, timeout=20)
        
        # 3. Handle success
        if response.status_code == 200:
            return response.json()
        
        # 4. Handle errors defined in FastAPI
        elif response.status_code == 400:
            st.error(f"API Error: {response.json().get('detail', 'Bad Request')}")
            return None
        else:
            st.error(f"API Call Failed. Status Code: {response.status_code}")
            st.warning("Please ensure the FastAPI backend is running.")
            return None

    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to API at {API_URL}.")
        st.warning("Make sure the FastAPI server is running in another terminal.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None


# --- Streamlit UI Layout ---

st.title("🎬 Item-Item Collaborative Movie Recommender")
st.markdown("Enter 1 to 5 movies you have rated highly to get personalized recommendations based on similarity patterns.")

# Placeholder list of popular movies for easy testing
SAMPLE_TITLES = ['Toy Story', 'Heat', 'Apollo 13', 'The Dark Knight', 'Pulp Fiction', 'Fargo', 'Speed']

with st.sidebar:
    st.header("Your Input")
    
    # Multiselect widget for the user to choose liked movies
    selected_titles = st.multiselect(
        "Which movies have you liked?",
        options=FULL_MOVIE_LIST, 
        default=['Toy Story'],
        max_selections=5
    )

    num_recs = st.slider(
        "Number of recommendations",
        min_value=5, max_value=20, value=10
    )
    
    # Button to trigger the API call
    recommend_button = st.button("Get Recommendations", type="primary")

st.markdown("---")

# --- Recommendation Display Logic ---

if recommend_button and selected_titles:
    st.subheader(f"Top {num_recs} Recommendations for you:")
    
    # Show spinner while waiting for API response
    with st.spinner('Calculating similarities...'):
        recommendations_data = get_recommendations_from_api(selected_titles, num_recs)
    
    if recommendations_data:
        st.subheader(f"Top {len(recommendations_data)} Recommendations for you:")
        st.success("Successfully generated recommendations based on your input!")
    
    # Use Streamlit's columns to create a clean, card-like display for each movie
        for i, rec in enumerate(recommendations_data):
        
        # Use an expander for the overview/details
        # The title now includes the calculated similarity score
            with st.expander(f"⭐ {rec['title']} — {rec['similarity']*100:.2f}% Similarity", expanded=True):
            
            # Use columns for neat alignment of metadata (1:4 ratio for key stats vs. plot)
                col1, col2 = st.columns([1, 4])
            
            # --- Col 1: Key Data & Stats ---
                with col1:
                # Display the Similarity Score clearly using the metric widget
                    st.metric("Similarity Score", f"{rec['similarity']*100:.2f}%")
                
                # Display the Genres (which are now clean strings from the backend)
                    st.markdown("**Genres:**")
                    st.info(rec['genres'] if rec['genres'] else "N/A")

                # Display the Cast (which are now top 3 names from the backend)
                # The 'cast' key must exist in the dict, which it does based on your recommender.py changes
                    if 'cast' in rec and rec['cast']:
                        st.markdown("**Top Cast:**")
                        st.text(rec['cast']) 
            
            # --- Col 2: Overview/Plot ---
                with col2:
                    st.markdown("**Overview:**")
                    st.write(rec['overview'] if rec['overview'] else "Plot summary unavailable.")
                
            st.markdown("---")

elif recommend_button and not selected_titles:
    st.warning("Please select at least one movie to get recommendations.")