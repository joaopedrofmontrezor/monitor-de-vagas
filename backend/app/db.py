"""Engine e sessão do SQLAlchemy.

A engine é criada uma vez por processo (API ou worker). `pool_pre_ping` testa a
conexão antes de usar, o que evita erro quando o Postgres reinicia no meio do dia.
`connect_timeout` faz o /health responder 503 em segundos, em vez de travar, se o banco sumir.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url, pool_pre_ping=True, connect_args={"connect_timeout": 5}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Abre uma sessão e garante que ela é fechada no fim da requisição."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
