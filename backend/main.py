from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

from database import get_db, init_db
from models import Track
from fingerprinting import AudioFingerprinter
from matching import AudioMatcher
from schemas import MatchResult, MatchRequest

load_dotenv()

app = FastAPI(title="SoundScout API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fingerprinter = AudioFingerprinter()
matcher = AudioMatcher()

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
async def root():
    return {"message": "SoundScout API"}

@app.post("/match", response_model=MatchResult)
async def match_audio(file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be audio")
        
        audio_data = await file.read()
        fingerprint = fingerprinter.fingerprint_audio(audio_data)
        
        matches = await matcher.find_matches(fingerprint, top_k=5)
        
        return MatchResult(
            matches=matches,
            processing_time_ms=0,
            confidence_threshold=0.7
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)