from src.domain.interfaces import Recommender
from typing import List, Dict, Any

class DummyRecommender(Recommender):
    def recommend(self, user_id: str, session_id: str, n: int = 10) -> List[Dict[str, Any]]:
        # Dummy: return popular items
        return [
            {"item_id": f"item_{i}", "score": 1.0 - i*0.1, "reason": "Popular"}
            for i in range(n)
        ]