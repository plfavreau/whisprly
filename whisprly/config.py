import os
import json
import sys
import base64


class Settings:
    def __init__(self):
        self.GROQ_API_KEY: str = ""


def get_secret_file_path() -> str:
    """Get the path to the .secret file next to the executable or in the project root."""
    if getattr(sys, 'frozen', False):
        # Running as a bundled exe - save next to the executable
        return os.path.join(os.path.dirname(sys.executable), ".secret")
    else:
        # Running as a script - save in project root
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), ".secret")


def get_config_file_path() -> str:
    """Get the path to the .config.json file next to the executable or in the project root."""
    if getattr(sys, 'frozen', False):
        # Running as a bundled exe - save next to the executable
        return os.path.join(os.path.dirname(sys.executable), ".config.json")
    else:
        # Running as a script - save in project root
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), ".config.json")


def load_api_key() -> str:
    """Load API key from .secret file."""
    secret_file = get_secret_file_path()
    if os.path.exists(secret_file):
        try:
            with open(secret_file, 'r') as f:
                encoded_key = f.read().strip()
                # Simple encoding - decode from base64
                return base64.b64decode(encoded_key.encode()).decode()
        except Exception:
            pass
    
    return ""


def save_api_key(api_key: str) -> None:
    """Save API key to .secret file with simple encoding."""
    secret_file = get_secret_file_path()
    # Simple encoding - encode to base64
    encoded_key = base64.b64encode(api_key.encode()).decode()
    with open(secret_file, 'w') as f:
        f.write(encoded_key)


def has_api_key() -> bool:
    """Check if API key is available."""
    return bool(load_api_key())


def load_settings() -> dict:
    """Load settings from .config.json file or create default settings."""
    config_file = get_config_file_path()
    default_settings = {
        "theme": "light",
        "START_RECORDING_SHORTCUT": "ctrl+alt+o",
        "STOP_RECORDING_SHORTCUT": "ctrl+alt+o",
        "EXIT_SHORTCUT": "ctrl+alt+x"
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    # Create default config file if it doesn't exist
    save_settings(default_settings)
    return default_settings


def save_settings(settings_dict: dict) -> None:
    """Save settings to .config.json file."""
    config_file = get_config_file_path()
    with open(config_file, 'w') as f:
        json.dump(settings_dict, f, indent=2)


# Load API key and settings at startup
api_key = load_api_key()
settings = Settings()
settings.GROQ_API_KEY = api_key

json_settings = load_settings()
START_RECORDING_SHORTCUT = json_settings.get("START_RECORDING_SHORTCUT", "ctrl+alt+o")
STOP_RECORDING_SHORTCUT = json_settings.get("STOP_RECORDING_SHORTCUT", "ctrl+alt+o")
EXIT_SHORTCUT = json_settings.get("EXIT_SHORTCUT", "ctrl+alt+x")

def reload_settings() -> None:
    global START_RECORDING_SHORTCUT, STOP_RECORDING_SHORTCUT, EXIT_SHORTCUT
    json_settings = load_settings()
    START_RECORDING_SHORTCUT = json_settings.get("START_RECORDING_SHORTCUT", "ctrl+alt+o")
    STOP_RECORDING_SHORTCUT = json_settings.get("STOP_RECORDING_SHORTCUT", "ctrl+alt+o")
    EXIT_SHORTCUT = json_settings.get("EXIT_SHORTCUT", "ctrl+alt+x")
