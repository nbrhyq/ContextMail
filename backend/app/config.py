from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./contextmail.db"
    llm_provider: str = "ollama"
    llm_model: str = "qwen3:latest"
    ollama_base_url: str = "http://127.0.0.1:11434"
    llm_timeout_seconds: float = 120
    max_iterations: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CONTEXTMAIL_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

