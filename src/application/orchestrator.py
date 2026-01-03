from src.domain.interfaces import Recommender, Learner, Sensor, Actuator

class Orchestrator:
    def __init__(self, recommender: Recommender, learner: Learner, sensor: Sensor, actuator: Actuator):
        self.recommender = recommender
        self.learner = learner
        self.sensor = sensor
        self.actuator = actuator

    def step(self, user_id: str, session_id: str, mood: str = "neutral") -> List[Dict[str, Any]]:
        # Sense
        data = self.sensor.sense()
        # Think
        recommendations = self.recommender.recommend(user_id, session_id, mood)
        # Act
        self.actuator.act(recommendations)
        # Learn (from data)
        self.learner.learn(data)
        return recommendations