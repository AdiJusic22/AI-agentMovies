from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Recommender(ABC):
    @abstractmethod
    def recommend(self, user_id: str, session_id: str, n: int = 10) -> List[Dict[str, Any]]:
        pass

class Learner(ABC):
    @abstractmethod
    def learn(self, event: Dict[str, Any]) -> None:
        pass

class Sensor(ABC):
    @abstractmethod
    def sense(self) -> Dict[str, Any]:
        pass

class Actuator(ABC):
    @abstractmethod
    def act(self, recommendations: List[Dict[str, Any]]) -> None:
        pass