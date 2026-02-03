"""
Application services for handling feedback and statistics.
This layer contains business logic that was previously in the web layer.
"""
from typing import Dict, Any, List
from collections import Counter
from src.infrastructure.db import SessionLocal, FeedbackModel
from src.domain.interfaces import Recommender, Learner


class FeedbackService:
    """
    Service for handling user feedback operations.
    Encapsulates business logic for feedback processing and statistics.
    """
    
    def __init__(self, recommender: Recommender, learner: Learner):
        self.recommender = recommender
        self.learner = learner
    
    def process_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user feedback: save to database and trigger model update.
        
        Args:
            feedback_data: {"name": str, "item_id": str, "rating": int, "mood": str}
        
        Returns:
            Result dictionary with status and rating
        """
        # Validate feedback_data
        if not feedback_data.get('name'):
            return {"error": "Name is required"}
        if not feedback_data.get('item_id'):
            return {"error": "Item ID is required"}
        if 'rating' not in feedback_data:
            return {"error": "Rating is required"}
        
        # Save feedback via learner
        result = self.learner.learn(feedback_data)
        
        # Handle duplicate/error cases
        if result.get("status") == "exists":
            return {"status": "already_rated", "rating": result.get("rating")}
        if result.get("status") == "error":
            return {"error": result.get("error", "Unknown error")}
        
        # Trigger model update (business logic)
        self.recommender.update_model()
        
        return {
            "status": "Feedback recorded and model updated",
            "rating": result.get("rating")
        }
    
    def get_user_statistics(self, user_name: str) -> Dict[str, Any]:
        """
        Get aggregated statistics for a user.
        
        Args:
            user_name: Name of the user
        
        Returns:
            Dictionary with user statistics
        """
        db = SessionLocal()
        try:
            # Fetch all feedback for user
            feedbacks = db.query(FeedbackModel).filter(
                FeedbackModel.user_name == user_name
            ).all()
            
            # No feedback case
            if not feedbacks:
                return {
                    "user_name": user_name,
                    "total_feedback": 0,
                    "liked_count": 0,
                    "disliked_count": 0,
                    "favorite_mood": None,
                    "moods": {}
                }
            
            # Calculate aggregations (business logic)
            liked = [f for f in feedbacks if f.rating >= 4]
            disliked = [f for f in feedbacks if f.rating <= 2]
            
            # Count moods
            mood_counts = Counter(f.mood for f in feedbacks)
            favorite_mood = mood_counts.most_common(1)[0][0] if mood_counts else None
            
            return {
                "user_name": user_name,
                "total_feedback": len(feedbacks),
                "liked_count": len(liked),
                "disliked_count": len(disliked),
                "favorite_mood": favorite_mood,
                "moods": dict(mood_counts)
            }
        finally:
            db.close()
    
    def get_user_ratings(self, user_name: str, mood: str = None) -> Dict[str, Any]:
        """
        Get user's ratings, optionally filtered by mood.
        
        Args:
            user_name: Name of the user
            mood: Optional mood filter
        
        Returns:
            Dictionary with ratings list
        """
        db = SessionLocal()
        try:
            query = db.query(FeedbackModel).filter(FeedbackModel.user_name == user_name)
            
            if mood:
                query = query.filter(FeedbackModel.mood == mood)
            
            feedbacks = query.all()
            
            return {
                "ratings": [
                    {
                        "item_id": f.item_id,
                        "rating": f.rating,
                        "mood": f.mood,
                        "timestamp": f.timestamp.isoformat() if f.timestamp else None,
                    }
                    for f in feedbacks
                ]
            }
        finally:
            db.close()
