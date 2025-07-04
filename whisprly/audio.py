import threading
from typing import List, Optional

import numpy as np
import sounddevice as sd
import soundfile as sf
from sounddevice import CallbackFlags


class AudioRecorder:
    def __init__(self, TEMP_FILENAME: str, rate: int, channels: int) -> None:
        self.TEMP_FILENAME: str = TEMP_FILENAME
        self.rate: int = rate
        self.channels: int = channels
        self.recording: bool = False
        self.frames: List[np.ndarray] = []
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self.recording = True
        self.frames = []
        self.thread = threading.Thread(target=self._record)
        self.thread.start()

    def _record(self) -> None:
        with sd.InputStream(
            samplerate=self.rate, channels=self.channels, callback=self.callback
        ):
            while self.recording:
                sd.sleep(100)

    def callback(self, indata: np.ndarray, frames: int, time, status: CallbackFlags) -> None:
        if status:
            print(status)
        self.frames.append(indata.copy())

    def stop(self) -> None:
        self.recording = False
        if self.thread:
            self.thread.join()

    def save(self) -> None:
        if not self.frames:
            return
        recording_data: np.ndarray = np.concatenate(self.frames, axis=0)
        sf.write(self.TEMP_FILENAME, recording_data, self.rate)
