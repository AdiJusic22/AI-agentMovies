"""
Application service for event queue operations.
Keeps queue-related business logic out of the web layer.
"""
from typing import Dict, Any
from datetime import datetime
import uuid
from src.infrastructure.db import SessionLocal, EventModel


class EventQueueService:
    """Service for enqueueing events and reading queue stats."""

    def enqueue_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            event_model = EventModel(
                id=str(uuid.uuid4()),
                user_id=event.get('user_id', 'unknown'),
                user_name=event.get('name') or event.get('user_name'),
                session_id=event.get('session_id', 'unknown'),
                event_type=event.get('event_type', 'unknown'),
                item_id=event.get('item_id', ''),
                rating=event.get('rating'),
                mood=event.get('mood'),
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

    def get_queue_stats(self) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            pending_count = db.query(EventModel).filter(EventModel.status == 'pending').count()
            processing_count = db.query(EventModel).filter(EventModel.status == 'processing').count()
            processed_count = db.query(EventModel).filter(EventModel.status == 'processed').count()
            failed_count = db.query(EventModel).filter(EventModel.status == 'failed').count()
            return {
                "pending": pending_count,
                "processing": processing_count,
                "processed": processed_count,
                "failed": failed_count,
                "total": pending_count + processing_count + processed_count + failed_count
            }
        finally:
            db.close()
