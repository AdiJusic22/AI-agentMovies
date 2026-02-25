from src.domain.interfaces import Recommender
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
import os
from src.infrastructure.db import SessionLocal, FeedbackModel

class MLRecommender(Recommender):
    def __init__(self):
        self.model = None
        self.ratings_matrix = None
        self.model_item_ids = None  # Čuva item_ids koji su korišteni pri treniranju modela
        self.user_ratings = {}  # user_name -> {item_id: rating}
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
        data_path = 'data/ml-latest-small'
        if os.path.exists(data_path):
            ratings = pd.read_csv(f'{data_path}/ratings.csv')
            movies = pd.read_csv(f'{data_path}/movies.csv')
            self.movies = movies.set_index('movieId')['title'].to_dict()
            self.genres = movies.set_index('movieId')['genres'].to_dict()
            self.years = {}
            for _, row in movies.iterrows():
                title = row['title']
                if '(' in title and title.endswith(')'):
                    try:
                        year = int(title.split('(')[-1].strip(')'))
                        self.years[row['movieId']] = year
                    except:
                        self.years[row['movieId']] = None
                else:
                    self.years[row['movieId']] = None
            self.ratings_matrix = ratings.pivot(index='userId', columns='movieId', values='rating').fillna(0)
            # Sačuva item_ids samo iz ratings CSV-a (KONSTANTNO)
            if self.item_ids is None:
                self.item_ids = self.ratings_matrix.columns.tolist()
                self.model_item_ids = list(self.item_ids)  # Inicijalni model koristi iste item_ids
            
            # Učitaj feedback-e iz baze i dodaj kao nove redove
            self._load_feedback_ratings()
            
            # Retrain KNN sa feedback rows ali sa ISTIM columns kao originalni ratings_matrix
            if not self.ratings_matrix.empty and len(self.ratings_matrix) > 0:
                # KNN radi sa transponiranom matricom (movies kao features, users kao data points)
                self.model = NearestNeighbors(
                    n_neighbors=min(3, max(1, len(self.ratings_matrix) - 1)), 
                    algorithm='brute', 
                    metric='cosine'
                )
                # Transpose jer trebamo movies kao kolone (features)
                self.model.fit(self.ratings_matrix.T.values)
                print(f"[ML] Model initialized. Matrix shape: {self.ratings_matrix.shape}, Features: {len(self.model_item_ids)}")
        else:
            pass
    
    def _load_feedback_ratings(self):
        """Učitaj sve feedback-e iz baze i dodaj kao nove redove u rating matricu."""
        db = SessionLocal()
        try:
            feedbacks = db.query(FeedbackModel).all()
            feedback_by_user = {}
            for fb in feedbacks:
                if fb.user_name not in feedback_by_user:
                    feedback_by_user[fb.user_name] = {}
                feedback_by_user[fb.user_name][int(fb.item_id)] = fb.rating
                if fb.user_name not in self.user_ratings:
                    self.user_ratings[fb.user_name] = {}
                self.user_ratings[fb.user_name][int(fb.item_id)] = fb.rating
            
            # Dodaj user feedback-e kao nove redove u matricu
            for user_name, ratings_dict in feedback_by_user.items():
                # Koristi SAMO item_ids koji su u ratings_matrix (ne pravi nove kolone)
                user_vector = [ratings_dict.get(item_id, 0) for item_id in self.item_ids]
                # Koristi unique index (ne user_name koji može biti dupliciran)
                unique_index = f"user_{user_name}"
                if unique_index not in self.ratings_matrix.index:
                    # Kreiraj novi red sa eksplicitnom listom kolona
                    self.ratings_matrix.loc[unique_index] = 0  # Inicijalizuj sa 0
                    for i, item_id in enumerate(self.item_ids):
                        self.ratings_matrix.loc[unique_index, item_id] = user_vector[i]
                else:
                    for i, item_id in enumerate(self.item_ids):
                        self.ratings_matrix.loc[unique_index, item_id] = user_vector[i]
        except Exception as e:
            print(f"[ML] Error loading feedback ratings: {e}")
        finally:
            db.close()

    def recommend(self, user_name: str, mood: str = "neutral", n: int = 10) -> list[dict[str, any]]:
        """
        Pravi collaborative filtering preporuke:
        1. Prvo prikaži liked filmove za ovaj mood
        2. Pronađi slične korisnike (KNN na osnovu rating history)
        3. Prikaži filmove koje su slični korisnici su dali visokim ocjenama
        4. Fallback: popularne filmove
        5. Filter po mood-u
        """
        if self.model is None or self.ratings_matrix is None or self.ratings_matrix.empty:
            return [{"item_id": f"movie_{i}", "title": f"Movie {i}", "year": "Unknown", "genres": "", "score": 1.0 - i*0.1, "reason": "Popular", "llm_description": "A great movie!", "agent_mood": "Fallback mode – enjoy!"} for i in range(n)]
        
        results = []
        
        # 1. Prikaži prvo liked filmove za ovaj mood
        liked = self._get_liked_movies(user_name, mood)
        disliked = self._get_disliked_movies_by_name(user_name, mood)
        
        for movie_id in liked[:n]:
            results.append({
                "item_id": str(movie_id),
                "title": self.movies.get(int(movie_id), f"Movie {movie_id}"),
                "year": self.years.get(int(movie_id), "Unknown"),
                "genres": self.genres.get(int(movie_id), ""),
                "score": 5.0,
                "reason": "You liked this before!",
                "llm_description": self.get_llm_description(self.movies.get(int(movie_id), f"Movie {movie_id}"), self.genres.get(int(movie_id), "")),
                "agent_mood": "You loved this one!"
            })
        
        if len(results) < n:
            # 2. Collaborative filtering: pronađi slične korisnike
            remaining = n - len(results)
            user_recommendations = self._get_collaborative_recommendations(user_name, liked, disliked, remaining, mood)
            results.extend(user_recommendations)
        
        if len(results) < n:
            # 3. FALLBACK: popularne preporuke za mood
            remaining = n - len(results)
            popular_recs = self._get_popular_recommendations(liked, disliked, remaining, mood)
            results.extend(popular_recs)
        
        return results[:n]
    
    def _get_popular_recommendations(self, liked: list, disliked: list, count: int, mood: str) -> list[dict]:
        """Dohvati popularne filmove kao fallback preporuke."""
        recommendations = []
        try:
            popular_items = self.ratings_matrix.mean().sort_values(ascending=False)
            popular_items = popular_items[~popular_items.index.isin(liked + disliked)]
            movie_ids = list(popular_items.index)
            
            # Filter po mood-u
            for movie_id in movie_ids:
                if len(recommendations) >= count:
                    break
                movie_genres = self.genres.get(int(movie_id), "").split("|")
                if self._matches_mood(movie_genres, mood):
                    recommendations.append({
                        "item_id": str(movie_id),
                        "title": self.movies.get(int(movie_id), f"Movie {movie_id}"),
                        "year": self.years.get(int(movie_id), "Unknown"),
                        "genres": self.genres.get(int(movie_id), ""),
                        "score": popular_items.get(movie_id, 0),
                        "reason": "Popular recommendation for your mood",
                        "llm_description": self.get_llm_description(self.movies.get(int(movie_id), f"Movie {movie_id}"), self.genres.get(int(movie_id), "")),
                        "agent_mood": "Trending now!"
                    })
        except Exception as e:
            print(f"[ML] Error in popular recommendations: {e}")
        
        return recommendations[:count]
    
    def _get_collaborative_recommendations(self, user_name: str, liked: list, disliked: list, count: int, mood: str) -> list[dict]:
        """
        Koristi cosine similarity da pronađe slične korisnike.
        Ne koristi KNN jer se matrica dinamički mijenja sa novim feedback-ima.
        """
        recommendations = []
        try:
            if not self.model_item_ids or not self.ratings_matrix.size:
                return recommendations
            
            # Kreiraj user vector za trenutnog korisnika
            unique_user_index = f"user_{user_name}"
            if unique_user_index in self.ratings_matrix.index:
                user_vector = self.ratings_matrix.loc[unique_user_index].values
            else:
                # Ako korisnik nije u matrici, kreiraj vektor od liked/disliked
                user_vector = np.zeros(len(self.model_item_ids))
                for item in liked:
                    if item in self.model_item_ids:
                        user_vector[self.model_item_ids.index(item)] = 5.0
                for item in disliked:
                    if item in self.model_item_ids:
                        user_vector[self.model_item_ids.index(item)] = 1.0
            
            # Izračunaj cosine similarity sa svim korisnicima
            similarities = cosine_similarity([user_vector], self.ratings_matrix.values)[0]
            
            # Pronađi top slične korisnike (ne tog korisnika samog)
            sorted_indices = np.argsort(similarities)[::-1]
            
            # Prikupli preporuke od sličnihusers
            similar_users_recommendations = {}
            top_n = min(5, len(sorted_indices))
            
            for idx in sorted_indices[1:top_n]:  # Preskoči prvog (to je sam korisnik/najbliži)
                if idx < len(self.ratings_matrix):
                    similar_user_ratings = self.ratings_matrix.iloc[idx]
                    for movie_id, rating in similar_user_ratings.items():
                        if rating >= 4 and movie_id not in liked and movie_id not in disliked:
                            if movie_id not in similar_users_recommendations:
                                similar_users_recommendations[movie_id] = []
                            similar_users_recommendations[movie_id].append(rating)
            
            # Sortiraj po prosjeku rating-a od sličnih korisnika
            sorted_recs = sorted(
                similar_users_recommendations.items(),
                key=lambda x: np.mean(x[1]),
                reverse=True
            )
            
            # Filter po mood-u i kreiraj rezultate
            for movie_id, ratings in sorted_recs[:count * 2]:
                movie_genres = self.genres.get(int(movie_id), "").split("|")
                if self._matches_mood(movie_genres, mood):
                    recommendations.append({
                        "item_id": str(movie_id),
                        "title": self.movies.get(int(movie_id), f"Movie {movie_id}"),
                        "year": self.years.get(int(movie_id), "Unknown"),
                        "genres": self.genres.get(int(movie_id), ""),
                        "score": np.mean(ratings),
                        "reason": f"Similar users loved this",
                        "llm_description": self.get_llm_description(self.movies.get(int(movie_id), f"Movie {movie_id}"), self.genres.get(int(movie_id), "")),
                        "agent_mood": "⭐ Based on your taste!"
                    })
                    if len(recommendations) >= count:
                        break
        except Exception as e:
            print(f"[ML] Error in collaborative recommendations: {e}")
        
        return recommendations[:count]
    
    def _matches_mood(self, movie_genres: list, mood: str) -> bool:
        """Provjeri da li filmske žanre odgovaraju mood-u."""
        if mood == "neutral":
            return True
        target_genres = self.mood_genres.get(mood, [])
        return any(g in target_genres for g in movie_genres)

    def update_model(self):
        """
        Update model by reloading feedback ratings.
        Cosine similarity ne zahteva retrain - jednostavno učitaj nove feedback-e.
        """
        print("[ML] Updating model with new feedback...")
        self.user_ratings.clear()
        self._load_feedback_ratings()
        print(f"[ML] Model updated. Matrix shape: {self.ratings_matrix.shape}, Users: {len(self.ratings_matrix)}")

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
    
    def _get_liked_movies(self, user_name: str, mood: str) -> list:
        """Dohvati lajkovane filmove za user-a i mood (rating >= 4), sortirano po vremenu"""
        db = SessionLocal()
        try:
            feedbacks = db.query(FeedbackModel).filter(
                FeedbackModel.user_name == user_name,
                FeedbackModel.mood == mood,
                FeedbackModel.rating >= 4
            ).order_by(FeedbackModel.timestamp.desc()).all()
            return [int(fb.item_id) for fb in feedbacks]
        except Exception as e:
            print(f"Error getting liked movies: {e}")
            return []
        finally:
            db.close()
    
    def _get_disliked_movies_by_name(self, user_name: str, mood: str) -> list:
        """Dohvati dislajkovane filmove za user-a i mood (rating <= 2)"""
        db = SessionLocal()
        try:
            feedbacks = db.query(FeedbackModel).filter(
                FeedbackModel.user_name == user_name,
                FeedbackModel.mood == mood,
                FeedbackModel.rating <= 2
            ).all()
            return [int(fb.item_id) for fb in feedbacks]
        except Exception as e:
            print(f"Error getting disliked movies: {e}")
            return []
        finally:
            db.close()