import json
import os

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class OverlayWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.setInterval(3000)  # 3 seconds
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

    def show_overlay(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        self.show()


        self.timer.stop()


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
        self.setStyleSheet("background: transparent;")

        settings_path = os.path.join(
            os.path.dirname(__file__), "../settings.json"
        )  # Relative path to settings.json
        with open(settings_path, "r") as f:
            settings = json.load(f)
        self.theme = settings.get("theme", "dark")  # Store theme as instance variable

        self.current_state = "idle"
        self.spinner = None

        # Main container widget with glassmorphism effect
        self.container = QWidget()
        self.container.setAutoFillBackground(True)
        self.container.setObjectName("container")
        self.container.setFixedWidth(240)
        if self.theme == "dark":
            dark_style = """
                QWidget#container {
                    background-color: rgba(45, 45, 45, 0.95);
                    border-radius: 12px;
                }
            """
            self.container.setStyleSheet(dark_style)
        else:  # white theme
            light_style = """
                QWidget#container {
                    background-color: rgba(255, 255, 255, 0.95);
                    border-radius: 12px;
                }
            """
            self.container.setStyleSheet(light_style)
        # Enhanced shadow with multiple layers
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.container.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(16)

        self.text_label = QLabel()
        font = QFont(
            "Roboto", 10, QFont.Weight.Medium
        )  # Changed to Roboto font and smaller size
        self.text_label.setFont(font)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_color = "rgba(255, 255, 255, 0.95)" if self.theme == "dark" else "rgba(0, 0, 0, 0.87)"
        self.text_label.setStyleSheet(f"color: {text_color}; border: none; background: transparent;")

        layout.addWidget(self.text_label, 1)  # Add stretch factor

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        # Enhanced animations
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutBack)

        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(150)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.set_text(text)

    def set_text(self, text: str) -> None:
        self.text_label.setText(text)

        # Clear previous spinner
        if self.spinner:
            self.spinner.stop()
            self.spinner.deleteLater()
            self.spinner = None

        # Clear icon

        icon = ""
        if "Listening" in text or "Recording" in text:
            self.current_state = "recording"
            icon = "🎤 "

        elif "Transcribing" in text or "Processing" in text:
            self.current_state = "transcribing"
            icon = "⌛ "

        elif "Done" in text or "Complete" in text:
            self.current_state = "done"
            icon = "✅ "

        elif "Error" in text:
            self.current_state = "error"
            icon = "⚠ "
        else:
            self.current_state = "idle"

        self.text_label.setText(f"{icon}{text}")
        self.adjustSize()


    def show_animated(self) -> None:
        screen = QApplication.primaryScreen()
        if not screen:
            return
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        start_y = -self.height() - 20
        end_y = 20
        self.setGeometry(x, start_y, self.width(), self.height())
        self.setWindowOpacity(0.0)
        self.show()
        self.animation.setStartValue(QRect(x, start_y, self.width(), self.height()))
        self.animation.setEndValue(QRect(x, end_y, self.width(), self.height()))
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutBack)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(0.95)
        self.opacity_animation.setDuration(150)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        self.opacity_animation.start()

    def hide_animated(self) -> None:
        if self.spinner:
            self.spinner.stop()
        end_y = -self.height() - 20
        current_geom = self.geometry()
        self.animation.setStartValue(current_geom)
        self.animation.setEndValue(
            QRect(current_geom.x(), end_y, current_geom.width(), current_geom.height())
        )
        self.animation.setEasingCurve(QEasingCurve.Type.InBack)
        self.animation.setDuration(200)
        self.opacity_animation.setStartValue(self.windowOpacity())
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.setDuration(150)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.animation.start()
        self.opacity_animation.start()
        self.opacity_animation.finished.connect(self.close)
