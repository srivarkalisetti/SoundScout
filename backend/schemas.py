from pydantic import BaseModel
from typing import List, Optional

class TrackMatch(BaseModel):
    track_id: int
    title: str
    artist: str
    confidence: float
    duration: float
    url: str

class MatchResult(BaseModel):
    matches: List[TrackMatch]
    processing_time_ms: float
    confidence_threshold: float

class MatchRequest(BaseModel):
    audio_data: bytes