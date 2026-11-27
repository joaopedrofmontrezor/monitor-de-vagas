import logging
import re
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any

from app.coletores.base import ColetaParcial, VagaColetada
from app.coletores.http import PASTA_CACHE_PADRAO, ClienteHttp, ErroHttp
from app.services.deduplicacao import normalizar_texto
from app.services.normalizacao import e_cidade_conhecida

log = logging.getLogger(__name__)

URL_API = "https://boards-api.greenhouse.io/v1/boards"

EMPRESAS_PADRAO: dict[str, str] = {
    "stone": "Stone",
    "btgpactual": "BTG Pactual",
    "c6bank": "C6 Bank",
    "xpinc": "XP Inc.",
    "agibank": "Agibank",
    "inter": "Inter",
    "clara": "Clara",
    "quintoandar": "QuintoAndar",
    "brex": "Brex",
    "bees": "BEES",
    "gympass": "Wellhub",
    "sumup": "SumUp",
    "ebanx": "EBANX",
    "vtex": "VTEX",
    "wildlifestudios": "Wildlife Studios",
    "braze": "Braze",
    "binance": "Binance",
    "airbnb": "Airbnb",
    "datadog": "Datadog",
    "jusbrasil": "Jusbrasil",
    "bancopan": "Banco PAN",
    "adyen": "Adyen",
    "databricks": "Databricks",
    "ebury": "Ebury",
    "gitlab": "GitLab",
    "figma": "Figma",
    "mongodb": "MongoDB",
    "stripe": "Stripe",
    "coinbase": "Coinbase",
    "rdstation": "RD Station",
    "agilize": "Agilize",
    "carta": "Carta",
    "payoneer": "Payoneer",
    "twilio": "Twilio",
    "pinterest": "Pinterest",
    "elastic": "Elastic",
}

_TOKEN_VALIDO = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_ESTAGIO = re.compile(r"\b(estagio|estagiari[oa]s?|interns?|internships?)\b")
_BRASIL = re.compile(r"\b(brasil|brazil)\b")


def empresas_configuradas(texto: str) -> dict[str, str | None]:
    tokens = [t.strip().lower() for t in texto.split(",") if t.strip()]
    if not tokens:
        return dict(EMPRESAS_PADRAO)
    invalidos = [t for t in tokens if not _TOKEN_VALIDO.match(t)]
    if invalidos:
        raise ValueError(f"GREENHOUSE_EMPRESAS com token inválido: {', '.join(invalidos)}")
    return {t: EMPRESAS_PADRAO.get(t) for t in dict.fromkeys(tokens)}


def e_estagio(titulo: str) -> bool:
    return bool(_ESTAGIO.search(normalizar_texto(titulo)))


def e_no_brasil(local: str | None) -> bool:
    if not local:
        return False
    return bool(_BRASIL.search(normalizar_texto(local))) or e_cidade_conhecida(local)


def criar_cliente_padrao() -> ClienteHttp:
    return ClienteHttp(pasta_cache=PASTA_CACHE_PADRAO)


class ColetorGreenhouse:
    nome = "greenhouse"
    intervalo_horas = 6

    def __init__(
        self,
        empresas: Mapping[str, str | None] | None = None,
        criar_cliente: Callable[[], ClienteHttp] = criar_cliente_padrao,
    ) -> None:
        self.empresas = dict(EMPRESAS_PADRAO if empresas is None else empresas)
        self._criar_cliente = criar_cliente

    def coletar(self) -> list[VagaColetada]:
        vagas: list[VagaColetada] = []
        erros: list[str] = []
        with self._criar_cliente() as cliente:
            for token, nome_empresa in self.empresas.items():
                try:
                    vagas += self._coletar_empresa(cliente, token, nome_empresa)
                except (ErroHttp, ValueError) as exc:
                    log.warning("greenhouse %s: %s", token, exc)
                    erros.append(f"{token}: {_motivo(exc)}")
        log.info("greenhouse: %d estágios no Brasil em %d empresas", len(vagas), len(self.empresas))
        if erros:
            raise ColetaParcial(vagas, erros)
        return vagas

    def _coletar_empresa(
        self, cliente: ClienteHttp, token: str, nome_empresa: str | None
    ) -> list[VagaColetada]:
        resposta = cliente.get_json(f"{URL_API}/{token}/jobs")
        if not isinstance(resposta, dict) or not isinstance(resposta.get("jobs"), list):
            raise ValueError("resposta sem a lista 'jobs'")

        vagas: list[VagaColetada] = []
        for job in resposta["jobs"]:
            if not _passa_no_filtro(job):
                continue
            detalhe = self._detalhe(cliente, token, job)
            if detalhe is None:
                continue
            vagas.append(_para_vaga(job | detalhe, nome_empresa))
        return vagas

    def _detalhe(self, cliente: ClienteHttp, token: str, job: dict[str, Any]) -> dict | None:
        try:
            detalhe = cliente.get_json(f"{URL_API}/{token}/jobs/{job['id']}")
        except ErroHttp as exc:
            if exc.status == 404:
                log.info("greenhouse %s: vaga %s saiu do ar", token, job["id"])
                return None
            log.warning("greenhouse %s: sem descrição da vaga %s (%s)", token, job["id"], exc)
            return job
        return detalhe if isinstance(detalhe, dict) else job


def _passa_no_filtro(job: Any) -> bool:
    if not isinstance(job, dict) or not job.get("id") or not job.get("absolute_url"):
        return False
    return e_estagio(job.get("title") or "") and e_no_brasil(_local(job))


def _para_vaga(job: dict[str, Any], nome_empresa: str | None) -> VagaColetada:
    return VagaColetada(
        fonte="greenhouse",
        url=job["absolute_url"],
        titulo=job["title"],
        empresa=job.get("company_name") or nome_empresa,
        cidade=_local(job),
        descricao=job.get("content") or "",
        publicada_em=_data(job.get("first_published") or job.get("updated_at")),
    )


def _local(job: dict[str, Any]) -> str | None:
    local = job.get("location")
    if isinstance(local, dict):
        return local.get("name") or None
    return None


def _data(valor: Any) -> datetime | None:
    if not isinstance(valor, str):
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return None


def _motivo(exc: Exception) -> str:
    if isinstance(exc, ErroHttp) and exc.status == 404:
        return "quadro não encontrado (404); o token mudou?"
    return str(exc)
