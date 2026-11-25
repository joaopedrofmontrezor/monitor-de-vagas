from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Annotated[Session, Depends(get_db)]) -> JSONResponse:
    """Confirma que a API está de pé e que o banco responde.

    Responde 503 quando o banco cai: o healthcheck do Docker (e do Render, no
    deploy) entende que o serviço não está saudável, em vez de achar que está tudo bem.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "erro", "banco": "indisponivel"})
    return JSONResponse(status_code=200, content={"status": "ok", "banco": "ok"})
