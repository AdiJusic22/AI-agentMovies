from src.domain.interfaces import Recommender, Learner, Sensor, Actuator
from typing import List, Dict, Any, Optional

class Orchestrator:
    def __init__(self, recommender: Recommender, learner: Learner, sensor: Actuator, actuator: Actuator):
        self.recommender = recommender
        self.learner = learner
        self.sensor = sensor
        self.actuator = actuator

    def step(self, user_name: str, mood: str = "neutral") -> List[Dict[str, Any]]:
        """Called by HTTP endpoints - just returns recommendations"""
        # Think
        recommendations = self.recommender.recommend(user_name, mood)
        return recommendations

    def tick(self, event: Optional[Dict[str, Any]] = None) -> str:
        """
        Process one event from queue (called by background runner).
        Returns: 'NoWork' if no event, 'Processed' if event was processed.
        """
        if not event:
            return "NoWork"
        
        # Sense
        context_data = self.sensor.sense()
        
        # Think (use context data as fallback)
        user_name = event.get('user_name') or event.get('user_id') or context_data.get('user_id', 'unknown')
        mood = event.get('mood') or context_data.get('mood', 'neutral')
        recommendations = self.recommender.recommend(user_name, mood)
        
        # Act
        self.actuator.act(recommendations)
        
        # Learn (only when feedback fields exist)
        if event.get('rating') is not None and event.get('mood'):
            self.learner.learn(event)
        
        return "Processed"