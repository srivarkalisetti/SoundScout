import React, { useState, useRef, useEffect } from 'react';
import AudioRecorder from './components/AudioRecorder';
import MatchResults from './components/MatchResults';
import './App.css';

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [matches, setMatches] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const handleRecordingComplete = async (audioBlob) => {
    setIsProcessing(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.wav');
      
      const response = await fetch('/api/match', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Matching failed');
      }
      
      const result = await response.json();
      setMatches(result.matches || []);
    } catch (err) {
      setError(err.message);
      setMatches([]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFeedback = (trackId, isCorrect) => {
    console.log(`Feedback for track ${trackId}: ${isCorrect ? 'correct' : 'incorrect'}`);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>SoundScout</h1>
        <p>Identify SoundCloud tracks from audio clips</p>
      </header>
      
      <main className="App-main">
        <AudioRecorder
          onRecordingComplete={handleRecordingComplete}
          isRecording={isRecording}
          onRecordingChange={setIsRecording}
        />
        
        {isProcessing && (
          <div className="processing">
            <div className="spinner"></div>
            <p>Analyzing audio...</p>
          </div>
        )}
        
        {error && (
          <div className="error">
            <p>Error: {error}</p>
          </div>
        )}
        
        {matches.length > 0 && (
          <MatchResults
            matches={matches}
            onFeedback={handleFeedback}
          />
        )}
      </main>
    </div>
  );
}

export default App;