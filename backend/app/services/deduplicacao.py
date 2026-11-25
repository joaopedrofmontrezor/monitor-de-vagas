import hashlib
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

PARAMS_RASTREAMENTO = {"fbclid", "gclid", "ref", "gh_src"}


def normalizar_texto(texto: str | None) -> str:
    if not texto:
        return ""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def url_canonica(url: str) -> str:
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
    base = "|".join(normalizar_texto(x) for x in (titulo, empresa, cidade))
    return hashlib.sha256(base.encode()).hexdigest()
