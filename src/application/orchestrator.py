from src.domain.interfaces import Recommender, Learner, Sensor, Actuator
from typing import List, Dict, Any

class Orchestrator:
    def __init__(self, recommender: Recommender, learner: Learner, sensor: Sensor, actuator: Actuator):
        self.recommender = recommender
        self.learner = learner
        self.sensor = sensor
        self.actuator = actuator

    def step(self, user_name: str, mood: str = "neutral") -> List[Dict[str, Any]]:
        # Sense
        data = self.sensor.sense()
        # Think
        recommendations = self.recommender.recommend(user_name, mood)
        # Act
        self.actuator.act(recommendations)
        # Learn (from data)
        self.learner.learn(data)
        return recommendations