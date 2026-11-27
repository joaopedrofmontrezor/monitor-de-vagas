import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from app.coletores.base import ColetaParcial
from app.coletores.greenhouse import (
    EMPRESAS_PADRAO,
    ColetorGreenhouse,
    e_estagio,
    e_no_brasil,
    empresas_configuradas,
)
from app.coletores.http import USER_AGENT, ClienteHttp
from app.coletores.registry import RegistroColetores

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "greenhouse"
LISTA_BTG = json.loads((FIXTURES / "btgpactual_jobs.json").read_text(encoding="utf-8"))
DETALHE_BTG = json.loads((FIXTURES / "btgpactual_job_4012001.json").read_text(encoding="utf-8"))


class ApiFalsa:
    def __init__(self) -> None:
        self.recebidas: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.recebidas.append(request)
        caminho = request.url.path.removeprefix("/v1/boards/")
        if caminho == "btgpactual/jobs":
            return httpx.Response(200, json=LISTA_BTG)
        if caminho == "btgpactual/jobs/4012001":
            return httpx.Response(200, json=DETALHE_BTG)
        if caminho == "btgpactual/jobs/4012009":
            return httpx.Response(404, json={"status": 404, "error": "Job not found"})
        if caminho == "btgpactual/jobs/4012002":
            return httpx.Response(500)
        if caminho.startswith("btgpactual/jobs/"):
            id_vaga = int(caminho.rsplit("/", 1)[1])
            job = next(j for j in LISTA_BTG["jobs"] if j["id"] == id_vaga)
            return httpx.Response(200, json=job | {"content": f"&lt;p&gt;Vaga {id_vaga}&lt;/p&gt;"})
        if caminho == "formato_novo/jobs":
            return httpx.Response(200, json={"vagas": []})
        if caminho == "vazia/jobs":
            return httpx.Response(200, json={"jobs": [], "meta": {"total": 0}})
        return httpx.Response(404, json={"status": 404, "error": "Not found"})

    def caminhos(self) -> list[str]:
        return [r.url.path for r in self.recebidas]


@pytest.fixture
def api():
    return ApiFalsa()


@pytest.fixture
def coletor_com(api):
    def _criar(empresas) -> ColetorGreenhouse:
        def criar_cliente() -> ClienteHttp:
            return ClienteHttp(
                transport=httpx.MockTransport(api),
                intervalo_por_dominio=0,
                max_tentativas=1,
                dormir=lambda s: None,
            )

        return ColetorGreenhouse(empresas, criar_cliente=criar_cliente)

    return _criar


def test_extrai_so_estagios_no_brasil_da_fixture(coletor_com):
    vagas = coletor_com({"btgpactual": "BTG Pactual"}).coletar()

    assert len(vagas) == 4
    assert [v.titulo for v in vagas] == [
        "Estagiário(a) de Threat Intelligence",
        "Estágio em Capacitação e Treinamento",
        "Programa BTG Talentos | Estágio de Férias UNICAMP 2027.1",
        "Data Engineering Intern",
    ]


def test_preenche_os_campos_da_vaga_coletada(coletor_com):
    vaga = coletor_com({"btgpactual": "BTG Pactual"}).coletar()[0]

    assert vaga.fonte == "greenhouse"
    assert vaga.tipo == "estagio"
    assert vaga.url == "https://job-boards.greenhouse.io/btgpactual/jobs/4012001"
    assert vaga.empresa == "BTG Pactual"
    assert vaga.cidade == "São Paulo, São Paulo, Brazil"
    assert vaga.descricao.startswith("&lt;h3&gt;Sobre a vaga")
    assert vaga.publicada_em == datetime(2026, 11, 10, 9, 0, tzinfo=timezone(timedelta(hours=-3)))


def test_busca_a_lista_sem_content_e_o_detalhe_so_das_que_passaram(coletor_com, api):
    coletor_com({"btgpactual": None}).coletar()

    assert api.caminhos() == [
        "/v1/boards/btgpactual/jobs",
        "/v1/boards/btgpactual/jobs/4012001",
        "/v1/boards/btgpactual/jobs/4012002",
        "/v1/boards/btgpactual/jobs/4012005",
        "/v1/boards/btgpactual/jobs/4012007",
        "/v1/boards/btgpactual/jobs/4012009",
    ]
    assert all("content" not in r.url.params for r in api.recebidas)
    assert all(r.headers["user-agent"] == USER_AGENT for r in api.recebidas)


def test_vaga_que_saiu_do_ar_no_detalhe_e_ignorada(coletor_com):
    vagas = coletor_com({"btgpactual": None}).coletar()

    assert all(not v.url.endswith("/4012009") for v in vagas)


def test_falha_no_detalhe_mantem_a_vaga_sem_descricao(coletor_com):
    vagas = coletor_com({"btgpactual": None}).coletar()

    vaga = next(v for v in vagas if v.url.endswith("/4012002"))
    assert vaga.titulo == "Estágio em Capacitação e Treinamento"
    assert vaga.cidade == "São Paulo"
    assert vaga.descricao == ""


def test_empresa_da_lista_e_usada_quando_a_api_nao_manda_o_nome():
    sem_nome = LISTA_BTG | {
        "jobs": [{k: v for k, v in LISTA_BTG["jobs"][6].items() if k != "company_name"}]
    }

    def servidor(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/jobs"):
            return httpx.Response(200, json=sem_nome)
        return httpx.Response(200, json=sem_nome["jobs"][0])

    coletor = ColetorGreenhouse(
        {"btgpactual": "BTG Pactual"},
        criar_cliente=lambda: ClienteHttp(
            transport=httpx.MockTransport(servidor), intervalo_por_dominio=0
        ),
    )

    (vaga,) = coletor.coletar()
    assert vaga.empresa == "BTG Pactual"
    assert vaga.descricao == ""


def test_token_com_404_vira_erro_sem_parar_as_outras_empresas(coletor_com):
    coletor = coletor_com({"wellhub": "Wellhub", "btgpactual": None, "formato_novo": None})

    with pytest.raises(ColetaParcial) as parcial:
        coletor.coletar()

    assert len(parcial.value.vagas) == 4
    assert parcial.value.erros == [
        "wellhub: quadro não encontrado (404); o token mudou?",
        "formato_novo: resposta sem a lista 'jobs'",
    ]


def test_quadro_vazio_nao_e_erro(coletor_com):
    assert coletor_com({"vazia": None}).coletar() == []


@pytest.mark.parametrize(
    ("titulo", "esperado"),
    [
        ("Estagiário(a) de Threat Intelligence", True),
        ("Estágio em Dados", True),
        ("ESTAGIO - TI", True),
        ("Estagiária de Marketing", True),
        ("Software Engineering Intern", True),
        ("Summer Internship 2027", True),
        ("Interns Program", True),
        ("Analista de Auditoria Interna", False),
        ("Especialista em Controles Internos", False),
        ("Analista de Internalização", False),
        ("International Sales Manager", False),
        ("Desenvolvedor Júnior", False),
    ],
)
def test_filtro_de_estagio_usa_palavra_inteira(titulo, esperado):
    assert e_estagio(titulo) is esperado


@pytest.mark.parametrize(
    ("local", "esperado"),
    [
        ("São Paulo, São Paulo, Brazil", True),
        ("Remote - Brazil", True),
        ("Brasil", True),
        ("São Paulo", True),
        ("Curitiba | On-site", True),
        ("Campinas", True),
        ("New York, New York, United States", False),
        ("Madrid, ES", False),
        ("Buenos Aires, BA, Argentina", False),
        ("Remote - LATAM", False),
        ("", False),
        (None, False),
    ],
)
def test_filtro_de_brasil_pelo_local(local, esperado):
    assert e_no_brasil(local) is esperado


def test_lista_padrao_tem_as_36_empresas_e_usa_gympass():
    assert len(EMPRESAS_PADRAO) == 36
    assert "gympass" in EMPRESAS_PADRAO
    assert "wellhub" not in EMPRESAS_PADRAO


def test_empresas_configuradas_vazio_usa_a_lista_padrao():
    assert empresas_configuradas("") == EMPRESAS_PADRAO
    assert empresas_configuradas(" , ") == EMPRESAS_PADRAO


def test_empresas_configuradas_le_tokens_separados_por_virgula():
    assert empresas_configuradas(" BTGPactual, nova_empresa,btgpactual ") == {
        "btgpactual": "BTG Pactual",
        "nova_empresa": None,
    }


def test_empresas_configuradas_recusa_token_invalido():
    with pytest.raises(ValueError, match="token inválido: btg pactual"):
        empresas_configuradas("btg pactual,inter")


def test_coletor_cumpre_as_regras_do_registro():
    registro = RegistroColetores()

    registro.registrar(ColetorGreenhouse())

    assert registro.obter("greenhouse").intervalo_horas == 6
