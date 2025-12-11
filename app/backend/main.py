from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import recommender 


class Recommendation(BaseModel):
    title: str
    similarity: float
    tmdbId: int = None
    genres: str = None
    overview: str = None

class UserInput(BaseModel):
    liked_movie_titles: List[str]
    n_recommendations: int = 10 


app = FastAPI(
    title="Item-Item Collaborative Filtering Recommender API",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """
    Called once when the application starts up. 
    Loads the ML model and lookup tables into memory.
    """
    try:
        recommender.load_artifacts()
        print("FastAPI: Recommendation artifacts loaded successfully.")
    except Exception as e:
        print(f"FATAL ERROR during startup: {e}")
       

@app.post("/recommendations/user/", response_model=List[Recommendation])
async def get_user_recommendations(user_input: UserInput):
    """
    Accepts a list of movies a user likes and returns the top predicted movies 
    they haven't seen, based on aggregated Item-Item similarity.
    """
    if not user_input.liked_movie_titles:
        raise HTTPException(
            status_code=400, 
            detail="Please provide at least one movie title the user liked."
        )

    try:
       
        recommendations = recommender.predict_for_user_ratings(
            user_input.liked_movie_titles, 
            user_input.n_recommendations
        )
        
        if not recommendations:
             raise HTTPException(
                status_code=404, 
                detail="Could not find recommendations. Check if titles are spelled correctly or if the user is a cold-start user."
            )

        return recommendations

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during prediction: {e}")


@app.get("/health")
def health_check():
    """Returns the status of the API and model loading."""
    status = "ready" if recommender.knn_model is not None else "model_loading_failed"
    return {"status": status, "model_loaded": recommender.knn_model is not None}