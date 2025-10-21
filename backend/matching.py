import numpy as np
import redis
import pickle
from typing import List, Dict, Any
from annoy import AnnoyIndex
import os
from database import SessionLocal, Track
from schemas import TrackMatch

class AudioMatcher:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        self.index = None
        self.track_metadata = {}
        self._load_index()
    
    def _load_index(self):
        try:
            index_data = self.redis_client.get("audio_index")
            if index_data:
                self.index = pickle.loads(index_data)
            
            metadata = self.redis_client.get("track_metadata")
            if metadata:
                self.track_metadata = pickle.loads(metadata)
        except Exception as e:
            print(f"Failed to load index: {e}")
            self.index = None
            self.track_metadata = {}
    
    async def find_matches(self, fingerprint: Dict[str, Any], top_k: int = 5) -> List[TrackMatch]:
        if not self.index or not self.track_metadata:
            return []
        
        try:
            constellation_vector = self._fingerprint_to_vector(fingerprint['constellation'])
            
            indices, distances = self.index.get_nns_by_vector(
                constellation_vector, top_k, include_distances=True
            )
            
            matches = []
            for idx, distance in zip(indices, distances):
                if idx in self.track_metadata:
                    track_data = self.track_metadata[idx]
                    confidence = max(0, 1 - distance)
                    
                    matches.append(TrackMatch(
                        track_id=track_data['id'],
                        title=track_data['title'],
                        artist=track_data['artist'],
                        confidence=confidence,
                        duration=track_data['duration'],
                        url=track_data['url']
                    ))
            
            return matches
        except Exception as e:
            print(f"Matching failed: {e}")
            return []
    
    def _fingerprint_to_vector(self, constellation: List[Tuple[float, float, float]], 
                             vector_size: int = 1000) -> List[float]:
        vector = [0.0] * vector_size
        
        for freq_diff, time_diff, magnitude in constellation:
            freq_hash = int(abs(freq_diff) * 100) % vector_size
            time_hash = int(abs(time_diff) * 10) % vector_size
            
            vector[freq_hash] += magnitude
            vector[time_hash] += magnitude * 0.5
        
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = [v / norm for v in vector]
        
        return vector
    
    async def build_index(self):
        db = SessionLocal()
        try:
            tracks = db.query(Track).all()
            
            if not tracks:
                return
            
            vectors = []
            metadata = {}
            
            for i, track in enumerate(tracks):
                if track.fingerprint:
                    fingerprint_data = pickle.loads(track.fingerprint)
                    vector = self._fingerprint_to_vector(fingerprint_data.get('constellation', []))
                    vectors.append(vector)
                    
                    metadata[i] = {
                        'id': track.id,
                        'title': track.title,
                        'artist': track.artist,
                        'duration': track.duration,
                        'url': track.url
                    }
            
            if vectors:
                vector_dim = len(vectors[0])
                self.index = AnnoyIndex(vector_dim, 'angular')
                
                for i, vector in enumerate(vectors):
                    self.index.add_item(i, vector)
                
                self.index.build(10)
                
                self.redis_client.set("audio_index", pickle.dumps(self.index))
                self.redis_client.set("track_metadata", pickle.dumps(metadata))
                
                self.track_metadata = metadata
                
        finally:
            db.close()