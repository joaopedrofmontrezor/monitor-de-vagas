from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from app.db import engine

PASTA_BACKEND = Path(__file__).resolve().parents[2]


def criar_config_alembic(conexao) -> Config:
    config = Config(str(PASTA_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(PASTA_BACKEND / "alembic"))
    config.attributes["conexao"] = conexao
    config.attributes["configurar_logs"] = False
    return config


@pytest.fixture(scope="session")
def banco_migrado(banco_disponivel):
    with engine.begin() as conexao:
        command.upgrade(criar_config_alembic(conexao), "head")


@pytest.fixture
def sessao(banco_migrado):
    with engine.connect() as conexao:
        transacao = conexao.begin()
        sessao = Session(bind=conexao, join_transaction_mode="create_savepoint")
        try:
            yield sessao
        finally:
            sessao.close()
            transacao.rollback()


@pytest.fixture
def config_alembic():
    return criar_config_alembic
