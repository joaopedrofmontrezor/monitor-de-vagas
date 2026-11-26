from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Vaga
from app.services.deduplicacao import normalizar_texto

TAMANHO_LOTE = 500
_COLUNAS_DO_BANCO = {"id", "coletada_em"}
_COM_ACENTO = "áàâãäéèêëíìîïóòôõöúùûüçñÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑ"
_SEM_ACENTO = "aaaaaeeeeiiiiooooouuuucnaaaaaeeeeiiiiooooouuuucn"


@dataclass(frozen=True)
class FiltroVagas:
    q: str | None = None
    cidade: str | None = None
    remoto: bool | None = None


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

    def listar(
        self, filtro: FiltroVagas, pagina: int = 1, por_pagina: int = 20
    ) -> tuple[list[Vaga], int]:
        condicoes = _condicoes(filtro)
        total = self._sessao.scalar(select(func.count()).select_from(Vaga).where(*condicoes))
        consulta = (
            select(Vaga)
            .where(*condicoes)
            .order_by(Vaga.coletada_em.desc(), Vaga.id.desc())
            .limit(por_pagina)
            .offset((pagina - 1) * por_pagina)
        )
        return list(self._sessao.scalars(consulta)), total or 0


def _condicoes(filtro: FiltroVagas) -> list[ColumnElement[bool]]:
    condicoes: list[ColumnElement[bool]] = []
    if filtro.q and (termo := normalizar_texto(filtro.q)):
        condicoes.append(_sem_acento(Vaga.titulo).like(f"%{_escapar_like(termo)}%", escape="\\"))
    if filtro.cidade and (cidade := normalizar_texto(filtro.cidade)):
        condicoes.append(_sem_acento(Vaga.cidade).like(f"{_escapar_like(cidade)}%", escape="\\"))
    if filtro.remoto is not None:
        condicoes.append(Vaga.remoto.is_(filtro.remoto))
    return condicoes


def _sem_acento(coluna) -> ColumnElement[str]:
    return func.lower(func.translate(coluna, _COM_ACENTO, _SEM_ACENTO))


def _escapar_like(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


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
