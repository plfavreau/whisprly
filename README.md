<div align="center">

![Demo](whisprly/assets/demo.gif)

# Whisprly

**AI-powered speech-to-text that transcribes wherever your cursor is on your computer**

[![Release](https://img.shields.io/github/v/release/plfavreau/whisprly?style=for-the-badge&logo=github&color=blue)](https://github.com/plfavreau/whisprly/releases)
[![Downloads](https://img.shields.io/github/downloads/plfavreau/whisprly/total?style=for-the-badge&logo=download&color=green)](https://github.com/plfavreau/whisprly/releases)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://www.python.org/)

_Transform your voice into text instantly, anywhere on your screen_ ✨

</div>

---

## ✨ Features

- **Real-time transcription** - Press F1, speak, release, done!
- **Lightning fast** - Powered by Groq's Whisper v3 Turbo
- **System-wide** - Works in any application
- **Customizable** - Configure hotkeys and settings
- **Windows optimized** - Native Windows experience
- **Lightweight** - Minimal resource usage

## 📥 Quick Download

**Want to try it right now?**

**[Download the latest release](https://github.com/plfavreau/whisprly/releases/latest)** - Just download `Whisprly.exe` and run it!

## 🚀 Quick Start

### Option 1: Use the Pre-built Executable

1. **Download** the latest `Whisprly.exe` from [releases](https://github.com/plfavreau/whisprly/releases/latest)
2. **Get your API key** from [https://console.groq.com/keys](https://console.groq.com/keys)
3. **Run** `Whisprly.exe` and enter your API key in settings
4. **Start transcribing!** Press `F1` to record

### Option 2: Build from Source

```bash
# Clone the repository
git clone https://github.com/plfavreau/whisprly.git
cd whisprly

# Set up environment
uv venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
uv sync

# Configure
cp .env.example .env
# Add your GROQ_API_KEY to .env

# Run
python main.py
```

### 🔨 Build Your Own Executable

Want to create your own `Whisprly.exe`? It's super easy!

```bash
# Build the executable
uv run python build.py
```

Your new `Whisprly.exe` will be in the `dist/` folder!

## 🎯 How to Use

| Action     | Shortcut         | Description                   |
| ---------- | ---------------- | ----------------------------- |
| **Record** | Hold `F1`        | Start recording your voice    |
| **Stop**   | Release `F1`     | Stop recording and transcribe |
| **Exit**   | `Ctrl + Alt + X` | Close the application         |

> **Pro tip**: The transcription appears wherever your cursor is - works in any app!

## Configuration

Customize your experience by editing the `.env` file:

```bash
# API Configuration
GROQ_API_KEY=your_api_key_here

# Hotkey Settings
RECORD_KEY=f1
EXIT_KEY=ctrl+alt+x

# Audio Settings
SAMPLE_RATE=16000
CHANNELS=1
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Groq** provides the Whisper v3 Turbo API
- **OpenAI** provides the original Whisper model
- **PyQt6** provides the python UI framework

---

<div align="center">

**Made with ❤️ by [plfavreau](https://github.com/plfavreau)**

**Star this repo if you find it useful!**

</div>
