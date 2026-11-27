import html
import re

from bs4 import BeautifulSoup

from app.services.deduplicacao import normalizar_texto

UFS = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}
_UF_POR_NOME = {normalizar_texto(nome): uf for uf, nome in UFS.items()}


_CIDADES = [
    ("Rio Branco", "AC"),
    ("Maceió", "AL"),
    ("Macapá", "AP"),
    ("Manaus", "AM"),
    ("Salvador", "BA"),
    ("Fortaleza", "CE"),
    ("Brasília", "DF"),
    ("Vitória", "ES"),
    ("Goiânia", "GO"),
    ("São Luís", "MA"),
    ("Cuiabá", "MT"),
    ("Campo Grande", "MS"),
    ("Belo Horizonte", "MG"),
    ("Belém", "PA"),
    ("João Pessoa", "PB"),
    ("Curitiba", "PR"),
    ("Recife", "PE"),
    ("Teresina", "PI"),
    ("Rio de Janeiro", "RJ"),
    ("Natal", "RN"),
    ("Porto Alegre", "RS"),
    ("Porto Velho", "RO"),
    ("Boa Vista", "RR"),
    ("Florianópolis", "SC"),
    ("São Paulo", "SP"),
    ("Aracaju", "SE"),
    ("Palmas", "TO"),
    ("Osasco", "SP"),
    ("Barueri", "SP"),
    ("Campinas", "SP"),
    ("Guarulhos", "SP"),
    ("Santo André", "SP"),
    ("São Bernardo do Campo", "SP"),
    ("São José dos Campos", "SP"),
    ("Ribeirão Preto", "SP"),
    ("Sorocaba", "SP"),
    ("Santos", "SP"),
    ("Jundiaí", "SP"),
    ("Niterói", "RJ"),
    ("Contagem", "MG"),
    ("Betim", "MG"),
    ("Uberlândia", "MG"),
    ("Joinville", "SC"),
    ("Blumenau", "SC"),
    ("Londrina", "PR"),
    ("Maringá", "PR"),
    ("Caxias do Sul", "RS"),
]
_CIDADE_POR_NOME = {normalizar_texto(nome): (nome, uf) for nome, uf in _CIDADES}


_APELIDOS = {
    "sp": "São Paulo - SP",
    "sampa": "São Paulo - SP",
    "rj": "Rio de Janeiro - RJ",
    "bh": "Belo Horizonte - MG",
    "poa": "Porto Alegre - RS",
    "bsb": "Brasília - DF",
    "df": "Brasília - DF",
}


_RUIDO = {
    "remoto",
    "remota",
    "remote",
    "hibrido",
    "hybrid",
    "presencial",
    "on-site",
    "onsite",
    "home office",
    "brasil",
    "brazil",
    "br",
}
_NAO_INFORMADO = re.compile(r"nao informad|a definir|a combinar|^n/?a$")
_PREFIXO_MODALIDADE = re.compile(
    r"^\s*(remote|remoto|h[ií]brido|hybrid|presencial)\s*(in|em|-|–|:)?\s+", re.IGNORECASE
)
_VARIOS_LOCAIS = re.compile(r";|\s+(?:or|ou)\s+", re.IGNORECASE)

_SEPARADORES = re.compile(r"\s+[-–]\s+|[/,|]|\s*[-–]\s*(?=[A-Za-z]{2}\s*$)")
_MINUSCULAS = {"de", "da", "do", "das", "dos", "e"}


def limpar_html(texto: str | None) -> str:
    if not texto:
        return ""
    sopa = BeautifulSoup(html.unescape(texto), "html.parser")
    for tag in sopa(["script", "style"]):
        tag.decompose()
    for br in sopa.find_all("br"):
        br.replace_with("\n")
    linhas = (linha.replace("\xa0", " ").strip() for linha in sopa.get_text("\n").splitlines())
    sem_vazias = [re.sub(r"\s+", " ", linha) for linha in linhas if linha]
    return "\n".join(sem_vazias)


def limpar_titulo(titulo: str | None) -> str:
    if not titulo:
        return ""
    sem_etiqueta = re.sub(r"^\s*(\[[^\]]*\]\s*)+", "", titulo)
    return re.sub(r"\s+", " ", sem_etiqueta).strip()


def normalizar_cidade(local: str | None) -> str | None:
    if not local:
        return None
    texto = re.sub(r"\(.*?\)|[\[\]]", " ", local)
    texto = _VARIOS_LOCAIS.split(texto)[0]
    texto = _PREFIXO_MODALIDADE.sub("", texto)

    normalizado = normalizar_texto(texto)
    if not normalizado or _NAO_INFORMADO.search(normalizado):
        return None
    if normalizado in _APELIDOS:
        return _APELIDOS[normalizado]

    partes = [p.strip() for p in _SEPARADORES.split(texto) if p.strip()]
    partes = [p for p in partes if normalizar_texto(p) not in _RUIDO]
    if not partes:
        return None

    cidade, *resto = partes
    if _uf_de(cidade) and normalizar_texto(cidade) not in _CIDADE_POR_NOME:
        return None

    nome, uf_padrao = _CIDADE_POR_NOME.get(normalizar_texto(cidade), (_titulo(cidade), None))
    uf = next((u for u in map(_uf_de, resto) if u), uf_padrao)
    return f"{nome} - {uf}" if uf else nome


def e_cidade_conhecida(local: str | None) -> bool:
    cidade = normalizar_cidade(local)
    if not cidade:
        return False
    nome = cidade.rsplit(" - ", 1)[0]
    return normalizar_texto(nome) in _CIDADE_POR_NOME


def detectar_remoto(*textos: str | None) -> bool:
    for texto in textos:
        normalizado = normalizar_texto(texto)
        achados = [
            (m.start(), remoto)
            for padrao, remoto in _SINAIS_MODALIDADE
            if (m := padrao.search(normalizado))
        ]
        if achados:
            return min(achados)[1]
    return False


_NEGACAO = r"\b(nao|sem)\s+(e\s+|sera\s+|aceita\s+|ha\s+|tem\s+)?(remot|home[\s-]?office)"
_REMOTO = r"\b(remot[oa]s?|remote|home[\s-]?office|teletrabalho|trabalho a distancia)\b"
_SINAIS_MODALIDADE = [
    (re.compile(_NEGACAO), False),
    (re.compile(_REMOTO), True),
    (re.compile(r"\b(hibrid[oa]s?|hybrid)\b"), False),
    (re.compile(r"\b(presencial|on[\s-]?site)\b"), False),
]


def _uf_de(parte: str) -> str | None:
    if parte.strip().upper() in UFS:
        return parte.strip().upper()
    return _UF_POR_NOME.get(normalizar_texto(parte))


def _titulo(texto: str) -> str:

    def maiuscula(palavra: str) -> str:
        return "-".join(p[:1].upper() + p[1:] for p in palavra.split("-"))

    palavras = texto.strip().lower().split()
    return " ".join(
        p if (i > 0 and p in _MINUSCULAS) else maiuscula(p) for i, p in enumerate(palavras)
    )
