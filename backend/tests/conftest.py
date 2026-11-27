import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.api.deps import get_db
from app.config import settings
from app.main import app

SUFIXO_BANCO_TESTE = "_teste"


def url_de_teste(url: str) -> URL:
    original = make_url(url)
    nome = original.database or "monitor_vagas"
    if nome.endswith(SUFIXO_BANCO_TESTE):
        return original
    return original.set(database=f"{nome}{SUFIXO_BANCO_TESTE}")


URL_BANCO_TESTE = url_de_teste(settings.database_url)


def criar_banco_se_faltar(url: URL) -> None:
    admin = create_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        connect_args={"connect_timeout": 5},
    )
    try:
        with admin.connect() as conexao:
            existe = conexao.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :nome"), {"nome": url.database}
            )
            if not existe:
                conexao.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin.dispose()


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
def engine_teste():
    engine = create_engine(URL_BANCO_TESTE, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def banco_disponivel(request, engine_teste):
    try:
        criar_banco_se_faltar(URL_BANCO_TESTE)
        with engine_teste.connect() as conn:
            conn.execute(text("SELECT 1"))
    except (OperationalError, ProgrammingError) as exc:
        motivo = f"banco de teste {URL_BANCO_TESTE.database} indisponível ({type(exc).__name__})"
        if request.config.getoption("--exigir-banco"):
            pytest.fail(f"{motivo} e o --exigir-banco foi passado")
        pytest.skip(f"{motivo}; rode `make up` para os testes de integração")
