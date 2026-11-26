from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.config import settings
from app.models import Base

config = context.config
if config.config_file_name is not None and config.attributes.get("configurar_logs", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def rodar_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def rodar_online() -> None:
    conexao = config.attributes.get("conexao")
    if conexao is not None:
        _migrar(conexao)
        return
    engine = create_engine(settings.database_url)
    with engine.connect() as conexao_nova:
        _migrar(conexao_nova)
    engine.dispose()


def _migrar(conexao) -> None:
    context.configure(connection=conexao, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    rodar_offline()
else:
    rodar_online()
