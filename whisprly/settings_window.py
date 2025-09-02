from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)
from .config import save_api_key, load_api_key, load_settings, save_settings


class SettingsWindow(QDialog):
    def __init__(self, parent=None, show_api_key_required=False):
        super().__init__(parent)
        self.setWindowTitle("Whisprly Settings")
        self.setModal(False)  # Don't block the main app
        self.show_api_key_required = show_api_key_required
        
        # Override close event to prevent killing the main app
        from PyQt6.QtCore import Qt
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # Load existing settings from .config.json
        self.settings = load_settings()
        self.existing_api_key = load_api_key()

        # Create layout and widgets
        self._setup_ui()
        
        if show_api_key_required:
            self.setWindowTitle("Whisprly - API Key Required")


    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        if self.show_api_key_required:
            info_label = QLabel("Welcome to Whisprly! Please enter your Groq API key to get started.")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

        # API Key setting
        api_key_label = QLabel("Groq API Key:")
        self.api_key_input = QLineEdit()
        if self.existing_api_key:
            # Show dots for existing key
            self.api_key_input.setText("•" * 20)
            self.api_key_input.setPlaceholderText("API key is set (enter new key to replace)")
        else:
            self.api_key_input.setPlaceholderText("Enter your Groq API key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(api_key_label)
        layout.addWidget(self.api_key_input)

        # Show API key button
        self.show_key_button = QPushButton("Show Key" if self.existing_api_key else "")
        if self.existing_api_key:
            self.show_key_button.clicked.connect(self._toggle_key_visibility)
            layout.addWidget(self.show_key_button)

        # Theme setting
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "light"))
        layout.addWidget(theme_label)
        layout.addWidget(self.theme_combo)

        # Start recording shortcut
        start_shortcut_label = QLabel("Start Recording Shortcut:")
        self.start_shortcut_input = QLineEdit()
        self.start_shortcut_input.setText(self.settings.get("START_RECORDING_SHORTCUT", "ctrl+alt+o"))
        layout.addWidget(start_shortcut_label)
        layout.addWidget(self.start_shortcut_input)

        # Stop recording shortcut
        stop_shortcut_label = QLabel("Stop Recording Shortcut:")
        self.stop_shortcut_input = QLineEdit()
        self.stop_shortcut_input.setText(self.settings.get("STOP_RECORDING_SHORTCUT", "ctrl+alt+o"))
        layout.addWidget(stop_shortcut_label)
        layout.addWidget(self.stop_shortcut_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_settings)
        if not self.show_api_key_required:
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.clicked.connect(self._cancel_settings)
            button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

    def _toggle_key_visibility(self) -> None:
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.api_key_input.setText(self.existing_api_key)
            self.show_key_button.setText("Hide Key")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.api_key_input.setText("•" * 20)
            self.show_key_button.setText("Show Key")
    
    def _save_settings(self) -> None:
        # Save API key if provided
        api_key_text = self.api_key_input.text().strip()
        if api_key_text and api_key_text != "•" * 20:
            if not api_key_text.startswith("gsk_"):
                QMessageBox.warning(self, "Invalid API Key", 
                                  "Groq API keys should start with 'gsk_'. Please check your key.")
                return
            save_api_key(api_key_text)
        elif self.show_api_key_required and not self.existing_api_key:
            QMessageBox.warning(self, "API Key Required", 
                              "Please enter your Groq API key to continue.")
            return

        # Save other settings
        self.settings["theme"] = self.theme_combo.currentText()
        self.settings["START_RECORDING_SHORTCUT"] = self.start_shortcut_input.text()
        self.settings["STOP_RECORDING_SHORTCUT"] = self.stop_shortcut_input.text()

        save_settings(self.settings)

        # Don't use accept() as it might close the main app
        # Just close the window instead and emit a custom signal if needed
        self.hide()
        self.deleteLater()
        
    def _cancel_settings(self) -> None:
        """Handle cancel button - just close window without saving."""
        print("Settings cancelled")
        self.hide()
        self.deleteLater()
        
    def closeEvent(self, event):
        """Override close event to ensure app doesn't quit when settings window closes."""
        print("Settings window closed via X button")
        # Prevent the event from propagating to parent and killing the app
        event.ignore()  # First ignore the event
        self.hide()  # Hide the window
        self.deleteLater()  # Clean up the window
        # Don't call event.accept() as it might propagate to main app
