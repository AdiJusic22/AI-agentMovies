from src.domain.interfaces import Actuator
from typing import List, Dict, Any

class DummyActuator(Actuator):
    def act(self, recommendations: List[Dict[str, Any]]) -> None:
        # Dummy: print recommendations
        print(f"Acting on recommendations: {recommendations}")