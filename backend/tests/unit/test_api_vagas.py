from datetime import UTC, datetime

import pytest

from app.api.deps import get_vaga_repository
from app.main import app
from app.models import Vaga
from app.repositories.vagas import FiltroVagas


def vaga(id_: int, titulo: str = "Estágio em Dados") -> Vaga:
    return Vaga(
        id=id_,
        fonte="greenhouse",
        tipo="estagio",
        titulo=titulo,
        empresa="Acme",
        cidade="São Paulo - SP",
        remoto=False,
        descricao="não sai na listagem",
        url=f"https://boards.greenhouse.io/acme/jobs/{id_}",
        url_canonica=f"https://boards.greenhouse.io/acme/jobs/{id_}",
        chave_conteudo=f"{id_:064d}",
        publicada_em=None,
        coletada_em=datetime(2026, 12, 1, 9, 0, tzinfo=UTC),
    )


class RepositorioFalso:
    def __init__(self, vagas: list[Vaga] | None = None, total: int | None = None) -> None:
        self.vagas = vagas or []
        self.total = len(self.vagas) if total is None else total
        self.chamadas: list[tuple[FiltroVagas, int, int]] = []

    def listar(self, filtro: FiltroVagas, pagina: int = 1, por_pagina: int = 20):
        self.chamadas.append((filtro, pagina, por_pagina))
        return self.vagas, self.total


@pytest.fixture
def repositorio_falso(client):
    def _usar(repositorio: RepositorioFalso) -> RepositorioFalso:
        app.dependency_overrides[get_vaga_repository] = lambda: repositorio
        return repositorio

    return _usar


def test_lista_vazia(client, repositorio_falso):
    repositorio_falso(RepositorioFalso())

    resp = client.get("/vagas")

    assert resp.status_code == 200
    assert resp.json() == {
        "itens": [],
        "total": 0,
        "pagina": 1,
        "por_pagina": 20,
        "total_paginas": 0,
    }


def test_devolve_os_campos_do_schema_sem_a_descricao(client, repositorio_falso):
    repositorio_falso(RepositorioFalso([vaga(7)]))

    item = client.get("/vagas").json()["itens"][0]

    assert item == {
        "id": 7,
        "fonte": "greenhouse",
        "tipo": "estagio",
        "titulo": "Estágio em Dados",
        "empresa": "Acme",
        "cidade": "São Paulo - SP",
        "remoto": False,
        "url": "https://boards.greenhouse.io/acme/jobs/7",
        "publicada_em": None,
        "coletada_em": "2026-12-01T09:00:00Z",
    }


def test_repassa_os_filtros_combinados_ao_repositorio(client, repositorio_falso):
    repositorio = repositorio_falso(RepositorioFalso())

    client.get("/vagas", params={"q": "dados", "cidade": "Curitiba", "remoto": "true"})

    assert repositorio.chamadas == [(FiltroVagas(q="dados", cidade="Curitiba", remoto=True), 1, 20)]


def test_sem_filtros_repassa_tudo_vazio(client, repositorio_falso):
    repositorio = repositorio_falso(RepositorioFalso())

    client.get("/vagas")

    assert repositorio.chamadas == [(FiltroVagas(), 1, 20)]


def test_calcula_total_de_paginas(client, repositorio_falso):
    repositorio = repositorio_falso(RepositorioFalso([vaga(1), vaga(2)], total=45))

    corpo = client.get("/vagas", params={"pagina": 3, "por_pagina": 20}).json()

    assert (corpo["total"], corpo["pagina"], corpo["total_paginas"]) == (45, 3, 3)
    assert repositorio.chamadas[0][1:] == (3, 20)


@pytest.mark.parametrize(
    "params",
    [
        {"por_pagina": 51},
        {"por_pagina": 0},
        {"pagina": 0},
        {"remoto": "talvez"},
        {"q": "x" * 101},
    ],
)
def test_parametros_invalidos_dao_422(client, repositorio_falso, params):
    repositorio = repositorio_falso(RepositorioFalso())

    resp = client.get("/vagas", params=params)

    assert resp.status_code == 422
    assert repositorio.chamadas == []


def test_documentado_no_openapi(client):
    rota = client.get("/openapi.json").json()["paths"]["/vagas"]["get"]

    nomes = {p["name"] for p in rota["parameters"]}
    assert nomes == {"q", "cidade", "remoto", "pagina", "por_pagina"}
    assert rota["summary"] == "Lista as vagas coletadas"
    assert "PaginaVagas" in str(rota["responses"]["200"])
