from src.domain.interfaces import Learner
from src.infrastructure.db import SessionLocal, FeedbackModel
from typing import Dict, Any
from datetime import datetime

class DummyLearner(Learner):
    def learn(self, event: Dict[str, Any]) -> None:
        # Spremi feedback u DB
        db = SessionLocal()
        try:
            feedback = FeedbackModel(
                id=f"{event['user_id']}_{event['item_id']}_{datetime.now().isoformat()}",
                user_id=event['user_id'],
                item_id=event['item_id'],
                rating=event['rating'],
                session_id=event.get('session_id', ''),
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