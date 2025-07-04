# Whisprly 🤫

Whisprly is a lightweight, real-time voice-to-text transcription tool powered by Groq.

## 🚀 Quick Start

### 1. Installation

Get up and running in seconds.

```bash
# Create a virtual environment and activate it
uv venv

.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Configuration

1.  Copy the `.env.example` file to `.env`.
2.  Create a Groq API key from [console.groq.com/keys](https://console.groq.com/keys).
3.  Set your `GROQ_API_KEY` in the `.env` file.

### 3. Usage

```bash
# Run the application through the virtual environment
python main.py
```

- **Start Recording**: Press and hold the `F1` key.
- **Stop Recording**: Release the `F1` key.
- The transcription will appear at the current position of your text cursor.
- **Exit**: Press `CTRL` + `ALT` + `X` to exit the application.

> ✨ These shortcuts can be customized in your `.env` file.

### 4. Start on boot (Windows)

To start the application on boot, you can add a shortcut to the startup folder :

1.  Create a shortcut to the application by right-clicking on the `main.py` file and selecting `Create shortcut`.
2.  Move the shortcut to the startup folder, usually found at `C:\Users\<YourUsername>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`.
