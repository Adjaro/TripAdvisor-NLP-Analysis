from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from sqlalchemy.orm import Session
from typing import List
from model import models, schemas
from utils import database

# Database dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def fetch_restaurant_data(db: Session) -> pd.DataFrame:
    restaurants = db.query(models.DimRestaurant).all()
    df = pd.DataFrame([schemas.DimRestaurant.from_orm(restaurant).dict() for restaurant in restaurants])
    return df

def recommend_restaurants(restaurant_name: str, db: Session, top_n: int = 5) -> List[schemas.DimRestaurant]:
    df = fetch_restaurant_data(db)
    
    if restaurant_name not in df['nom'].values:
        raise ValueError(f"Restaurant '{restaurant_name}' not found in the database.")
    
    # Combine relevant features into a single string
    df['combined_features'] = df.apply(lambda row: f"{row['type_cuisines']} {row['adresse']} {row['note_globale']}", axis=1)
    
    # Vectorize the combined features
    vectorizer = TfidfVectorizer()
    feature_matrix = vectorizer.fit_transform(df['combined_features'])
    
    # Find the index of the given restaurant
    restaurant_idx = df[df['nom'] == restaurant_name].index[0]
    
    # Calculate cosine similarity
    cosine_sim = cosine_similarity(feature_matrix, feature_matrix)
    
    # Get similarity scores for the given restaurant
    similarity_scores = list(enumerate(cosine_sim[restaurant_idx]))
    
    # Sort the restaurants based on similarity scores
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    
    # Get the indices of the top_n most similar restaurants
    similar_restaurant_indices = [i[0] for i in similarity_scores[1:top_n+1]]
    
    # Fetch the recommended restaurants
    recommended_restaurants = df.iloc[similar_restaurant_indices]
    
    return [schemas.DimRestaurant.from_orm(models.DimRestaurant(**restaurant)) for restaurant in recommended_restaurants.to_dict(orient='records')]

# Example usage
def example_usage():
    db = next(get_db())
    try:
        recommendations = recommend_restaurants("L'Institut Restaurant", db)
        for restaurant in recommendations:
            print(restaurant)
    finally:
        db.close()

if __name__ == "__main__":
    example_usage()