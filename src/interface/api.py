from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from src.application.orchestrator import Orchestrator
from src.application.runner import BackgroundRunner
from src.infrastructure.recommender_impl import MLRecommender
from src.infrastructure.learner_impl import DummyLearner
from src.infrastructure.sensor_impl import DummySensor
from src.infrastructure.actuator_impl import DummyActuator
from src.infrastructure.db import SessionLocal, FeedbackModel, EventModel
from collections import Counter
from typing import Optional
import asyncio
from datetime import datetime
import uuid

app = FastAPI()

# Global runner instance
runner: Optional[BackgroundRunner] = None

@app.on_event("startup")
async def startup_event():
    """Start the background runner on application startup."""
    global runner
    orchestrator = Orchestrator(
        recommender=MLRecommender(),
        learner=DummyLearner(),
        sensor=DummySensor(),
        actuator=DummyActuator()
    )
    runner = BackgroundRunner(orchestrator, tick_interval=5.0)
    # Start runner in background
    asyncio.create_task(runner.run())

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the background runner on application shutdown."""
    global runner
    if runner:
        runner.stop()

@app.get("/")
def read_root():
    return RedirectResponse(url="/static/index.html")

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Dependency injection
def get_orchestrator():
    return Orchestrator(
        recommender=MLRecommender(),
        learner=DummyLearner(),
        sensor=DummySensor(),
        actuator=DummyActuator()
    )



@app.get("/recommend")
def recommend(name: str, mood: str = "neutral", orchestrator: Orchestrator = Depends(get_orchestrator)):
    try:
        if not name or len(name.strip()) == 0:
            return {"error": "Name is required"}
        return orchestrator.step(name.strip(), mood)
    except Exception as e:
        return {"error": str(e)}

@app.post("/events")
def ingest_event(event: dict):
    """
    Ingest event into the queue for background processing.
    Events are stored as 'pending' and will be processed by the runner.
    """
    db = SessionLocal()
    try:
        event_model = EventModel(
            id=str(uuid.uuid4()),
            user_id=event.get('user_id', 'unknown'),
            session_id=event.get('session_id', 'unknown'),
            event_type=event.get('event_type', 'unknown'),
            item_id=event.get('item_id', ''),
            timestamp=datetime.now(),
            context=str(event.get('context', {})),
            status='pending'
        )
        db.add(event_model)
        db.commit()
        return {"status": "queued", "event_id": event_model.id}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

@app.post("/feedback")
def feedback(feedback_data: dict, orchestrator: Orchestrator = Depends(get_orchestrator)):
    # feedback_data: {"name": "Adi", "item_id": "296", "rating": 5, "mood": "happy"}
    try:
        # Dodaj u learner
        result = orchestrator.learner.learn(feedback_data)
        if result.get("status") == "exists":
            return {"status": "already_rated", "rating": result.get("rating")}
        if result.get("status") == "error":
            return {"error": result.get("error", "Unknown error")}
        # Retrain recommender
        orchestrator.recommender.update_model()
        return {"status": "Feedback recorded and model updated", "rating": result.get("rating")}
    except Exception as e:
        return {"error": str(e)}

@app.get("/stats")
def get_stats(name: str):
    """Get user statistics: liked, disliked, favorite mood, favorite genre"""
    db = SessionLocal()
    try:
        # Get all feedback for user
        feedbacks = db.query(FeedbackModel).filter(FeedbackModel.user_name == name).all()
        
        if not feedbacks:
            return {
                "user_name": name,
                "total_feedback": 0,
                "liked_count": 0,
                "disliked_count": 0,
                "favorite_mood": None,
                "moods": {}
            }
        
        # Calculate stats
        liked = [f for f in feedbacks if f.rating >= 4]
        disliked = [f for f in feedbacks if f.rating <= 2]
        
        # Count moods
        mood_counts = Counter(f.mood for f in feedbacks)
        favorite_mood = mood_counts.most_common(1)[0][0] if mood_counts else None
        
        return {
            "user_name": name,
            "total_feedback": len(feedbacks),
            "liked_count": len(liked),
            "disliked_count": len(disliked),
            "favorite_mood": favorite_mood,
            "moods": dict(mood_counts)
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@app.get("/ratings")
def get_ratings(name: str, mood: Optional[str] = None):
    """Vrati listu sacuvanih ocjena za korisnika; opcionalno filtriraj po raspolozenju."""
    db = SessionLocal()
    try:
        query = db.query(FeedbackModel).filter(FeedbackModel.user_name == name)
        if mood:
            query = query.filter(FeedbackModel.mood == mood)
        feedbacks = query.all()
        return {
            "ratings": [
                {
                    "item_id": f.item_id,
                    "rating": f.rating,
                    "mood": f.mood,
                    "timestamp": f.timestamp.isoformat() if f.timestamp else None,
                }
                for f in feedbacks
            ]
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@app.get("/runner/stats")
def get_runner_stats():
    """Get background runner statistics."""
    global runner
    if not runner:
        return {"error": "Runner not initialized"}
    return runner.get_stats()


@app.get("/runner/events")
def get_pending_events():
    """Get count of pending events in queue."""
    db = SessionLocal()
    try:
        pending_count = db.query(EventModel).filter(EventModel.status == 'pending').count()
        processed_count = db.query(EventModel).filter(EventModel.status == 'processed').count()
        return {
            "pending": pending_count,
            "processed": processed_count,
            "total": pending_count + processed_count
        }
    finally:
        db.close()