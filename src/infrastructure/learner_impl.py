from src.domain.interfaces import Learner
from src.infrastructure.db import SessionLocal, FeedbackModel
from typing import Dict, Any
from datetime import datetime

class DummyLearner(Learner):
    def learn(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Save feedback; prevent duplicates per user_name + mood + item_id."""
        db = SessionLocal()
        try:
            user_name = event.get('name') or event.get('user_name')
            mood = event.get('mood')
            item_id = event.get('item_id')
            rating = event.get('rating')

            if not user_name or not mood or not item_id or rating is None:
                return {"status": "error", "error": "Missing required feedback fields"}

            existing = db.query(FeedbackModel).filter(
                FeedbackModel.user_name == user_name,
                FeedbackModel.mood == mood,
                FeedbackModel.item_id == item_id
            ).first()

            if existing:
                # Do not duplicate; return existing rating
                return {"status": "exists", "rating": existing.rating}

            feedback = FeedbackModel(
                id=f"{user_name}_{item_id}_{mood}_{datetime.now().isoformat()}",
                user_name=user_name,
                item_id=item_id,
                rating=rating,
                mood=mood,
                timestamp=datetime.now()
            )
            db.add(feedback)
            db.commit()
            print(f"Learned from feedback: {event}")
            return {"status": "created", "rating": rating}
        except Exception as e:
            print(f"Error saving feedback: {e}")
            db.rollback()
            return {"status": "error", "error": str(e)}
        finally:
            db.close()