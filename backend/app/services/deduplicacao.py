"""Chaves de deduplicação: a mesma vaga nunca entra duas vezes no banco.

Duas chaves, as duas com UNIQUE no Postgres (issue #3):
- `url_canonica`: a mesma URL escrita de jeitos diferentes (maiúsculas, utm_*, #âncora).
- `chave_conteudo`: a mesma vaga publicada em sites diferentes (título|empresa|cidade).

São funções puras (sem banco, sem rede): os testes rodam em milissegundos.
"""

import hashlib
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


PARAMS_RASTREAMENTO = {"fbclid", "gclid", "ref", "gh_src"}


def normalizar_texto(texto: str | None) -> str:
    """Minúsculas, sem acento e com espaços colapsados."""
    if not texto:
        return ""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def url_canonica(url: str) -> str:
    """Remove parâmetros de rastreamento, fragmento e barra final.

    O caminho mantém maiúsculas e minúsculas: em muitos sites `/Vaga/1` e `/vaga/1`
    são páginas diferentes. Já esquema e domínio não diferenciam caixa.
    """
    partes = urlsplit(url.strip())
    query = [
        (k, v)
        for k, v in parse_qsl(partes.query, keep_blank_values=True)
        if not (k.lower().startswith("utm_") or k.lower() in PARAMS_RASTREAMENTO)
    ]
    return urlunsplit(
        (
            partes.scheme.lower(),
            partes.netloc.lower(),
            partes.path.rstrip("/"),
            urlencode(sorted(query)),
            "",
        )
    )


def chave_conteudo(titulo: str, empresa: str | None, cidade: str | None) -> str:
    """Mesma vaga publicada em sites diferentes gera a mesma chave.

    Passe a cidade JÁ normalizada (`normalizacao.normalizar_cidade`): assim
    "São Paulo/SP" e "Sao Paulo, São Paulo, Brazil" viram a mesma chave.

    Limitação aceita no MVP: duas vagas da mesma empresa, com o mesmo título e na
    mesma cidade, viram uma só.
    """
    base = "|".join(normalizar_texto(x) for x in (titulo, empresa, cidade))
    return hashlib.sha256(base.encode()).hexdigest()
