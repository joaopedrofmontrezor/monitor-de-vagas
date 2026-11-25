import pytest

from app.services.deduplicacao import chave_conteudo, normalizar_texto, url_canonica
from app.services.normalizacao import normalizar_cidade


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("HTTPS://Site.com/vaga/1/?utm_source=x&id=9", "https://site.com/vaga/1?id=9"),
        ("https://site.com/vaga/1#descricao", "https://site.com/vaga/1"),
        ("https://site.com/v?b=2&a=1&gclid=abc", "https://site.com/v?a=1&b=2"),
        ("  https://site.com/vaga/1  ", "https://site.com/vaga/1"),
        ("https://site.com/vaga/1?fbclid=x&ref=linkedin&UTM_Campaign=y", "https://site.com/vaga/1"),
        
        (
            "https://empresa.com/carreiras?gh_jid=8243837002&gh_src=abc123",
            "https://empresa.com/carreiras?gh_jid=8243837002",
        ),
        
        ("https://site.com/Vaga/ABC", "https://site.com/Vaga/ABC"),
        ("https://site.com/busca?q=&pagina=2", "https://site.com/busca?pagina=2&q="),
    ],
)
def test_url_canonica(entrada, esperado):
    assert url_canonica(entrada) == esperado


def test_url_canonica_e_idempotente():
    url = "HTTPS://Site.com/vaga/1/?utm_source=x&id=9#topo"
    assert url_canonica(url_canonica(url)) == url_canonica(url)


def test_normalizar_texto_remove_acento_caixa_e_espacos():
    assert normalizar_texto("  Estágio   em DADOS ") == "estagio em dados"
    assert normalizar_texto("Ação\tçÃO\n") == "acao cao"
    assert normalizar_texto(None) == ""


def test_chave_igual_para_mesma_vaga_escrita_diferente():
    a = chave_conteudo("Estágio  em Dados", "ACME", "São Paulo")
    b = chave_conteudo("estagio em dados", "acme", "sao paulo")
    assert a == b


def test_chave_diferente_para_cidades_diferentes():
    assert chave_conteudo("Estágio", "ACME", "SP") != chave_conteudo("Estágio", "ACME", "RJ")


def test_chave_aceita_empresa_e_cidade_vazias():
    assert chave_conteudo("Estágio", None, None) == chave_conteudo("estágio", "", "")
    assert len(chave_conteudo("Estágio", None, None)) == 64  


def test_chave_com_cidade_normalizada_junta_fontes_diferentes():
    """O motivo de normalizar a cidade ANTES de calcular a chave."""
    cidade_greenhouse = normalizar_cidade("Osasco, Sao Paulo, Brazil")
    cidade_github = normalizar_cidade("Osasco - SP")
    greenhouse = chave_conteudo("Estágio em Dados", "ACME", cidade_greenhouse)
    github = chave_conteudo("Estágio em Dados", "ACME", cidade_github)
    assert greenhouse == github
