import os
import sys
import tempfile
from typing import Optional

import keyboard
import psutil
from groq import Groq
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from .audio import AudioRecorder
from .config import (
    EXIT_SHORTCUT,
    START_RECORDING_SHORTCUT,
    has_api_key,
    load_api_key,
    reload_settings,
)
from .settings_window import SettingsWindow
from .ui import Notification, OverlayWidget


class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon_path: str, parent=None) -> None:
        super().__init__(QIcon(icon_path), parent)
        self.setToolTip("Whisprly")
        # Ensure the system tray is available before showing
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.show()
        else:
            print("System tray is not available on this system.")


TEMP_FILENAME: str = "audio.wav"
SAMPLE_RATE: int = 44100
CHANNELS: int = 1

client: Optional[Groq] = None


class VoiceToTextApp(QObject):
    exit_signal = pyqtSignal()
    show_notification_signal = pyqtSignal(str)
    update_notification_signal = pyqtSignal(str)
    hide_notification_signal = pyqtSignal(int)
    shutdown_signal = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        # Check for single instance first
        if not self._check_single_instance():
            return

        self.app: QApplication = QApplication(sys.argv)
        self.overlay = OverlayWidget()
        self.exit_signal.connect(self.app.quit)
        self.show_notification_signal.connect(self._show_notification)
        self.update_notification_signal.connect(self._update_notification)
        self.hide_notification_signal.connect(self._hide_notification)
        self.shutdown_signal.connect(self._perform_shutdown)
        self.recorder: AudioRecorder = AudioRecorder(
            TEMP_FILENAME, SAMPLE_RATE, CHANNELS
        )
        self.notification: Optional[Notification] = None
        self.recording_pressed = False
        self.is_recording: bool = False
        self.is_processing = False
        self.settings_window: Optional[SettingsWindow] = None
        self.tray_icon = None
        self.tray_menu = None
        self.pid_file = None
        self._initialize_client()

    def _check_single_instance(self) -> bool:
        """Check if another instance is already running using PID file."""
        self.pid_file = os.path.join(tempfile.gettempdir(), "whisprly.pid")
        current_pid = os.getpid()

        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, "r") as f:
                    existing_pid = int(f.read().strip())

                # Check if the process with this PID is actually running
                if psutil.pid_exists(existing_pid):
                    try:
                        process = psutil.Process(existing_pid)
                        # Check if it's actually our application by looking at the command line
                        if any(
                            "whisprly" in str(arg).lower() or "main.py" in str(arg)
                            for arg in process.cmdline()
                        ):
                            # Another instance is running, show error dialog
                            temp_app = QApplication(sys.argv)
                            msg = QMessageBox()
                            msg.setIcon(QMessageBox.Icon.Warning)
                            msg.setWindowTitle("Whisprly Already Running")
                            msg.setText(
                                "Another instance of Whisprly is already running."
                            )
                            msg.setInformativeText(
                                f"Process ID: {existing_pid}\nPlease close the existing instance first, or check the system tray."
                            )
                            msg.exec()
                            temp_app.quit()
                            sys.exit(0)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process doesn't exist or we can't access it, remove stale PID file
                        os.remove(self.pid_file)
                else:
                    # PID doesn't exist, remove stale PID file
                    os.remove(self.pid_file)
            except (ValueError, FileNotFoundError, PermissionError):
                # Invalid PID file or permission issues, remove it
                try:
                    os.remove(self.pid_file)
                except (OSError, PermissionError):
                    pass

        # Write our PID to the file
        try:
            with open(self.pid_file, "w") as f:
                f.write(str(current_pid))
            print(f"Created PID file: {self.pid_file} with PID: {current_pid}")
        except Exception as e:
            print(f"Warning: Could not create PID file: {e}")

        return True

    def _on_settings_cancelled(self) -> None:
        """Handle when settings are cancelled - don't kill the app."""
        print("Settings cancelled, continuing background operation...")
        # Ensure tray icon stays visible
        if self.tray_icon:
            self.tray_icon.setVisible(True)

    def _on_settings_finished(self, result) -> None:
        """Handle when settings window is finished - don't kill the app."""
        print("Settings window closed, continuing background operation...")
        # Reload settings in case they were changed
        reload_settings()
        self._initialize_client()
        self._reregister_hotkeys()
        # Explicitly ensure the settings window is cleaned up but don't kill the main app
        if self.settings_window:
            self.settings_window.deleteLater()
            self.settings_window = None
        # Ensure tray icon remains visible
        if self.tray_icon:
            self.tray_icon.setVisible(True)
            print(
                f"Tray icon visibility after settings close: {self.tray_icon.isVisible()}"
            )

    def start_recording(self, _: Optional[keyboard.KeyboardEvent] = None) -> None:
        if not self.is_recording and not self.is_processing:
            self.is_recording = True
            self.is_processing = True
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
                self.update_notification_signal.emit("Recording too short")
                self.hide_notification_signal.emit(1000)
                self.is_processing = False
                return

            self.update_notification_signal.emit("Transcribing...")

            try:
                if not client:
                    self.update_notification_signal.emit("API key not configured")
                    self.hide_notification_signal.emit(2000)
                    self.is_processing = False
                    return

                with open(self.recorder.TEMP_FILENAME, "rb") as file:
                    transcription: str = client.audio.transcriptions.create(
                        file=(self.recorder.TEMP_FILENAME, file.read()),
                        model="whisper-large-v3-turbo",
                        response_format="text",
                    )  # type: ignore
                transcription = transcription.strip()
                print("Transcription: ", transcription)
                keyboard.write(transcription)
                self.update_notification_signal.emit("Done")
            except Exception as e:
                print(f"An error occurred: {e}")
                self.update_notification_signal.emit("Error!")
            finally:
                self.hide_notification_signal.emit(1000)
                if os.path.exists(self.recorder.TEMP_FILENAME):
                    os.remove(self.recorder.TEMP_FILENAME)
                self.is_processing = False

    def _create_tray_icon(self) -> None:
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray is not available on this system.")
            return

        icon_path = self._get_icon_path()
        print(f"Loading tray icon from: {icon_path}")

        self.tray_icon = TrayIcon(icon_path)
        self.tray_menu = QMenu()

        # Create menu actions
        self.settings_action = QAction("Settings")
        self.settings_action.triggered.connect(self.open_settings)

        self.quit_action = QAction("Quit")
        self.quit_action.triggered.connect(self._initiate_shutdown)

        # Add actions to menu
        self.tray_menu.addAction(self.settings_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.quit_action)

        # Set the context menu
        self.tray_icon.setContextMenu(self.tray_menu)

        # Add single-click handler to open settings
        self.tray_icon.activated.connect(self._on_tray_icon_activated)

        # Force show the tray icon
        self.tray_icon.setVisible(True)

        print(f"Tray icon created and should be visible: {self.tray_icon.isVisible()}")

    def _on_tray_icon_activated(self, reason) -> None:
        """Handle tray icon activation (single-click)."""
        from PyQt6.QtWidgets import QSystemTrayIcon

        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single left-click - open settings
            self.open_settings()

    def open_settings(self, show_api_key_required=False) -> None:
        # Always create a new settings window to avoid connection issues
        self.settings_window = SettingsWindow(
            show_api_key_required=show_api_key_required
        )
        self.settings_window.setModal(
            False
        )  # Make it non-modal so it doesn't block the tray icon

        # Show settings window without blocking the main application
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

        # Don't connect to any signals for regular settings to avoid shutdown issues
        # Settings will be handled internally by the settings window itself

    def _on_settings_saved(self) -> None:
        """Handle when settings are saved."""
        print("Settings saved, reloading configuration...")
        reload_settings()
        self._initialize_client()
        self._reregister_hotkeys()
        # Ensure tray icon stays visible
        if self.tray_icon:
            self.tray_icon.setVisible(True)

    def _reregister_hotkeys(self) -> None:
        keyboard.unhook_all()

        try:
            # Register recording hotkey - use a different approach for press/release
            self.recording_pressed = False

            def on_recording_key_press():
                if not self.recording_pressed:
                    self.recording_pressed = True
                    self.start_recording()

            def on_recording_key_release():
                if self.recording_pressed:
                    self.recording_pressed = False
                    self.stop_recording_and_transcribe()

            # Register the hotkeys
            keyboard.add_hotkey(
                START_RECORDING_SHORTCUT, on_recording_key_press, suppress=True
            )
            keyboard.add_hotkey(
                START_RECORDING_SHORTCUT,
                on_recording_key_release,
                suppress=False,
                trigger_on_release=True,
            )

            # Register exit hotkey
            keyboard.add_hotkey(EXIT_SHORTCUT, self._initiate_shutdown, suppress=True)

            print(
                f"Hotkeys registered: Record={START_RECORDING_SHORTCUT}, Exit={EXIT_SHORTCUT}"
            )
        except Exception as e:
            print(f"Error registering hotkeys: {e}")
            # Try with simpler F1 key as fallback
            self._register_fallback_hotkeys()

    def _register_fallback_hotkeys(self) -> None:
        """Fallback to simpler hotkeys if combinations don't work."""
        try:
            print("Registering fallback hotkeys: F1 for recording, Ctrl+Alt+X for exit")

            self.recording_pressed = False

            def on_f1_press():
                if not self.recording_pressed:
                    self.recording_pressed = True
                    self.start_recording()

            def on_f1_release():
                if self.recording_pressed:
                    self.recording_pressed = False
                    self.stop_recording_and_transcribe()

            keyboard.add_hotkey("f1", on_f1_press, suppress=True)
            keyboard.add_hotkey(
                "f1", on_f1_release, suppress=False, trigger_on_release=True
            )
            keyboard.add_hotkey("ctrl+alt+x", self._initiate_shutdown, suppress=True)

        except Exception as e:
            print(f"Even fallback hotkeys failed: {e}")
            print("You may need to use the system tray menu to control the application")

    def _get_icon_path(self) -> str:
        # Determine the path to the icon file, considering PyInstaller's behavior
        if getattr(sys, "frozen", False):
            # Running as a bundled exe
            base_path = sys._MEIPASS  # type: ignore
        else:
            # Running as a script
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Try multiple icon formats
        icon_paths = [
            os.path.join(base_path, "whisprly", "assets", "icon.png"),
        ]

        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                print(f"Found icon at: {icon_path}")
                return icon_path

        print(f"No icon found in {base_path}")
        # Return a default system icon if no custom icon is found
        return ""

    def _initiate_shutdown(self) -> None:
        print("\nShutdown initiated...")
        # This method is safe to call from any thread.
        keyboard.unhook_all()
        self.shutdown_signal.emit()

    def _perform_shutdown(self) -> None:
        print("Performing shutdown on main thread...")
        # This method will be executed on the main GUI thread.
        if self.notification:
            self.notification.close()
        self.overlay.close()

        # Hide the tray icon before quitting
        if self.tray_icon:
            self.tray_icon.hide()

        # Clean up the PID file
        if self.pid_file and os.path.exists(self.pid_file):
            try:
                os.remove(self.pid_file)
                print(f"Removed PID file: {self.pid_file}")
            except Exception as e:
                print(f"Warning: Could not remove PID file: {e}")

        self.app.quit()
        os._exit(0)

    def _show_notification(self, text: str) -> None:
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

    def _initialize_client(self) -> None:
        """Initialize the Groq client with the current API key."""
        global client
        api_key = load_api_key()
        if api_key:
            client = Groq(api_key=api_key)
        else:
            client = None

    def _check_api_key_on_startup(self) -> None:
        """Check if API key is available and show settings when appropriate."""
        if not has_api_key():
            # No API key - show required dialog and handle it specially
            self._show_required_api_key_dialog()
        elif getattr(sys, "frozen", False):
            # Running as exe - show settings on first launch
            self.open_settings(show_api_key_required=False)
        else:
            # Running as script - just ensure tray icon is visible
            if self.tray_icon:
                self.tray_icon.setVisible(True)

    def _show_required_api_key_dialog(self) -> None:
        """Show the API key required dialog and handle the blocking behavior."""
        settings_window = SettingsWindow(show_api_key_required=True)

        def on_api_key_dialog_finished():
            if not has_api_key():
                print("No API key provided. Exiting...")
                self._initiate_shutdown()
            else:
                self._initialize_client()
                print("API key configured successfully!")

        # Only connect the shutdown logic for the API key required dialog
        settings_window.finished.connect(on_api_key_dialog_finished)
        settings_window.show()
        settings_window.raise_()
        settings_window.activateWindow()

    def run(self) -> None:
        # Create tray icon first to ensure it's always visible
        self._create_tray_icon()

        # Check for API key on startup
        self._check_api_key_on_startup()

        # Ensure tray icon is visible after startup
        if self.tray_icon:
            self.tray_icon.setVisible(True)
            print(f"Tray icon final visibility: {self.tray_icon.isVisible()}")

        print(f"Press and hold '{START_RECORDING_SHORTCUT}' to record.")
        print(f"Press '{EXIT_SHORTCUT}' to exit.")
        self._reregister_hotkeys()
        self.app.exec()
