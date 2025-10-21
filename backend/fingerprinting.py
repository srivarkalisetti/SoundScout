import numpy as np
import librosa
import chromaprint
import hashlib
from typing import List, Tuple
import io

class AudioFingerprinter:
    def __init__(self):
        self.sample_rate = 22050
        self.n_fft = 2048
        self.hop_length = 512
        self.n_mels = 128
        
    def fingerprint_audio(self, audio_data: bytes) -> dict:
        try:
            audio_array, sr = librosa.load(io.BytesIO(audio_data), sr=self.sample_rate)
            
            chromaprint_fp = self._chromaprint_fingerprint(audio_array, sr)
            constellation_fp = self._constellation_fingerprint(audio_array, sr)
            
            return {
                'chromaprint': chromaprint_fp,
                'constellation': constellation_fp,
                'duration': len(audio_array) / sr
            }
        except Exception as e:
            raise ValueError(f"Audio fingerprinting failed: {str(e)}")
    
    def _chromaprint_fingerprint(self, audio: np.ndarray, sr: int) -> str:
        try:
            fp = chromaprint.fingerprint(audio, sr)
            return fp
        except:
            return ""
    
    def _constellation_fingerprint(self, audio: np.ndarray, sr: int) -> List[Tuple[float, float, float]]:
        stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
        magnitude = np.abs(stft)
        
        mel_spec = librosa.feature.melspectrogram(
            S=magnitude, sr=sr, n_mels=self.n_mels, fmax=sr//2
        )
        
        peaks = self._find_peaks(mel_spec)
        constellation = self._build_constellation(peaks)
        
        return constellation
    
    def _find_peaks(self, spectrogram: np.ndarray, threshold: float = 0.1) -> List[Tuple[int, int, float]]:
        peaks = []
        for t in range(spectrogram.shape[1]):
            for f in range(spectrogram.shape[0]):
                if spectrogram[f, t] > threshold:
                    is_peak = True
                    for dt in [-1, 0, 1]:
                        for df in [-1, 0, 1]:
                            if (dt == 0 and df == 0):
                                continue
                            nt, nf = t + dt, f + df
                            if (0 <= nt < spectrogram.shape[1] and 
                                0 <= nf < spectrogram.shape[0] and 
                                spectrogram[nf, nt] >= spectrogram[f, t]):
                                is_peak = False
                                break
                        if not is_peak:
                            break
                    if is_peak:
                        peaks.append((f, t, spectrogram[f, t]))
        return peaks
    
    def _build_constellation(self, peaks: List[Tuple[int, int, float]], 
                           target_pairs: int = 100) -> List[Tuple[float, float, float]]:
        constellation = []
        for i, (f1, t1, mag1) in enumerate(peaks):
            for j, (f2, t2, mag2) in enumerate(peaks[i+1:], i+1):
                if t2 - t1 > 0.1 and t2 - t1 < 10.0:
                    freq_diff = f2 - f1
                    time_diff = t2 - t1
                    combined_mag = mag1 + mag2
                    constellation.append((freq_diff, time_diff, combined_mag))
        
        constellation.sort(key=lambda x: x[2], reverse=True)
        return constellation[:target_pairs]