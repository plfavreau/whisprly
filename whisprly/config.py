import os
import json

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(verbose=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    GROQ_API_KEY: str = os.environ["GROQ_API_KEY"]


try:
    settings = Settings()
except Exception as e:
    raise ValueError(
        "Missing required environment variables. Please check your .env file."
    ) from e

settings_path = os.path.join(os.path.dirname(__file__), '../settings.json')
with open(settings_path, 'r') as f:
    json_settings = json.load(f)
START_RECORDING_SHORTCUT = json_settings.get('START_RECORDING_SHORTCUT', 'o')
EXIT_SHORTCUT = json_settings.get('EXIT_SHORTCUT', 'ctrl+alt+x')
