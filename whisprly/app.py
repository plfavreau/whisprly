import os
import sys
from typing import Optional

import keyboard
import pyautogui
from groq import Groq
from groq.types.audio import Transcription
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from .audio import AudioRecorder
from .config import settings
from .ui import Notification, OverlayWidget

TEMP_FILENAME: str = "audio.wav"
SAMPLE_RATE: int = 44100
CHANNELS: int = 1

client: Groq = Groq(api_key=settings.GROQ_API_KEY)


class VoiceToTextApp(QObject):
    exit_signal = pyqtSignal()
    show_notification_signal = pyqtSignal(str)
    update_notification_signal = pyqtSignal(str)
    hide_notification_signal = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.app: QApplication = QApplication(sys.argv)
        self.overlay = OverlayWidget()
        self.exit_signal.connect(self.app.quit)
        self.show_notification_signal.connect(self._show_notification)
        self.update_notification_signal.connect(self._update_notification)
        self.hide_notification_signal.connect(self._hide_notification)
        self.recorder: AudioRecorder = AudioRecorder(
            TEMP_FILENAME, SAMPLE_RATE, CHANNELS
        )
        self.notification: Optional[Notification] = None
        self.is_recording: bool = False

    def start_recording(self) -> None:
        if not self.is_recording:
            self.is_recording = True
            self.recorder.start()
            self.overlay.show_overlay()
            self.show_notification_signal.emit("Listening...")
            print("Recording started...")

    def stop_recording_and_transcribe(
        self, _: Optional[keyboard.KeyboardEvent] = None
    ) -> None:
        if self.is_recording:
            self.is_recording = False
            self.recorder.stop()
            print("Recording stopped.")
            self.recorder.save()

            if not os.path.exists(self.recorder.TEMP_FILENAME):
                print("Recording was too short. No file saved.")
                self.hide_notification_signal.emit(0)
                return

            self.update_notification_signal.emit("Transcribing...")

            try:
                with open(self.recorder.TEMP_FILENAME, "rb") as file:
                    transcription: Transcription = client.audio.transcriptions.create(
                        file=(self.recorder.TEMP_FILENAME, file.read()),
                        model="whisper-large-v3-turbo",
                        response_format="verbose_json",
                    )
                pyautogui.write(transcription.text)
                self.update_notification_signal.emit("Done")
            except Exception as e:
                print(f"An error occurred: {e}")
                self.update_notification_signal.emit("Error!")
            finally:
                self.hide_notification_signal.emit(1000)
                if os.path.exists(self.recorder.TEMP_FILENAME):
                    os.remove(self.recorder.TEMP_FILENAME)

    def _exit_app(self) -> None:
        print("\nExit hotkey pressed. Shutting down...")
        self.exit_signal.emit()

    def _show_notification(self, text: str) -> None:
        self.notification = Notification(text)
        self.notification.show_animated()

    def _update_notification(self, text: str) -> None:
        if self.notification:
            self.notification.set_text(text)

    def _hide_notification(self, delay_ms: int) -> None:
        if self.notification:
            if delay_ms > 0:
                pass
            else:
                self.notification.hide_animated()

    def run(self) -> None:
        print(f"Press and hold '{settings.START_RECORDING_SHORTCUT}' to record.")
        print(f"Press '{settings.EXIT_SHORTCUT}' to exit.")
        keyboard.add_hotkey(
            settings.START_RECORDING_SHORTCUT, self.start_recording, suppress=True
        )
        keyboard.on_release_key(
            settings.START_RECORDING_SHORTCUT, self.stop_recording_and_transcribe
        )
        keyboard.add_hotkey(settings.EXIT_SHORTCUT, self._exit_app, suppress=True)
        self.app.exec()
