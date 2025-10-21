from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://soundscout:soundscout@localhost:5432/soundscout")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Track(Base):
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    soundcloud_id = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    artist = Column(String, index=True)
    duration = Column(Float)
    url = Column(String)
    waveform_url = Column(String)
    fingerprint = Column(LargeBinary)
    chromaprint_fingerprint = Column(Text)
    created_at = Column(DateTime)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    Base.metadata.create_all(bind=engine)