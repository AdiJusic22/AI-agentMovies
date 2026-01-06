from src.domain.interfaces import Learner
from src.infrastructure.db import SessionLocal, FeedbackModel
from typing import Dict, Any
from datetime import datetime

class DummyLearner(Learner):
    def learn(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Save feedback; prevent duplicates per user_name + mood + item_id."""
        db = SessionLocal()
        try:
            existing = db.query(FeedbackModel).filter(
                FeedbackModel.user_name == event['name'],
                FeedbackModel.mood == event['mood'],
                FeedbackModel.item_id == event['item_id']
            ).first()

            if existing:
                # Do not duplicate; return existing rating
                return {"status": "exists", "rating": existing.rating}

            feedback = FeedbackModel(
                id=f"{event['name']}_{event['item_id']}_{event['mood']}_{datetime.now().isoformat()}",
                user_name=event['name'],
                item_id=event['item_id'],
                rating=event['rating'],
                mood=event['mood'],
                timestamp=datetime.now()
            )
            db.add(feedback)
            db.commit()
            print(f"Learned from feedback: {event}")
            return {"status": "created", "rating": event['rating']}
        except Exception as e:
            print(f"Error saving feedback: {e}")
            db.rollback()
            return {"status": "error", "error": str(e)}
        finally:
            db.close()