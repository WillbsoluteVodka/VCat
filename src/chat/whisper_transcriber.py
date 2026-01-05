"""
Whisper-based speech-to-text transcription for VCat.
Uses faster-whisper for efficient local transcription.
Supports Chinese and English with VAD auto-stop.
"""

import os
import tempfile
import threading
from typing import Optional, Callable
from queue import Queue

import numpy as np
import sounddevice as sd
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

# Try to import faster-whisper
try:
    from faster_whisper import WhisperModel
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    print("[Whisper] faster-whisper not installed. Run: pip install faster-whisper")


class AudioRecorder:
    """
    Audio recorder with Voice Activity Detection (VAD).
    Automatically stops recording after silence is detected.
    """
    
    SAMPLE_RATE = 16000  # Whisper expects 16kHz
    CHANNELS = 1
    SILENCE_THRESHOLD = 0.01  # RMS threshold for silence detection
    SILENCE_DURATION = 1.5   # Seconds of silence before auto-stop
    
    def __init__(self, on_auto_stop: Optional[Callable] = None):
        self.recording = False
        self.audio_data = []
        self._lock = threading.Lock()
        self.on_auto_stop = on_auto_stop  # Callback when auto-stop triggers
        self._silence_frames = 0
        self._frames_for_silence = int(self.SILENCE_DURATION * self.SAMPLE_RATE / 1024)  # ~23 frames for 1.5s
        self._has_speech = False  # Track if we've heard any speech
        
    def start(self):
        """Start recording audio with VAD."""
        with self._lock:
            self.audio_data = []
            self.recording = True
            self._silence_frames = 0
            self._has_speech = False
            
        def callback(indata, frames, time, status):
            if status:
                print(f"[AudioRecorder] Status: {status}")
            if not self.recording:
                return
                
            with self._lock:
                self.audio_data.append(indata.copy())
                
            # Calculate RMS for VAD
            rms = np.sqrt(np.mean(indata ** 2))
            
            if rms > self.SILENCE_THRESHOLD:
                # Speech detected
                self._silence_frames = 0
                self._has_speech = True
            else:
                # Silence detected
                if self._has_speech:  # Only count silence after speech
                    self._silence_frames += 1
                    
                    # Auto-stop after enough silence
                    if self._silence_frames >= self._frames_for_silence:
                        print(f"[AudioRecorder] Silence detected, auto-stopping...")
                        self.recording = False
                        if self.on_auto_stop:
                            # Call in main thread
                            self.on_auto_stop()
        
        self.stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype='float32',
            blocksize=1024,  # ~64ms per block
            callback=callback
        )
        self.stream.start()
        print("[AudioRecorder] Recording started (auto-stop on 1.5s silence)...")
        
    def stop(self) -> np.ndarray:
        """Stop recording and return audio data."""
        with self._lock:
            self.recording = False
            
        self.stream.stop()
        self.stream.close()
        
        with self._lock:
            if not self.audio_data:
                return np.array([], dtype=np.float32)
            audio = np.concatenate(self.audio_data, axis=0)
            
        print(f"[AudioRecorder] Recording stopped. Duration: {len(audio) / self.SAMPLE_RATE:.1f}s")
        return audio.flatten()
    
    def is_recording(self) -> bool:
        return self.recording


class TranscriptionWorker(QThread):
    """
    Background worker thread for Whisper transcription.
    Runs transcription without blocking the UI.
    """
    
    # Signal emitted when transcription is complete
    finished = pyqtSignal(str)
    
    # Signal emitted on error
    error = pyqtSignal(str)
    
    # Signal emitted for progress updates
    progress = pyqtSignal(str)
    
    def __init__(self, model: 'WhisperModel', audio_data: np.ndarray, parent=None):
        super().__init__(parent)
        self.model = model
        self.audio_data = audio_data
        
    def run(self):
        """Run transcription in background thread."""
        try:
            if len(self.audio_data) < 1600:  # Less than 0.1 second
                self.error.emit("录音太短，请再试一次")
                return
                
            self.progress.emit("正在识别...")
            
            # Run transcription
            # Use multilingual model settings
            segments, info = self.model.transcribe(
                self.audio_data,
                language=None,  # Auto-detect language
                task="transcribe",
                beam_size=5,
                vad_filter=True,  # Filter out silence
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200,
                )
            )
            
            # Collect transcribed text
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
                
            result = " ".join(text_parts).strip()
            
            if result:
                print(f"[Whisper] Transcription: {result}")
                self.finished.emit(result)
            else:
                self.error.emit("未检测到语音")
                
        except Exception as e:
            print(f"[Whisper] Transcription error: {e}")
            self.error.emit(f"识别失败: {str(e)}")


class WhisperTranscriber(QObject):
    """
    Main class for Whisper-based speech-to-text.
    Provides push-to-talk style voice input.
    
    Usage:
        transcriber = WhisperTranscriber()
        transcriber.transcription_ready.connect(on_text_ready)
        transcriber.start_recording()
        # User speaks...
        transcriber.stop_recording()  # This triggers transcription
    """
    
    # Signal emitted when transcription is ready
    transcription_ready = pyqtSignal(str)
    
    # Signal emitted for status updates
    status_changed = pyqtSignal(str)
    
    # Signal emitted on error
    error_occurred = pyqtSignal(str)
    
    # Available model sizes
    MODEL_SIZES = {
        'tiny': 'tiny',           # ~39MB, fastest, lower quality
        'base': 'base',           # ~74MB, fast, good quality
        'small': 'small',         # ~244MB, slower, better quality
        'medium': 'medium',       # ~769MB, slow, high quality
    }
    
    def __init__(self, model_size: str = 'base', parent=None):
        super().__init__(parent)
        
        self.model: Optional[WhisperModel] = None
        self.model_size = model_size
        self.recorder = AudioRecorder(on_auto_stop=self._on_vad_auto_stop)
        self.worker: Optional[TranscriptionWorker] = None
        self._is_loading = False
        self._is_recording = False
        
    def _on_vad_auto_stop(self):
        """Called by AudioRecorder when VAD detects silence."""
        # Use QTimer to ensure we're on the main thread
        from PyQt5.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(self, "_do_auto_stop", Qt.QueuedConnection)
    
    @pyqtSlot()
    def _do_auto_stop(self):
        """Actually perform the auto-stop (called on main thread)."""
        if self._is_recording:
            self.stop_recording()
        
    def load_model(self):
        """Load the Whisper model. Called lazily on first use."""
        if self.model is not None:
            return True
            
        if not HAS_WHISPER:
            self.error_occurred.emit("Whisper 未安装")
            return False
            
        if self._is_loading:
            return False
            
        self._is_loading = True
        self.status_changed.emit(f"正在加载语音模型 ({self.model_size})...")
        
        try:
            # Use CPU for compatibility
            # On Apple Silicon, this will use CoreML acceleration
            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",  # Faster on CPU
            )
            self.status_changed.emit("语音模型已就绪")
            print(f"[Whisper] Model '{self.model_size}' loaded successfully")
            self._is_loading = False
            return True
            
        except Exception as e:
            self._is_loading = False
            error_msg = f"加载模型失败: {str(e)}"
            print(f"[Whisper] {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
            
    def start_recording(self):
        """Start recording audio from microphone."""
        if self._is_recording:
            return
            
        # Ensure model is loaded
        if self.model is None:
            # Load model in background
            threading.Thread(target=self._load_and_start).start()
            return
            
        self._is_recording = True
        self.recorder.start()
        self.status_changed.emit("🎤 正在录音...")
        
    def _load_and_start(self):
        """Load model then start recording."""
        if self.load_model():
            self._is_recording = True
            self.recorder.start()
            self.status_changed.emit("🎤 正在录音...")
        
    def stop_recording(self):
        """Stop recording and start transcription."""
        if not self._is_recording:
            return
            
        self._is_recording = False
        audio_data = self.recorder.stop()
        
        if len(audio_data) < 1600:  # Too short
            self.error_occurred.emit("录音太短")
            return
            
        self.status_changed.emit("正在识别...")
        
        # Start transcription in background
        self.worker = TranscriptionWorker(self.model, audio_data, self)
        self.worker.finished.connect(self._on_transcription_done)
        self.worker.error.connect(self._on_transcription_error)
        self.worker.start()
        
    def _on_transcription_done(self, text: str):
        """Handle successful transcription."""
        self.status_changed.emit("")
        self.transcription_ready.emit(text)
        
    def _on_transcription_error(self, error: str):
        """Handle transcription error."""
        self.status_changed.emit("")
        self.error_occurred.emit(error)
        
    def cancel(self):
        """Cancel current recording/transcription."""
        if self._is_recording:
            self._is_recording = False
            self.recorder.stop()
            
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker = None
            
        self.status_changed.emit("")
        
    @property
    def is_recording(self) -> bool:
        return self._is_recording
        
    @property
    def is_ready(self) -> bool:
        return self.model is not None
        
    @property
    def is_available(self) -> bool:
        return HAS_WHISPER


# Convenience function for checking availability
def is_whisper_available() -> bool:
    """Check if Whisper is available on this system."""
    return HAS_WHISPER
