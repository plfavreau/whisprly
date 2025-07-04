import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(verbose=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    GROQ_API_KEY: str = os.environ["GROQ_API_KEY"]
    START_RECORDING_SHORTCUT: str = "f1"
    EXIT_SHORTCUT: str = "ctrl+alt+x"


try:
    settings = Settings()
except Exception as e:
    raise ValueError(
        "Missing required environment variables. Please check your .env file."
    ) from e
