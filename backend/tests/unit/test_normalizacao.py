import pytest

from app.services.normalizacao import (
    detectar_remoto,
    limpar_html,
    limpar_titulo,
    normalizar_cidade,
)


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("São Paulo - SP", "São Paulo - SP"),
        ("sp", "São Paulo - SP"),
        ("São Paulo/SP", "São Paulo - SP"),
        ("São Paulo, São Paulo, Brazil", "São Paulo - SP"),
        ("Osasco, SP", "Osasco - SP"),
        ("Osasco, Sao Paulo, Brazil", "Osasco - SP"),
        ("Ribeirao Preto, Sao Paulo, Brazil", "Ribeirão Preto - SP"),
        ("Campo Grande, Mato Grosso Do Sul, Brazil", "Campo Grande - MS"),
        (
            "Belo Horizonte, Minas Gerais, Brazil; São Paulo, São Paulo, Brazil",
            "Belo Horizonte - MG",
        ),
        ("Curitiba | On-site", "Curitiba - PR"),
        ("Curitiba or São Paulo | On-site", "Curitiba - PR"),
        ("Rio de Janeiro; São Paulo", "Rio de Janeiro - RJ"),
        ("Remote in Buenos Aires", "Buenos Aires"),
        ("Híbrido em São Paulo/SP", "São Paulo - SP"),
        ("Híbrido - São Paulo, SP (Av. Brigadeiro Faria Lima, 2391, cj 7)", "São Paulo - SP"),
        ("Vila Olímpia - SP", "Vila Olímpia - SP"),
        ("[HÍBRIDO - SP]", "São Paulo - SP"),
        ("São Paulo / SP", "São Paulo - SP"),
        ("Betim / MG", "Betim - MG"),
        ("SAO PAULO-SP", "São Paulo - SP"),
        ("  florianopolis  ", "Florianópolis - SC"),
        ("SÃO JOSÉ DO RIO PRETO / SP", "São José do Rio Preto - SP"),
        ("Embu-Guaçu, SP", "Embu-Guaçu - SP"),
    ],
)
def test_normalizar_cidade(entrada, esperado):
    assert normalizar_cidade(entrada) == esperado


@pytest.mark.parametrize(
    "entrada",
    [
        None,
        "",
        "Remoto",
        "Brasil",
        "Brazil",
        "Remoto - Brasil",
        "Localização não informada",
        "Minas Gerais",
        "MG",
        "n/a",
    ],
)
def test_normalizar_cidade_sem_cidade_devolve_none(entrada):
    assert normalizar_cidade(entrada) is None


def test_mesma_cidade_escrita_de_jeitos_diferentes_vira_uma_so():
    formas = {
        normalizar_cidade(x)
        for x in ["São Paulo - SP", "sp", "São Paulo/SP", "Sao Paulo, Sao Paulo, Brazil"]
    }
    assert formas == {"São Paulo - SP"}


@pytest.mark.parametrize(
    ("textos", "esperado"),
    [
        (("Remoto",), True),
        (("Trabalho Remoto.",), True),
        (("nosso trabalho é 100% remoto",), True),
        (("Home office",), True),
        (("Remote in Buenos Aires",), True),
        (("Remoto (com possibilidade de Híbrido/Presencial a depender do acordo)",), True),
        (("Híbrido: 3x presencial e 2x remoto",), False),
        (("modelo presencial com flexibilidade (3x por semana no escritório)",), False),
        (("Curitiba | On-site",), False),
        (("Esta vaga não é remota",), False),
        (("Presencial, sem home office",), False),
        (("Experiência com remoção de dados",), False),
        (("São Paulo - SP", "[Remoto] Estágio em Dados"), True),
        (("Híbrido", "[Remoto] Estágio em Dados"), False),
        ((None, "", "Estágio em Dados"), False),
        ((), False),
    ],
)
def test_detectar_remoto(textos, esperado):
    assert detectar_remoto(*textos) is esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("[Remoto] Estágio na ANDA", "Estágio na ANDA"),
        ("[HÍBRIDO - SP] Engenheiro(a) de Software", "Engenheiro(a) de Software"),
        ("[Híbrido/SP] [Júnior]  Front-end   Developer", "Front-end Developer"),
        ("Estágio em Dados [2026]", "Estágio em Dados [2026]"),
        (None, ""),
    ],
)
def test_limpar_titulo(entrada, esperado):
    assert limpar_titulo(entrada) == esperado


def test_limpar_html_escapado_do_greenhouse():
    entrada = (
        "&lt;p&gt;&lt;strong&gt;Sobre a vaga&lt;/strong&gt;&lt;/p&gt;"
        "&lt;ul&gt;&lt;li&gt;Python&lt;/li&gt;&lt;li&gt;SQL&amp;nbsp;básico&lt;/li&gt;&lt;/ul&gt;"
    )
    assert limpar_html(entrada) == "Sobre a vaga\nPython\nSQL básico"


def test_limpar_html_com_br_e_espacos():
    entrada = "<div>Linha 1<br>Linha    2<br/><br/>   </div><p>\n\n Linha 3 </p><script>x</script>"
    assert limpar_html(entrada) == "Linha 1\nLinha 2\nLinha 3"


def test_limpar_html_vazio():
    assert limpar_html(None) == ""
    assert limpar_html("") == ""
