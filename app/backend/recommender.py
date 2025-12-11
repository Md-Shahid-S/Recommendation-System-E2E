# app/backend/recommender.py

import joblib
import pandas as pd
import numpy as np
import os
import ast


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
        
        raise RuntimeError("Failed to load recommendation model artifacts.")


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
        
        query_index = movie_titles.index(target_movie_title)
        
        
        SPARSE_MATRIX_PATH = os.path.join(MODELS_DIR, 'movie_features_matrix.joblib')
        movie_features_matrix = joblib.load(SPARSE_MATRIX_PATH)

        query_movie_vector = movie_features_matrix[query_index]
        
        distances, indices = knn_model.kneighbors(
            query_movie_vector, n_neighbors=n_recommendations + 1
        )
        
        # 4. Process results and fetch rich metadata
        results = []
        
        for i in range(1, len(indices.flatten())):
            recommended_title = movie_titles[indices.flatten()[i]]
            similarity_score = 1 - distances.flatten()[i] 
            
            
            metadata = movie_lookup_df[movie_lookup_df['title'] == recommended_title].iloc[0].to_dict()
            
           
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
        return [] 
    except Exception as e:
        print(f"Prediction error: {e}")
        return []


def predict_for_user_ratings(user_input_titles: list, n_recommendations: int = 10):
    """
    A full user-based prediction pipeline:
    1. Finds similar items for ALL movies the user liked.
    2. Aggregates results, sorts, and filters out already rated movies.
    """
    
    final_recommendations = {}
    
    for title in user_input_titles:
 
        similar_items = get_recommendations(title, n_recommendations=5) 
        
        for item in similar_items:
            if item['title'] not in final_recommendations:
                final_recommendations[item['title']] = item['similarity']
            else:
                final_recommendations[item['title']] = max(final_recommendations[item['title']], item['similarity'])

    sorted_recs = sorted(final_recommendations.items(), key=lambda item: item[1], reverse=True)
    
    final_list = [
        {'title': title, 'similarity': score} 
        for title, score in sorted_recs 
        if title not in user_input_titles
    ][:n_recommendations] 
    
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
        return "" 
        
    try:
        data_list = ast.literal_eval(json_str) 
        if isinstance(data_list, list):
            names = [item.get(key_to_extract, '') for item in data_list]
            return ", ".join(names)
        return ""
    except (ValueError, SyntaxError):
        return json_str


