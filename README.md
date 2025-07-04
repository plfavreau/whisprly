# Whisprly 🤫

Whisprly is a lightweight, real-time voice-to-text transcription tool powered by Groq.

## 🚀 Quick Start

### 1. Installation

Get up and running in seconds.

```bash
# Create a virtual environment
uv venv

# Activate it (Windows)
.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Configuration

1.  Copy the `.env.example` file to `.env`.
2.  Create a Groq API key from [console.groq.com/keys](https://console.groq.com/keys).
3.  Set your `GROQ_API_KEY` in the `.env` file.

### 3. Usage

- **Start Recording**: Press and hold the `F1` key.
- **Stop Recording**: Release the `F1` key.
- The transcription will appear at the current position of your text cursor.
- **Exit**: Press `CTRL` + `ALT` + `X` to exit the application.

> ✨ These shortcuts can be customized in your `.env` file.

---
