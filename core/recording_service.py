"""
Recording service for audio and video practice sessions
"""
import os
import threading
import time
from datetime import datetime
from typing import Optional, Callable
from pathlib import Path
from shutil import which
from config.settings import Settings

try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("[WARNING] sounddevice not available. Audio recording disabled.")

try:
    import cv2
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False
    print("[WARNING] opencv-python not available. Video recording disabled.")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("[WARNING] whisper not available. Speech-to-text disabled.")


class AudioRecorder:
    """Handle audio recording"""
    
    def __init__(self):
        self.is_recording = False
        self.audio_data = []
        self.sample_rate = 44100
        self.channels = 1
        self.recording_thread = None
        
    def start_recording(self):
        """Start audio recording"""
        if not AUDIO_AVAILABLE:
            raise RuntimeError("Audio recording not available. Install sounddevice.")
        
        if self.is_recording:
            return
        
        self.is_recording = True
        self.audio_data = []
        
        def record_audio():
            try:
                with sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    callback=self._audio_callback
                ):
                    while self.is_recording:
                        time.sleep(0.1)
            except Exception as e:
                print(f"[ERROR] Audio recording error: {e}")
                self.is_recording = False
        
        self.recording_thread = threading.Thread(target=record_audio, daemon=True)
        self.recording_thread.start()
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio input"""
        if status:
            print(f"[WARNING] Audio status: {status}")
        self.audio_data.append(indata.copy())
    
    def stop_recording(self) -> Optional[bytes]:
        """Stop recording and return audio data"""
        if not self.is_recording:
            return None
        
        self.is_recording = False
        
        if self.recording_thread:
            self.recording_thread.join(timeout=2)
        
        if not self.audio_data:
            return None
        
        # Concatenate all audio chunks
        import numpy as np
        audio_array = np.concatenate(self.audio_data, axis=0)
        
        return audio_array
    
    def save_recording(self, audio_data, file_path: str) -> bool:
        """Save audio recording to file"""
        try:
            if not AUDIO_AVAILABLE:
                return False
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save as WAV file
            sf.write(file_path, audio_data, self.sample_rate)
            return True
        except Exception as e:
            print(f"[ERROR] Error saving audio: {e}")
            return False


class VideoRecorder:
    """Handle video recording"""
    
    def __init__(self):
        self.is_recording = False
        self.video_writer = None
        self.cap = None
        self.fps = 30
        self.frame_width = 640
        self.frame_height = 480
        self.output_path = None
        
    def start_recording(self, output_path: str):
        """Start video recording"""
        if not VIDEO_AVAILABLE:
            raise RuntimeError("Video recording not available. Install opencv-python.")
        
        if self.is_recording:
            return
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        self.output_path = output_path
        self.cap = cv2.VideoCapture(0)  # Use default camera
        
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")
        
        # Get camera properties
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
        
        # Define codec and create VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            output_path,
            fourcc,
            self.fps,
            (self.frame_width, self.frame_height)
        )
        
        self.is_recording = True
        
        # Start recording thread
        def record_video():
            try:
                while self.is_recording:
                    ret, frame = self.cap.read()
                    if ret:
                        self.video_writer.write(frame)
                    else:
                        break
                    time.sleep(1.0 / self.fps)
            except Exception as e:
                print(f"[ERROR] Video recording error: {e}")
            finally:
                self._cleanup()
        
        recording_thread = threading.Thread(target=record_video, daemon=True)
        recording_thread.start()
    
    def stop_recording(self) -> Optional[str]:
        """Stop recording and return file path"""
        if not self.is_recording:
            return None
        
        self.is_recording = False
        time.sleep(0.5)  # Give thread time to finish
        
        return self.output_path
    
    def _cleanup(self):
        """Clean up video resources"""
        if self.video_writer:
            self.video_writer.release()
        if self.cap:
            self.cap.release()
        self.video_writer = None
        self.cap = None
    
    def get_preview_frame(self) -> Optional[bytes]:
        """Get a preview frame from camera"""
        if not VIDEO_AVAILABLE:
            return None
        
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return None
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                return buffer.tobytes()
            return None
        except Exception as e:
            print(f"[ERROR] Error getting preview frame: {e}")
            return None


class TranscriptionService:
    """Handle speech-to-text transcription"""
    
    _ffmpeg_checked = False
    _ffmpeg_available = False
    
    @staticmethod
    def _ensure_ffmpeg() -> bool:
        """Ensure ffmpeg is available for local Whisper transcription"""
        if TranscriptionService._ffmpeg_checked:
            return TranscriptionService._ffmpeg_available
        
        candidates = []
        if Settings.FFMPEG_PATH:
            candidates.append(Settings.FFMPEG_PATH)
        ffmpeg_in_path = which("ffmpeg")
        if ffmpeg_in_path:
            candidates.append(ffmpeg_in_path)
        
        for candidate in candidates:
            if not candidate:
                continue
            candidate_path = Path(candidate)
            if candidate_path.is_file() or candidate_path.is_dir():
                ffmpeg_dir = candidate_path.parent if candidate_path.is_file() else candidate_path
                if str(ffmpeg_dir) not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ.get("PATH", "")
                TranscriptionService._ffmpeg_available = True
                break
        
        TranscriptionService._ffmpeg_checked = True
        return TranscriptionService._ffmpeg_available
    
    @staticmethod
    def _transcribe_with_openai(audio_file_path: str) -> Optional[str]:
        """Use OpenAI Whisper API for transcription"""
        if not Settings.OPENAI_API_KEY:
            print("[ERROR] OPENAI_API_KEY not configured. Cannot fallback to API transcription.")
            return None
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=Settings.OPENAI_API_KEY)
            with open(audio_file_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
        except Exception as api_error:
            print(f"[ERROR] OpenAI transcription failed: {api_error}")
            return None
    
    @staticmethod
    def transcribe_audio(audio_file_path: str, use_api: bool = False) -> Optional[str]:
        """Transcribe audio file to text"""
        if not os.path.exists(audio_file_path):
            print(f"[ERROR] Audio file not found: {audio_file_path}")
            return None
        
        try:
            should_use_api = use_api
            if not should_use_api:
                if not WHISPER_AVAILABLE:
                    print("[WARNING] Whisper package not installed. Falling back to API transcription.")
                    should_use_api = True
                elif not TranscriptionService._ensure_ffmpeg():
                    print("[WARNING] ffmpeg not detected. Falling back to API transcription.")
                    should_use_api = True
            
            if should_use_api:
                return TranscriptionService._transcribe_with_openai(audio_file_path)
            
            os.environ.setdefault("WHISPER_DISABLE_F16", "1")  # Avoid FP16 warnings on CPU
            model = whisper.load_model("base")
            result = model.transcribe(audio_file_path)
            return result["text"]
                
        except Exception as e:
            print(f"[ERROR] Error transcribing audio: {e}")
            if "ffmpeg" in str(e).lower():
                print("⚠️ Please install ffmpeg (https://ffmpeg.org/download.html) and add it to your PATH, or set FFMPEG_PATH in your environment.")
            if not use_api and Settings.OPENAI_API_KEY:
                print("[INFO] Retrying transcription via OpenAI API fallback...")
                return TranscriptionService.transcribe_audio(audio_file_path, use_api=True)
            import traceback
            traceback.print_exc()
            return None

