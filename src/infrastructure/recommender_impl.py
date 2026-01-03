from src.domain.interfaces import Recommender
from sklearn.neighbors import NearestNeighbors
import pandas as pd
import numpy as np
import os
import openai

class MLRecommender(Recommender):
    def __init__(self):
        self.model = None
        self.ratings_matrix = None
        self.item_ids = None
        self.movies = None
        self._load_data()

    def _load_data(self):
        # Load MovieLens data
        data_path = 'data/ml-latest-small'
        if os.path.exists(data_path):
            ratings = pd.read_csv(f'{data_path}/ratings.csv')
            movies = pd.read_csv(f'{data_path}/movies.csv')
            self.movies = movies.set_index('movieId')['title'].to_dict()
            self.genres = movies.set_index('movieId')['genres'].to_dict()
            # Create user-item matrix
            self.ratings_matrix = ratings.pivot(index='userId', columns='movieId', values='rating').fillna(0)
            self.item_ids = self.ratings_matrix.columns.tolist()
            # Fit KNN model
            self.model = NearestNeighbors(n_neighbors=10, algorithm='brute', metric='cosine')
            self.model.fit(self.ratings_matrix.T)  # Item-based
        else:
            # Fallback to dummy
            pass

    def recommend(self, user_id: str, session_id: str, n: int = 10) -> list[dict[str, any]]:
        if self.model is None:
            # Dummy fallback
            return [{"item_id": f"movie_{i}", "title": f"Movie {i}", "genres": "", "score": 1.0 - i*0.1, "reason": "Popular", "llm_description": "A great movie!", "agent_mood": "Fallback mode – enjoy!"} for i in range(n)]
        
        # Simple user-based: recommend movies similar to user's top-rated
        try:
            user_id_int = int(user_id)
            if user_id_int in self.ratings_matrix.index:
                user_ratings = self.ratings_matrix.loc[user_id_int]
                if user_ratings.notna().any():
                    top_movie = user_ratings.idxmax()  # User's top-rated movie
                    if pd.notna(top_movie):
                        # Find similar movies using KNN
                        distances, indices = self.model.kneighbors(self.ratings_matrix.T.loc[[top_movie]], n_neighbors=n+1)
                        similar_movies = self.ratings_matrix.T.iloc[indices[0][1:]].index  # Skip self
                        return [
                            {
                                "item_id": str(movie_id),
                                "title": self.movies.get(int(movie_id), f"Movie {movie_id}"),
                                "genres": self.genres.get(int(movie_id), ""),
                                "score": self.ratings_matrix.loc[:, movie_id].mean(),  # Use mean rating as score
                                "reason": f"Similar to your top movie: {self.movies.get(int(top_movie), top_movie)}",
                                "llm_description": self.get_llm_description(self.movies.get(int(movie_id), f"Movie {movie_id}"), self.genres.get(int(movie_id), "")),
                                "agent_mood": "Excited to recommend this based on your taste!"
                            }
                            for movie_id in similar_movies
                        ]
        except (ValueError, KeyError):
            pass
        
        # Fallback to popular
        popular_items = self.ratings_matrix.mean().sort_values(ascending=False).head(n)
        return [
            {
                "item_id": str(item_id),
                "title": self.movies.get(int(item_id), f"Movie {item_id}"),
                "genres": self.genres.get(int(item_id), ""),
                "score": score,
                "reason": "Popular",
                "llm_description": self.get_llm_description(self.movies.get(int(item_id), f"Movie {item_id}"), self.genres.get(int(item_id), "")),
                "agent_mood": "These are crowd favorites – hope you like them!"
            }
            for item_id, score in popular_items.items()
        ]

    def update_model(self):
        # Dummy: retrain sa novim podacima (za sada samo reload)
        self._load_data()
        # U realnom: append new ratings i retrain KNN

    def get_llm_description(self, movie_title: str, genres: str) -> str:
        # Dummy LLM: opis filma
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a movie recommender AI. Describe why a user might like this movie based on title and genres. Keep it short."},
                    {"role": "user", "content": f"Movie: {movie_title}, Genres: {genres}"}
                ]
            )
            return response.choices[0].message.content
        except:
            return f"This {genres.lower()} movie '{movie_title}' is highly rated and might appeal to fans of similar films."