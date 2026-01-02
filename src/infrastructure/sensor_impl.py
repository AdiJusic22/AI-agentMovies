from src.domain.interfaces import Sensor
from typing import Dict, Any

class DummySensor(Sensor):
    def sense(self) -> Dict[str, Any]:
        # Dummy: return mock event
        return {"user_id": "123", "event_type": "click"}