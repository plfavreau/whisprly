# Whisprly

Whisprly is a lightweight, real-time voice-to-text transcription tool powered by Whisper v3 Turbo through Groq.

## 🚀 Quick Start

### 1. Installation

Get up and running in seconds.

```bash
# Create a virtual environment and activate it
uv venv

.venv\Scripts\activate

# Sync dependencies
```

uv sync

````

### 2. Configuration

i

1.  Copy the `.env.example` file to `.env`.
2.  Create a Groq API key from [console.groq.com/keys](https://console.groq.com/keys).
3.  Set your `GROQ_API_KEY` in the `.env` file.

### 3. Usagei

```bash
# Run the application through the virtual environment
python main.py
````

- **Start Recording**: Press and hold the `F1` key.
- **Stop Recording**: Release the `F1` key.
- The transcription will appear at the current position of your text cursor.
- **Exit**: Press `CTRL` + `ALT` + `X` to exit the application.

> ✨ These shortcuts can be customized in your `.env` file.

### 4. Start on boot (Windows)

To start the application on boot, you can add a shortcut to the `start_whisprly.vbs` script in the startup folder:

1.  Press `Win + R` to open the Run dialog.
2.  Type `shell:startup` and press Enter. This will open the startup folder.
3.  Create a shortcut to the `start_whisprly.vbs` file by right-clicking on it and selecting `Create shortcut`.
4.  Move the newly created shortcut into the startup folder.

[!] Note: The exit is not possible in this mode (or you may need to cut the process manually)
