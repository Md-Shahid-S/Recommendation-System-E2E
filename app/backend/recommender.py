# app/backend/recommender.py

import joblib
import pandas as pd
import numpy as np
import os
import ast

# --- 1. Loading Model Artifacts at Startup ---
MODELS_DIR = '../../models/'
MODEL_PATH = os.path.join(MODELS_DIR, 'knn_recommender_model.joblib')
INDEX_MAP_PATH = os.path.join(MODELS_DIR, 'movie_index_map.pkl')
LOOKUP_PATH = os.path.join(MODELS_DIR, 'final_movie_lookup_df.pkl') 

# Global variables to hold the loaded artifacts
knn_model = None
movie_titles = None
movie_lookup_df = None

def load_artifacts():
    """
    Loads all necessary model components and lookup tables into memory once at startup.
    This function will be called by FastAPI's startup event.
    """
    global knn_model, movie_titles, movie_lookup_df
    
    print("Loading ML artifacts...")
    try:
        knn_model = joblib.load(MODEL_PATH)
        movie_titles = joblib.load(INDEX_MAP_PATH)
        movie_lookup_df = pd.read_pickle(LOOKUP_PATH)
        print("ML artifacts loaded successfully.")
    except Exception as e:
        print(f"Error loading artifacts: {e}")
        # In a production environment, you would log this error and halt.
        raise RuntimeError("Failed to load recommendation model artifacts.")

# --- 2. The Core Item-Based Prediction Function ---

def get_recommendations(target_movie_title: str, n_recommendations: int = 10):
    """
    Generates recommendations by finding the nearest neighbors (most similar items) 
    to a target movie. This is the core Item-Item CF function.
    
    Args:
        target_movie_title: The title of the movie to find recommendations for.
        n_recommendations: The number of recommendations to return.
    
    Returns:
        A list of dictionaries containing rich movie data.
    """
    
    if knn_model is None:
        raise RuntimeError("Model artifacts not loaded.")

    try:
        # 1. Look up the index of the target movie in the titles map
        query_index = movie_titles.index(target_movie_title)
        
        # 2. Since we need the vector for the query movie, we must load the sparse matrix.
        # NOTE: For deployment, the sparse matrix can be huge. The best practice is to 
        # save the feature vectors for ALL movies separately, but for simplicity here,
        # we will use a small placeholder/cached copy if the full matrix is too large. 
        
        # *** REAL WORLD FIX: For production, you would need to load the full 
        # movie_features_matrix.joblib artifact here or have the model pre-calculated
        # all distances. Since we trained the model on the full matrix, we need a way 
        # to access the feature vector for 'query_index'. ***

        # --- Simplified Prediction (Assumes the full sparse matrix is available, which you need to load) ---
        # Assuming we load the full sparse matrix here for a quick test:
        SPARSE_MATRIX_PATH = os.path.join(MODELS_DIR, 'movie_features_matrix.joblib')
        movie_features_matrix = joblib.load(SPARSE_MATRIX_PATH)

        query_movie_vector = movie_features_matrix[query_index]
        
        # 3. Get the neighbors (k+1 to exclude the query movie itself)
        distances, indices = knn_model.kneighbors(
            query_movie_vector, n_neighbors=n_recommendations + 1
        )
        
        # 4. Process results and fetch rich metadata
        results = []
        # Start from index 1 to skip the input movie itself
        for i in range(1, len(indices.flatten())):
            recommended_title = movie_titles[indices.flatten()[i]]
            similarity_score = 1 - distances.flatten()[i] 
            
            # Find the rich metadata (genres, cast, overview) using the title
            metadata = movie_lookup_df[movie_lookup_df['title'] == recommended_title].iloc[0].to_dict()
            
            # Construct the final output dictionary
            result = {
                'title': recommended_title,
                'similarity': round(similarity_score, 4),
                'tmdbId': metadata.get('tmdbId'),
                'genres': metadata.get('genres'),
                'cast': metadata.get('cast')[0:5], 
                'overview': metadata.get('overview'),
            }
            results.append(result)
            
        return results

    except ValueError:
        return [] # Return empty list if movie not found
    except Exception as e:
        print(f"Prediction error: {e}")
        return []

# --- 3. Example of how the NEW RATING data is used (for user-based recommendation) ---
# NOTE: This function is required if you want to predict for a specific user, not just a movie.

def predict_for_user_ratings(user_input_titles: list, n_recommendations: int = 10):
    """
    A full user-based prediction pipeline:
    1. Finds similar items for ALL movies the user liked.
    2. Aggregates results, sorts, and filters out already rated movies.
    """
    
    final_recommendations = {}
    
    for title in user_input_titles:
        # Get item-item recommendations for each movie the user likes
        similar_items = get_recommendations(title, n_recommendations=5) 
        
        for item in similar_items:
            # Aggregate the recommendations based on similarity score
            # We are using similarity as a proxy for the predicted rating
            if item['title'] not in final_recommendations:
                final_recommendations[item['title']] = item['similarity']
            else:
                # If a movie is recommended multiple times, take the highest similarity
                final_recommendations[item['title']] = max(final_recommendations[item['title']], item['similarity'])

    # Sort the aggregated results and format output
    sorted_recs = sorted(final_recommendations.items(), key=lambda item: item[1], reverse=True)
    
    # Filter out the movies the user has already rated (user_input_titles)
    final_list = [
        {'title': title, 'similarity': score} 
        for title, score in sorted_recs 
        if title not in user_input_titles
    ][:n_recommendations] # Take the top N after filtering
    
    # Now, enrich the list with the full metadata lookup
    enriched_list = []
    for rec in final_list:
        metadata = movie_lookup_df[movie_lookup_df['title'] == rec['title']].iloc[0].to_dict()

        cleaned_genres = parse_json_string(metadata.get('genres'), 'name')
        full_cast_string = parse_json_string(metadata.get('cast'), 'name')
        top_cast = ", ".join(full_cast_string.split(', ')[:3])
        rec.update({
            'tmdbId': metadata.get('tmdbId'),
            'genres': cleaned_genres,
            'cast': top_cast,
            'overview': metadata.get('overview'),
        })
        
        enriched_list.append(rec)
        
    return enriched_list


def parse_json_string(json_str, key_to_extract):
    """Safely converts a JSON string (like genres or cast) into a readable string."""
    if not isinstance(json_str, str):
        return "" # Handle NaN or non-string values
        
    try:
        # ast.literal_eval is safer than json.loads for potentially messy CSV data
        data_list = ast.literal_eval(json_str) 
        if isinstance(data_list, list):
            # Extract names from the list of dictionaries, e.g., [{'name': 'Action'}]
            names = [item.get(key_to_extract, '') for item in data_list]
            return ", ".join(names)
        return ""
    except (ValueError, SyntaxError):
        # Return raw string if parsing fails, or an empty string
        return json_str

# --- End of recommender.py ---

