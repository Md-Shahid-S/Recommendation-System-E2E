# app/frontend/streamlit_app.py

import streamlit as st
import requests
import json
from typing import List
import pandas as pd
import joblib 
import os 

MODELS_DIR = '../../models/'
INDEX_MAP_PATH = os.path.join(MODELS_DIR, 'movie_index_map.pkl')

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
    st.stop()  

API_URL = "https://recommendation-system-e2e.onrender.com/recommendations/user/"

st.set_page_config(
    page_title="Item-Item Movie Recommender",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_recommendations_from_api(liked_titles: List[str], n: int = 10):
    """Sends user input to the FastAPI backend and returns the results."""
    
    payload = {
        "liked_movie_titles": liked_titles,
        "n_recommendations": n
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=20)
        
        if response.status_code == 200:
            return response.json()
        
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



st.title("🎬 Item-Item Collaborative Movie Recommender")
st.markdown("Enter 1 to 5 movies you have rated highly to get personalized recommendations based on similarity patterns.")

SAMPLE_TITLES = ['Toy Story', 'Heat', 'Apollo 13', 'The Dark Knight', 'Pulp Fiction', 'Fargo', 'Speed']

with st.sidebar:
    st.header("Your Input")
    
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
    
    recommend_button = st.button("Get Recommendations", type="primary")

st.markdown("---")


if recommend_button and selected_titles:
    st.subheader(f"Top {num_recs} Recommendations for you:")
    
    with st.spinner('Calculating similarities...'):
        recommendations_data = get_recommendations_from_api(selected_titles, num_recs)
    
    if recommendations_data:
        st.subheader(f"Top {len(recommendations_data)} Recommendations for you:")
        st.success("Successfully generated recommendations based on your input!")
    
        for i, rec in enumerate(recommendations_data):
        
            with st.expander(f"⭐ {rec['title']} — {rec['similarity']*100:.2f}% Similarity", expanded=True):
            
                col1, col2 = st.columns([1, 4])
            
                with col1:
                    st.metric("Similarity Score", f"{rec['similarity']*100:.2f}%")
                
                    st.markdown("**Genres:**")
                    st.info(rec['genres'] if rec['genres'] else "N/A")
                    if 'cast' in rec and rec['cast']:
                        st.markdown("**Top Cast:**")
                        st.text(rec['cast']) 
            
                with col2:
                    st.markdown("**Overview:**")
                    st.write(rec['overview'] if rec['overview'] else "Plot summary unavailable.")
                
            st.markdown("---")

elif recommend_button and not selected_titles:
    st.warning("Please select at least one movie to get recommendations.")