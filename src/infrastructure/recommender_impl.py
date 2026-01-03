from src.domain.interfaces import Recommender
from sklearn.neighbors import NearestNeighbors
import pandas as pd
import numpy as np
import os
from src.infrastructure.db import SessionLocal, FeedbackModel
# import openai  # Removed for now

class MLRecommender(Recommender):
    def __init__(self):
        self.model = None
        self.ratings_matrix = None
        self.item_ids = None
        self.movies = None
        self.genres = None
        self.mood_genres = {
            "happy": ["Comedy", "Animation", "Musical"],
            "sad": ["Drama", "Romance"],
            "angry": ["Action", "Thriller", "Crime"],
            "excited": ["Adventure", "Sci-Fi", "Fantasy"],
            "relaxed": ["Documentary", "Family"],
            "scared": ["Horror"],
            "neutral": []  # All genres
        }
        self._load_data()

    def _load_data(self):
        # Load MovieLens data
        data_path = 'data/ml-latest-small'
        if os.path.exists(data_path):
            ratings = pd.read_csv(f'{data_path}/ratings.csv')
            movies = pd.read_csv(f'{data_path}/movies.csv')
            self.movies = movies.set_index('movieId')['title'].to_dict()
            self.genres = movies.set_index('movieId')['genres'].to_dict()
            self.years = {}
            for _, row in movies.iterrows():
                title = row['title']
                # Extract year from title, e.g., "Toy Story (1995)" -> 1995
                if '(' in title and title.endswith(')'):
                    try:
                        year = int(title.split('(')[-1].strip(')'))
                        self.years[row['movieId']] = year
                    except:
                        self.years[row['movieId']] = None
                else:
                    self.years[row['movieId']] = None
            # Create user-item matrix
            self.ratings_matrix = ratings.pivot(index='userId', columns='movieId', values='rating').fillna(0)
            self.item_ids = self.ratings_matrix.columns.tolist()            # Load feedback from DB and add to matrix
            db = SessionLocal()
            try:
                feedbacks = db.query(FeedbackModel).all()
                for fb in feedbacks:
                    user_id = int(fb.user_id)
                    movie_id = int(fb.item_id)
                    if user_id in self.ratings_matrix.index and movie_id in self.ratings_matrix.columns:
                        self.ratings_matrix.loc[user_id, movie_id] = fb.rating
            except Exception as e:
                print(f"Error loading feedback: {e}")
            finally:
                db.close()            # Fit KNN model
            self.model = NearestNeighbors(n_neighbors=10, algorithm='brute', metric='cosine')
            self.model.fit(self.ratings_matrix.T)  # Item-based
        else:
            # Fallback to dummy
            pass

    def recommend(self, user_id: str, session_id: str, mood: str = "neutral", n: int = 10) -> list[dict[str, any]]:
        if self.model is None:
            # Dummy fallback
            return [{"item_id": f"movie_{i}", "title": f"Movie {i}", "year": "Unknown", "genres": "", "score": 1.0 - i*0.1, "reason": "Popular", "llm_description": "A great movie!", "agent_mood": "Fallback mode – enjoy!"} for i in range(n)]
        
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
                        # Filter out disliked
                        similar_movies = [m for m in similar_movies if m not in disliked][:n]
                        # Filter by mood
                        similar_movies = self._filter_by_mood(similar_movies, mood)
                        return [
                            {
                                "item_id": str(movie_id),
                                "title": self.movies.get(int(movie_id), f"Movie {movie_id}"),
                                "year": self.years.get(int(movie_id), "Unknown"),
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
        
        # Fallback to popular, filter disliked
        disliked = self._get_disliked_movies(user_id)
        popular_items = self.ratings_matrix.mean().sort_values(ascending=False)
        popular_items = popular_items[~popular_items.index.isin(disliked)].head(n*2)  # More to filter
        movie_ids = list(popular_items.index)
        movie_ids = self._filter_by_mood(movie_ids, mood)
        return [
            {
                "item_id": str(item_id),
                "title": self.movies.get(int(item_id), f"Movie {item_id}"),
                "year": self.years.get(int(item_id), "Unknown"),
                "genres": self.genres.get(int(item_id), ""),
                "score": popular_items.get(item_id, 0),
                "reason": "Popular",
                "llm_description": self.get_llm_description(self.movies.get(int(item_id), f"Movie {item_id}"), self.genres.get(int(item_id), "")),
                "agent_mood": "These are crowd favorites – hope you like them!"
            }
            for item_id in movie_ids
        ]

    def update_model(self):
        # Dummy: retrain sa novim podacima (za sada samo reload)
        self._load_data()
        # U realnom: append new ratings i retrain KNN

    def get_llm_description(self, movie_title: str, genres: str) -> str:
        # Dummy LLM: opis filma bez API
        return f"This {genres.lower()} movie '{movie_title}' is highly rated and might appeal to fans of similar films."

    def _filter_by_mood(self, movie_ids: list, mood: str) -> list:
        if mood == "neutral":
            return movie_ids
        target_genres = self.mood_genres.get(mood, [])
        filtered = []
        for mid in movie_ids:
            movie_genres = self.genres.get(int(mid), "").split("|")
            if any(g in target_genres for g in movie_genres):
                filtered.append(mid)
        return filtered[:10]  # Limit to 10