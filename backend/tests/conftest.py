import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.api.deps import get_db
from app.db import engine
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sobrescrever_db():

    def _trocar(sessao_falsa):
        app.dependency_overrides[get_db] = lambda: sessao_falsa

    return _trocar


@pytest.fixture(scope="session")
def banco_disponivel():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip("Postgres indisponível; rode `make up` para os testes de integração")
