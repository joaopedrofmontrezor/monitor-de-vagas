from datetime import UTC, datetime, timedelta

import pytest

from app.models import Vaga
from app.services.deduplicacao import chave_conteudo, url_canonica

pytestmark = pytest.mark.integracao

INICIO = datetime(2026, 12, 1, 9, 0, tzinfo=UTC)


@pytest.fixture
def com_vagas(sessao, client, sobrescrever_db):
    def _criar(*vagas: dict) -> None:
        for i, dados in enumerate(vagas):
            url = f"https://x.com/vagas/{i}"
            titulo = dados.get("titulo", f"Estágio {i}")
            cidade = dados.get("cidade", "São Paulo - SP")
            empresa = dados.get("empresa", "Acme")
            sessao.add(
                Vaga(
                    fonte="greenhouse",
                    titulo=titulo,
                    empresa=empresa,
                    cidade=cidade,
                    remoto=dados.get("remoto", False),
                    url=url,
                    url_canonica=url_canonica(url),
                    chave_conteudo=chave_conteudo(titulo, empresa, cidade),
                    coletada_em=INICIO + timedelta(hours=i),
                )
            )
        sessao.flush()
        sobrescrever_db(sessao)

    return _criar


def titulos(resp) -> list[str]:
    return [v["titulo"] for v in resp.json()["itens"]]


def test_lista_vazia_com_banco_de_verdade(com_vagas, client):
    com_vagas()

    corpo = client.get("/vagas").json()

    assert (corpo["itens"], corpo["total"], corpo["total_paginas"]) == ([], 0, 0)


def test_mais_recentes_primeiro(com_vagas, client):
    com_vagas({"titulo": "Antiga"}, {"titulo": "Do meio"}, {"titulo": "Nova"})

    assert titulos(client.get("/vagas")) == ["Nova", "Do meio", "Antiga"]


def test_busca_no_titulo_ignora_acento_e_maiuscula(com_vagas, client):
    com_vagas({"titulo": "Estágio em Dados"}, {"titulo": "ESTÁGIO Front-end"}, {"titulo": "Júnior"})

    assert titulos(client.get("/vagas", params={"q": "estagio"})) == [
        "ESTÁGIO Front-end",
        "Estágio em Dados",
    ]


def test_busca_trata_porcentagem_como_texto(com_vagas, client):
    com_vagas({"titulo": "Estágio 100% remoto"}, {"titulo": "Estágio 100 vagas"})

    assert titulos(client.get("/vagas", params={"q": "100%"})) == ["Estágio 100% remoto"]


def test_cidade_casa_pelo_comeco_sem_acento(com_vagas, client):
    com_vagas(
        {"titulo": "A", "cidade": "São Paulo - SP"},
        {"titulo": "B", "cidade": "São José dos Campos - SP"},
        {"titulo": "C", "cidade": None},
    )

    assert titulos(client.get("/vagas", params={"cidade": "sao paulo"})) == ["A"]


@pytest.mark.parametrize(("remoto", "esperado"), [("true", ["Remota"]), ("false", ["Local"])])
def test_filtro_remoto(com_vagas, client, remoto, esperado):
    com_vagas({"titulo": "Remota", "remoto": True}, {"titulo": "Local", "remoto": False})

    assert titulos(client.get("/vagas", params={"remoto": remoto})) == esperado


def test_filtros_combinados(com_vagas, client):
    com_vagas(
        {"titulo": "Estágio Dados", "cidade": "Curitiba - PR", "remoto": True},
        {"titulo": "Estágio Dados", "cidade": "Curitiba - PR", "remoto": False, "empresa": "B"},
        {"titulo": "Estágio Front", "cidade": "Curitiba - PR", "remoto": True},
        {"titulo": "Estágio Dados SP", "cidade": "São Paulo - SP", "remoto": True},
    )

    resp = client.get("/vagas", params={"q": "dados", "cidade": "curitiba", "remoto": "true"})

    assert resp.json()["total"] == 1
    assert resp.json()["itens"][0]["cidade"] == "Curitiba - PR"
    assert resp.json()["itens"][0]["remoto"] is True


def test_paginacao(com_vagas, client):
    com_vagas(*({"titulo": f"Vaga {i}"} for i in range(5)))

    pagina_1 = client.get("/vagas", params={"por_pagina": 2, "pagina": 1}).json()
    pagina_3 = client.get("/vagas", params={"por_pagina": 2, "pagina": 3}).json()
    depois_do_fim = client.get("/vagas", params={"por_pagina": 2, "pagina": 4}).json()

    assert [v["titulo"] for v in pagina_1["itens"]] == ["Vaga 4", "Vaga 3"]
    assert [v["titulo"] for v in pagina_3["itens"]] == ["Vaga 0"]
    assert (pagina_1["total"], pagina_1["total_paginas"]) == (5, 3)
    assert depois_do_fim["itens"] == [] and depois_do_fim["total"] == 5
