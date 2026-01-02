from pydantic import BaseModel
from typing import Optional

class Event(BaseModel):
    user_id: str
    session_id: str
    event_type: str  # click, impression, rating
    item_id: str
    timestamp: str
    context: Optional[Dict[str, Any]] = {}

class Recommendation(BaseModel):
    item_id: str
    score: float
    reason: Optional[str] = None