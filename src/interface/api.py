from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from src.application.orchestrator import Orchestrator
from src.infrastructure.recommender_impl import MLRecommender
from src.infrastructure.learner_impl import DummyLearner
from src.infrastructure.sensor_impl import DummySensor
from src.infrastructure.actuator_impl import DummyActuator

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency injection
def get_orchestrator():
    return Orchestrator(
        recommender=MLRecommender(),
        learner=DummyLearner(),
        sensor=DummySensor(),
        actuator=DummyActuator()
    )

@app.get("/")
def read_root():
    return {"message": "Personal Recommender Agent", "ui": "/static/index.html"}

@app.get("/recommend")
def recommend(user_id: str, session_id: str, orchestrator: Orchestrator = Depends(get_orchestrator)):
    try:
        return orchestrator.step(user_id, session_id)
    except Exception as e:
        return {"error": str(e)}

@app.post("/events")
def ingest_event(event: dict, orchestrator: Orchestrator = Depends(get_orchestrator)):
    orchestrator.learner.learn(event)
    return {"status": "ok"}