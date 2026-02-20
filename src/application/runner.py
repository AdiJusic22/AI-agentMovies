"""
Background runner/worker for autonomous agent operation.
Implements the tick loop: periodically processes events from queue.
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime
from src.application.orchestrator import Orchestrator
from src.infrastructure.db import SessionLocal, EventModel
from sqlalchemy import and_

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackgroundRunner:
    """
    Autonomous background worker that processes events from the queue.
    Runs continuously and implements NoWork behavior when queue is empty.
    """
    
    def __init__(self, orchestrator: Orchestrator, tick_interval: float = 5.0):
        """
        Args:
            orchestrator: The orchestrator to use for processing events
            tick_interval: Seconds between ticks (default 5s)
        """
        self.orchestrator = orchestrator
        self.tick_interval = tick_interval
        self.running = False
        self.total_processed = 0
        self.total_no_work = 0
    
    def get_next_event(self) -> Optional[dict]:
        """
        Fetch the next pending event from the database queue.
        Returns None if no events available.
        """
        db = SessionLocal()
        try:
            event = db.query(EventModel).filter(
                EventModel.status == 'pending'
            ).order_by(EventModel.timestamp).first()
            
            if event:
                # Mark as processing
                event.status = 'processing'
                db.commit()
                
                # Convert to dict
                return {
                    'id': event.id,
                    'user_id': event.user_id,
                    'user_name': event.user_name or event.user_id,
                    'session_id': event.session_id,
                    'event_type': event.event_type,
                    'item_id': event.item_id,
                    'rating': event.rating,
                    'mood': event.mood or 'neutral',
                    'timestamp': event.timestamp,
                    'context': event.context,
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching event: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    async def tick(self):
        """
        Execute one tick of the agent cycle:
        1. Get next event from queue
        2. If no event → return NoWork
        3. If event exists → process via orchestrator
        """
        event = self.get_next_event()
        
        if not event:
            self.total_no_work += 1
            result = "NoWork"
            logger.debug(f"Tick: {result} (total no-work: {self.total_no_work})")
        else:
            try:
                result = self.orchestrator.tick(event)
                self._mark_event_status(event['id'], 'processed')
                self.total_processed += 1
                logger.info(f"Tick: {result} - Event {event['id']} (total processed: {self.total_processed})")
            except Exception as e:
                self._mark_event_status(event['id'], 'failed')
                logger.error(f"Error processing event {event['id']}: {e}")
                result = "Failed"
        
        return result

    def _mark_event_status(self, event_id: str, status: str) -> None:
        db = SessionLocal()
        try:
            event = db.query(EventModel).filter(EventModel.id == event_id).first()
            if event:
                event.status = status
                db.commit()
        except Exception as e:
            logger.error(f"Error updating event status {event_id} -> {status}: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def run(self):
        """
        Main loop: continuously tick until stopped.
        Implements sleep during NoWork to avoid CPU waste.
        """
        self.running = True
        logger.info(f"Background runner started (tick interval: {self.tick_interval}s)")
        
        while self.running:
            try:
                result = await self.tick()
                
                # If NoWork, sleep longer to avoid wasting resources
                if result == "NoWork":
                    await asyncio.sleep(self.tick_interval)
                else:
                    # If processing, shorter sleep for responsiveness
                    await asyncio.sleep(1.0)
                    
            except Exception as e:
                logger.error(f"Error in runner loop: {e}", exc_info=True)
                await asyncio.sleep(self.tick_interval)
    
    def stop(self):
        """Stop the runner gracefully."""
        logger.info(f"Stopping runner (processed: {self.total_processed}, no-work: {self.total_no_work})")
        self.running = False
    
    def get_stats(self) -> dict:
        """Get runner statistics."""
        return {
            "running": self.running,
            "total_processed": self.total_processed,
            "total_no_work": self.total_no_work,
            "tick_interval": self.tick_interval
        }
