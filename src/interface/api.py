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
def recommend(name: str, mood: str = "neutral", orchestrator: Orchestrator = Depends(get_orchestrator)):
    try:
        if not name or len(name.strip()) == 0:
            return {"error": "Name is required"}
        return orchestrator.step(name.strip(), mood)
    except Exception as e:
        return {"error": str(e)}

@app.post("/events")
def ingest_event(event: dict, orchestrator: Orchestrator = Depends(get_orchestrator)):
    orchestrator.learner.learn(event)
    return {"status": "ok"}

@app.post("/feedback")
def feedback(feedback_data: dict, orchestrator: Orchestrator = Depends(get_orchestrator)):
    # feedback_data: {"name": "Adi", "item_id": "296", "rating": 5, "mood": "happy"}
    try:
        # Dodaj u learner
        orchestrator.learner.learn(feedback_data)
        # Retrain recommender
        orchestrator.recommender.update_model()
        return {"status": "Feedback recorded and model updated"}
    except Exception as e:
        return {"error": str(e)}