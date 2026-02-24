from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from src.application.orchestrator import Orchestrator
from src.application.runner import BackgroundRunner
from src.application.feedback_service import FeedbackService
from src.application.event_service import EventQueueService
from src.infrastructure.recommender_impl import MLRecommender
from src.infrastructure.learner_impl import DummyLearner
from src.infrastructure.sensor_impl import DummySensor
from src.infrastructure.actuator_impl import DummyActuator
from typing import Optional
import asyncio

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

def get_event_service():
    return EventQueueService()



@app.get("/recommend")
def recommend(name: str, mood: str = "neutral", orchestrator: Orchestrator = Depends(get_orchestrator)):
    try:
        if not name or len(name.strip()) == 0:
            return {"error": "Name is required"}
        return orchestrator.step(name.strip(), mood)
    except Exception as e:
        return {"error": str(e)}

@app.post("/events")
def ingest_event(event: dict, service: EventQueueService = Depends(get_event_service)):
    """
    Ingest event into the queue for background processing.
    Events are stored as 'pending' and will be processed by the runner.
    """
    return service.enqueue_event(event)

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
def get_pending_events(service: EventQueueService = Depends(get_event_service)):
    """Get count of pending events in queue."""
    return service.get_queue_stats()