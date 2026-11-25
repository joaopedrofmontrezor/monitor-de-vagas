"""Configuração lida das variáveis de ambiente (e do arquivo .env, se existir).

Toda configuração passa por aqui: o resto do código importa `settings` e nunca
lê `os.environ` direto. Assim os nomes das variáveis ficam documentados num lugar só.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # "../.env" é o .env da raiz do repositório quando o pytest roda dentro de backend/.
    # No Docker as variáveis já chegam pelo env_file do compose.
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    ambiente: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://monitor:monitor@localhost:5432/monitor_vagas"

    # Token do bot criado no BotFather. Vazio = Telegram desligado (útil nos testes).
    telegram_bot_token: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
