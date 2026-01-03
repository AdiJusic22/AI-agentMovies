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
        # Validate user_id
        user_id_int = int(user_id)
        if user_id_int not in orchestrator.recommender.ratings_matrix.index:
            return {"error": f"User {user_id} not found in dataset. Valid users: 1-610"}
        return orchestrator.step(user_id, session_id)
    except ValueError:
        return {"error": "Invalid user_id, must be integer"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/events")
def ingest_event(event: dict, orchestrator: Orchestrator = Depends(get_orchestrator)):
    orchestrator.learner.learn(event)
    return {"status": "ok"}

@app.post("/feedback")
def feedback(feedback_data: dict, orchestrator: Orchestrator = Depends(get_orchestrator)):
    # feedback_data: {"user_id": "1", "item_id": "296", "rating": 5, "session_id": "test"}
    # Spremi u DB i retrain model ako treba
    try:
        # Dodaj u learner
        orchestrator.learner.learn(feedback_data)
        # Retrain recommender (dummy za sada)
        orchestrator.recommender.update_model()  # Dodati metodu
        return {"status": "Feedback recorded and model updated"}
    except Exception as e:
        return {"error": str(e)}