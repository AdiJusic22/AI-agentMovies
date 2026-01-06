from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
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

class FeedbackModel(Base):
    __tablename__ = 'feedback'
    id = Column(String, primary_key=True)
    user_name = Column(String)  # Ime korisnika (npr "Adi")
    item_id = Column(String)
    rating = Column(Integer)  # 1-5 (1-2=dislike, 4-5=like)
    mood = Column(String)  # happy, sad, angry, etc.
    timestamp = Column(DateTime)

engine = create_engine('sqlite:///data/feedback.db')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()