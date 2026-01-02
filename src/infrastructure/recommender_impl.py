from src.domain.interfaces import Recommender
from sklearn.neighbors import NearestNeighbors
import pandas as pd
import numpy as np
import os

class MLRecommender(Recommender):
    def __init__(self):
        self.model = None
        self.ratings_matrix = None
        self.item_ids = None
        self._load_data()

    def _load_data(self):
        # Load MovieLens data
        data_path = 'data/ml-latest-small'
        if os.path.exists(data_path):
            ratings = pd.read_csv(f'{data_path}/ratings.csv')
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
            return [{"item_id": f"movie_{i}", "score": 1.0 - i*0.1, "reason": "Popular"} for i in range(n)]
        
        # For simplicity, recommend based on popular items or random
        # In real: use user history from DB
        popular_items = self.ratings_matrix.mean().sort_values(ascending=False).head(n)
        return [{"item_id": str(item_id), "score": score, "reason": "Popular"} for item_id, score in popular_items.items()]