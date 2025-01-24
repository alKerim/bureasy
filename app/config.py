import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # FastAPI settings
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000
    FASTAPI_DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Allowed CORS
    ALLOWED_ORIGINS: List[str] = Field(default=["*"])  # Parse as a list
    ALLOWED_METHODS: List[str] = Field(default=["*"])
    ALLOWED_HEADERS: List[str] = Field(default=["*"])

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Groq/OpenAI API keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    CLIENT_NAME: str = os.getenv("CLIENT_NAME", "groq")  # or "openai"

    # Models
    MODEL_NAME_CONVERSATIONAL_GROQ: str = os.getenv("MODEL_NAME_CONVERSATIONAL_GROQ", "")

    class Config:
        env_file = ".env"

settings = Settings()
