import os
import sys
import threading
from typing import Any, List, Optional

import keyboard
import numpy as np
import pyautogui
import sounddevice as sd
import soundfile as sf
from groq import Groq
from groq.types.audio import Transcription
from PyQt6.QtCore import (
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    QRect,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from sounddevice import CallbackFlags

from config import settings

TEMP_FILENAME: str = "audio.wav"
SAMPLE_RATE: int = 44100
CHANNELS: int = 1

client: Groq = Groq(api_key=settings.GROQ_API_KEY)


class OverlayWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.3);")
        self.hide()

    def show_overlay(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        self.show()


class Notification(QWidget):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Main container widget
        self.container = QWidget()
        self.container.setStyleSheet(
            """
            QWidget {
                background-color: #212121;
                border-radius: 12px;
                border: 1px solid #424242;
            }
            """
        )

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.container.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_label = QLabel()
        self.text_label.setStyleSheet(
            """
            QLabel {
                color: #E0E0E0;
                font-size: 15px;
                font-weight: 500;
                border: none;
            }
            """
        )

        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(400)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(300)

        self.set_text(text)

    def set_text(self, text: str) -> None:
        self.text_label.setText(text)
        if "Listening" in text:
            icon_char = "🎤"
        elif "Done" in text:
            icon_char = "✓"
        elif "Error" in text:
            icon_char = "!"
        else:
            icon_char = "..."

        self.icon_label.setText(icon_char)
        self.icon_label.setStyleSheet(
            """
            QLabel {
                color: #E0E0E0;
                font-size: 20px;
                border: none;
            }
            """
        )
        self.adjustSize()

    def show_animated(self) -> None:
        screen = QApplication.primaryScreen()
        if not screen:
            return

        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        start_y = -self.height()
        end_y = 40

        self.setGeometry(x, start_y, self.width(), self.height())
        self.setWindowOpacity(0.0)
        self.show()

        self.animation.setStartValue(QRect(x, start_y, self.width(), self.height()))
        self.animation.setEndValue(QRect(x, end_y, self.width(), self.height()))

        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)

        self.animation.start()
        self.opacity_animation.start()

    def hide_animated(self) -> None:
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.finished.connect(self.close)
        self.opacity_animation.start()


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

    def callback(
        self, indata: np.ndarray, frames: int, time: Any, status: CallbackFlags
    ) -> None:
        if status:
            print(status, file=sys.stderr)
        self.frames.append(indata.copy())

    def stop(self) -> None:
        if not self.thread:
            return
        self.recording = False
        self.thread.join()
        if not self.frames:
            return
        recording_data: np.ndarray = np.concatenate(self.frames, axis=0)
        sf.write(self.TEMP_FILENAME, recording_data, self.rate)


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
            self.overlay.show_overlay()
            self.show_notification_signal.emit("Listening...")
            self.recorder.start()
            print("Recording started...")

    def stop_recording_and_transcribe(self) -> None:
        if self.is_recording:
            self.is_recording = False
            self.overlay.hide()
            self.recorder.stop()
            print("Recording stopped.")

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

                print(f"Transcription: {transcription.text}")
                pyautogui.write(transcription.text)
                self.update_notification_signal.emit("Done!")

            except Exception as e:
                print(f"Error during transcription: {e}")
                self.update_notification_signal.emit("Error!")
            finally:
                self.hide_notification_signal.emit(1000)
                if os.path.exists(self.recorder.TEMP_FILENAME):
                    os.remove(self.recorder.TEMP_FILENAME)

    def _exit_app(self) -> None:
        print("\nExit hotkey pressed. Shutting down...")
        keyboard.unhook_all()
        self.overlay.close()
        self.exit_signal.emit()

    def _show_notification(self, text: str) -> None:
        if self.notification:
            self.notification.close()
        self.notification = Notification(text)
        self.notification.show_animated()

    def _update_notification(self, text: str) -> None:
        if self.notification:
            self.notification.set_text(text)

    def _hide_notification(self, delay_ms: int) -> None:
        if self.notification:
            if delay_ms > 0:
                QTimer.singleShot(delay_ms, self.notification.hide_animated)
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


if __name__ == "__main__":
    app_instance: VoiceToTextApp = VoiceToTextApp()
    app_instance.run()
