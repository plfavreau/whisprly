import signal

from PyQt6.QtCore import QTimer

from whisprly.app import VoiceToTextApp

if __name__ == "__main__":
    app = VoiceToTextApp()

    signal.signal(signal.SIGINT, lambda sig, frame: app._initiate_shutdown())

    timer = QTimer()
    timer.start(250)
    timer.timeout.connect(lambda: None)

    app.run()
