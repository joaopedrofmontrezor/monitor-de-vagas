from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Vaga

TAMANHO_LOTE = 500
_COLUNAS_DO_BANCO = {"id", "coletada_em"}


@dataclass(frozen=True)
class ResultadoUpsert:
    novas: int
    duplicadas: int
    ids_novos: list[int] = field(default_factory=list)


class VagaRepository:
    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def salvar_novas(self, vagas: Sequence[Vaga]) -> ResultadoUpsert:
        ids_novos: list[int] = []
        for inicio in range(0, len(vagas), TAMANHO_LOTE):
            lote = [_como_linha(v) for v in vagas[inicio : inicio + TAMANHO_LOTE]]
            comando = insert(Vaga).values(lote).on_conflict_do_nothing().returning(Vaga.id)
            ids_novos += self._sessao.scalars(comando).all()
        return ResultadoUpsert(
            novas=len(ids_novos), duplicadas=len(vagas) - len(ids_novos), ids_novos=ids_novos
        )


def _como_linha(vaga: Vaga) -> dict[str, Any]:
    linha: dict[str, Any] = {}
    for coluna in Vaga.__table__.columns:
        if coluna.key in _COLUNAS_DO_BANCO:
            continue
        valor = getattr(vaga, coluna.key)
        if valor is None and coluna.default is not None:
            valor = coluna.default.arg
        linha[coluna.key] = valor
    return linha
