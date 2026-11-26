import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.api.deps import get_db
from app.db import engine
from app.main import app


def pytest_addoption(parser):
    parser.addoption(
        "--exigir-banco",
        action="store_true",
        default=False,
        help="falha, em vez de pular, quando o Postgres não responde (usado no CI)",
    )


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
def banco_disponivel(request):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        if request.config.getoption("--exigir-banco"):
            pytest.fail("Postgres indisponível e o --exigir-banco foi passado")
        pytest.skip("Postgres indisponível; rode `make up` para os testes de integração")
