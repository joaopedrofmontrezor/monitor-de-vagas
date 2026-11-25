from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    ambiente: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://monitor:monitor@localhost:5432/monitor_vagas"

    telegram_bot_token: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
