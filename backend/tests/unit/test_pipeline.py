from datetime import UTC, datetime

import pytest

from app.coletores.base import ColetaParcial, VagaColetada
from app.services.deduplicacao import chave_conteudo, url_canonica
from app.services.pipeline import (
    TAMANHO_MAXIMO_ERRO,
    _juntar,
    converter,
    executar_todos,
    para_vaga,
)


def coletada(**campos) -> VagaColetada:
    padrao = {
        "fonte": "greenhouse",
        "url": "https://boards.greenhouse.io/acme/jobs/1?gh_src=abc",
        "titulo": "[Remoto]  Estágio em   Dados",
        "empresa": " Acme ",
        "cidade": "Osasco, Sao Paulo, Brazil",
    }
    return VagaColetada(**(padrao | campos))


def test_para_vaga_normaliza_titulo_cidade_e_empresa():
    vaga = para_vaga(coletada())

    assert vaga.titulo == "Estágio em Dados"
    assert vaga.cidade == "Osasco - SP"
    assert vaga.empresa == "Acme"
    assert vaga.fonte == "greenhouse"
    assert vaga.tipo == "estagio"


def test_para_vaga_calcula_as_chaves_de_dedup_com_os_valores_normalizados():
    vaga = para_vaga(coletada())

    assert vaga.url == "https://boards.greenhouse.io/acme/jobs/1?gh_src=abc"
    assert vaga.url_canonica == url_canonica(vaga.url)
    assert "gh_src" not in vaga.url_canonica
    assert vaga.chave_conteudo == chave_conteudo("Estágio em Dados", "Acme", "Osasco - SP")


def test_mesma_vaga_com_formatos_diferentes_gera_a_mesma_chave():
    a = para_vaga(coletada(titulo="Estágio em Dados", cidade="Osasco - SP"))
    b = para_vaga(coletada(titulo="[Novo] Estágio em Dados", cidade="osasco, sao paulo, brazil"))

    assert a.chave_conteudo == b.chave_conteudo


def test_para_vaga_limpa_o_html_da_descricao():
    vaga = para_vaga(coletada(descricao="&lt;p&gt;Venha &amp; aprenda&lt;/p&gt;<br>Python"))

    assert vaga.descricao == "Venha & aprenda\nPython"


@pytest.mark.parametrize(
    ("campos", "remoto"),
    [
        ({"cidade": "Remote - Brazil"}, True),
        ({"cidade": "São Paulo", "titulo": "Estágio em Dados (remoto)"}, True),
        ({"cidade": "Híbrido em São Paulo/SP", "titulo": "Estágio"}, False),
        ({"cidade": "São Paulo", "titulo": "Estágio", "remoto": True}, True),
    ],
)
def test_para_vaga_detecta_remoto_pela_cidade_ou_pelo_titulo(campos, remoto):
    assert para_vaga(coletada(**campos)).remoto is remoto


def test_para_vaga_corta_textos_maiores_que_as_colunas():
    vaga = para_vaga(coletada(titulo="E" * 400, empresa="A" * 250))

    assert len(vaga.titulo) == 300
    assert len(vaga.empresa) == 200


def test_para_vaga_mantem_data_de_publicacao_e_aceita_campos_vazios():
    publicada = datetime(2026, 11, 20, tzinfo=UTC)
    vaga = para_vaga(coletada(empresa=None, cidade=None, publicada_em=publicada))

    assert vaga.empresa is None
    assert vaga.cidade is None
    assert vaga.publicada_em == publicada


@pytest.mark.parametrize(
    "campos",
    [{"titulo": "[Remoto]"}, {"url": "https://x.com/" + "a" * 2000}],
)
def test_para_vaga_descarta_titulo_vazio_depois_de_limpo_e_url_grande_demais(campos):
    assert para_vaga(coletada(**campos)) is None


def test_converter_pula_as_descartadas_e_mantem_a_ordem():
    vagas = converter(
        [
            coletada(url="https://x.com/1", titulo="Estágio A"),
            coletada(url="https://x.com/2", titulo="[Remoto]"),
            coletada(url="https://x.com/3", titulo="Estágio C"),
        ]
    )

    assert [v.url for v in vagas] == ["https://x.com/1", "https://x.com/3"]


def test_coleta_parcial_guarda_vagas_e_erros():
    parcial = ColetaParcial([coletada()], ["empresa x: 404", "empresa y: timeout"])

    assert len(parcial.vagas) == 1
    assert parcial.erros == ["empresa x: 404", "empresa y: timeout"]
    assert str(parcial) == "empresa x: 404; empresa y: timeout"


def test_juntar_erros_corta_texto_muito_grande():
    assert _juntar([]) is None
    assert _juntar(["a", "b"]) == "a; b"
    longo = _juntar(["x" * 5000])
    assert len(longo) == TAMANHO_MAXIMO_ERRO
    assert longo.endswith("...")


class ColetorFalso:
    intervalo_horas = 6

    def __init__(self, nome: str) -> None:
        self.nome = nome

    def coletar(self) -> list[VagaColetada]:
        return []


def test_executar_todos_segue_em_frente_quando_o_banco_falha():
    def sessao_que_falha():
        raise ConnectionError("banco fora do ar")

    resultados = executar_todos([ColetorFalso("a"), ColetorFalso("b")], sessao_que_falha)

    assert [r.coletor for r in resultados] == ["a", "b"]
    assert all(r.erro == "ConnectionError: banco fora do ar" for r in resultados)
