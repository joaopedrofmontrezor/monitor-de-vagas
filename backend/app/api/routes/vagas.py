import math
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_vaga_repository
from app.repositories.vagas import FiltroVagas, VagaRepository
from app.schemas.vaga import PaginaVagas, VagaSaida

MAX_POR_PAGINA = 50

router = APIRouter(prefix="/vagas", tags=["vagas"])


@router.get(
    "",
    summary="Lista as vagas coletadas",
    description=(
        "Vagas mais recentes primeiro, com paginação. Os filtros são combinados com E. "
        "A busca no título e o filtro de cidade ignoram maiúsculas e acentos "
        '("estagio" encontra "Estágio"); `cidade` casa pelo começo do nome '
        '("sao paulo" encontra "São Paulo - SP").'
    ),
)
def listar_vagas(
    repositorio: Annotated[VagaRepository, Depends(get_vaga_repository)],
    q: Annotated[
        str | None, Query(max_length=100, description="Trecho do título", examples=["dados"])
    ] = None,
    cidade: Annotated[
        str | None, Query(max_length=120, description="Cidade", examples=["São Paulo"])
    ] = None,
    remoto: Annotated[
        bool | None, Query(description="true: só remotas; false: só presenciais/híbridas")
    ] = None,
    pagina: Annotated[int, Query(ge=1, description="Começa em 1")] = 1,
    por_pagina: Annotated[int, Query(ge=1, le=MAX_POR_PAGINA)] = 20,
) -> PaginaVagas:
    filtro = FiltroVagas(q=q, cidade=cidade, remoto=remoto)
    vagas, total = repositorio.listar(filtro, pagina=pagina, por_pagina=por_pagina)
    return PaginaVagas(
        itens=[VagaSaida.model_validate(v) for v in vagas],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=math.ceil(total / por_pagina),
    )
