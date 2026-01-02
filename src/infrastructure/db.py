from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

class EventModel(Base):
    __tablename__ = 'events'
    id = Column(String, primary_key=True)
    user_id = Column(String)
    session_id = Column(String)
    event_type = Column(String)
    item_id = Column(String)
    timestamp = Column(DateTime)
    context = Column(Text)

engine = create_engine('sqlite:///data/events.db')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()