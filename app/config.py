from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GROQ_API_KEY: str
    FASTAPI_HOST: str
    FASTAPI_PORT: int
    FASTAPI_DEBUG: bool
    LOG_LEVEL: str
    ALLOWED_ORIGINS: str
    ALLOWED_METHODS: str
    ALLOWED_HEADERS: str
    LANGUAGE: str
    CLIENT_NAME: str
    MODEL_NAME_CONVERSATIONAL_GROQ: str

    # Use only `model_config`
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow"  # Allow extra fields if needed
    )

settings = Settings()
