import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from app.db import engine
from app.models import Base

pytestmark = pytest.mark.integracao


def test_banco_esta_na_ultima_migration(banco_migrado, config_alembic):
    with engine.connect() as conexao:
        atual = MigrationContext.configure(conexao).get_current_revision()
        cabeca = ScriptDirectory.from_config(config_alembic(conexao)).get_current_head()

    assert atual == cabeca


def test_models_e_migrations_estao_em_sincronia(banco_migrado):
    with engine.connect() as conexao:
        diferencas = compare_metadata(
            MigrationContext.configure(conexao, opts={"compare_type": True}), Base.metadata
        )

    assert diferencas == [], "rode `make migration m=...` para gerar a migration que falta"


def test_downgrade_e_upgrade_de_novo(banco_migrado, config_alembic):
    with engine.connect() as conexao:
        transacao = conexao.begin()
        try:
            command.downgrade(config_alembic(conexao), "base")
            assert "vagas" not in inspect(conexao).get_table_names()

            command.upgrade(config_alembic(conexao), "head")
            assert {"vagas", "execucoes_coleta"} <= set(inspect(conexao).get_table_names())
        finally:
            transacao.rollback()
