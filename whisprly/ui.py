from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt
from PyQt6.QtGui import QColor
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
