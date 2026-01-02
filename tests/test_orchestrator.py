import pytest
from src.application.orchestrator import Orchestrator
from src.infrastructure.recommender_impl import DummyRecommender
from src.infrastructure.learner_impl import DummyLearner
from src.infrastructure.sensor_impl import DummySensor
from src.infrastructure.actuator_impl import DummyActuator

def test_orchestrator_step():
    orchestrator = Orchestrator(
        recommender=DummyRecommender(),
        learner=DummyLearner(),
        sensor=DummySensor(),
        actuator=DummyActuator()
    )
    recommendations = orchestrator.step("user1", "session1")
    assert len(recommendations) == 10
    assert recommendations[0]["item_id"] == "item_0"