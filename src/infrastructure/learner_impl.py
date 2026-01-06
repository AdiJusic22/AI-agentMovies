from src.domain.interfaces import Learner
from src.infrastructure.db import SessionLocal, FeedbackModel
from typing import Dict, Any
from datetime import datetime

class DummyLearner(Learner):
    def learn(self, event: Dict[str, Any]) -> None:
        # Spremi feedback u DB sa user_name i mood
        db = SessionLocal()
        try:
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
        except Exception as e:
            print(f"Error saving feedback: {e}")
            db.rollback()
        finally:
            db.close()