from src.domain.interfaces import Learner
from src.infrastructure.db import SessionLocal
from typing import Dict, Any

class DummyLearner(Learner):
    def learn(self, event: Dict[str, Any]) -> None:
        # Dummy: just log to console
        print(f"Learned from event: {event}")