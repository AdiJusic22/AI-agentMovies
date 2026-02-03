from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from src.application.orchestrator import Orchestrator
from src.application.runner import BackgroundRunner
from src.application.feedback_service import FeedbackService
from src.infrastructure.recommender_impl import MLRecommender
from src.infrastructure.learner_impl import DummyLearner
from src.infrastructure.sensor_impl import DummySensor
from src.infrastructure.actuator_impl import DummyActuator
from src.infrastructure.db import SessionLocal, FeedbackModel, EventModel
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

def get_feedback_service():
    return FeedbackService(
        recommender=MLRecommender(),
        learner=DummyLearner()
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
def feedback(feedback_data: dict, service: FeedbackService = Depends(get_feedback_service)):
    """
    Thin web layer: receive feedback, delegate to service, return response.
    All business logic is in FeedbackService.
    """
    return service.process_feedback(feedback_data)

@app.get("/stats")
def get_stats(name: str, service: FeedbackService = Depends(get_feedback_service)):
    """
    Thin web layer: receive request, delegate to service, return response.
    All business logic (aggregation, counting) is in FeedbackService.
    """
    return service.get_user_statistics(name)


@app.get("/ratings")
def get_ratings(name: str, mood: Optional[str] = None, service: FeedbackService = Depends(get_feedback_service)):
    """
    Thin web layer: receive request, delegate to service, return response.
    All business logic is in FeedbackService.
    """
    return service.get_user_ratings(name, mood)


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