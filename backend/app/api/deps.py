from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.repositories.vagas import VagaRepository

get_db = get_session


def get_vaga_repository(db: Annotated[Session, Depends(get_db)]) -> VagaRepository:
    return VagaRepository(db)


__all__ = ["get_db", "get_vaga_repository"]
