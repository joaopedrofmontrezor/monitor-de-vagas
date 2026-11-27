import base64
import hashlib
import json
import logging
import time
from collections.abc import Callable, Mapping
from pathlib import Path

import httpx

log = logging.getLogger(__name__)

USER_AGENT = "MonitorDeVagas/0.1 (+https://github.com/joaopedrofmontrezor/monitor-de-vagas)"
PASTA_CACHE_PADRAO = Path(".cache/http")
TIMEOUT_S = 15.0
INTERVALO_POR_DOMINIO_S = 2.0
MAX_TENTATIVAS = 3
ESPERA_BASE_S = 1.0
ESPERA_MAXIMA_S = 60.0
VALIDADE_CACHE_S = 3600.0


class ErroHttp(Exception):
    def __init__(self, mensagem: str, status: int | None = None) -> None:
        super().__init__(mensagem)
        self.status = status


class ClienteHttp:
    def __init__(
        self,
        *,
        timeout: float = TIMEOUT_S,
        intervalo_por_dominio: float = INTERVALO_POR_DOMINIO_S,
        max_tentativas: int = MAX_TENTATIVAS,
        espera_base: float = ESPERA_BASE_S,
        pasta_cache: Path | None = None,
        validade_cache: float = VALIDADE_CACHE_S,
        transport: httpx.BaseTransport | None = None,
        relogio: Callable[[], float] = time.monotonic,
        agora: Callable[[], float] = time.time,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self._http = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            follow_redirects=True,
            transport=transport,
        )
        self._intervalo = intervalo_por_dominio
        self._max_tentativas = max_tentativas
        self._espera_base = espera_base
        self._pasta_cache = pasta_cache
        self._validade_cache = validade_cache
        self._relogio = relogio
        self._agora = agora
        self._dormir = dormir
        self._ultima_por_dominio: dict[str, float] = {}

    def __enter__(self) -> "ClienteHttp":
        return self

    def __exit__(self, *_: object) -> None:
        self.fechar()

    def fechar(self) -> None:
        self._http.close()

    def get(self, url: str, params: Mapping[str, str | int] | None = None) -> httpx.Response:
        requisicao = self._http.build_request("GET", url, params=params)
        em_cache = self._ler_cache(requisicao)
        if em_cache is not None:
            log.debug("cache: %s", requisicao.url)
            return em_cache

        resposta = self._enviar_com_retry(requisicao)
        self._gravar_cache(resposta)
        return resposta

    def get_json(self, url: str, params: Mapping[str, str | int] | None = None) -> object:
        resposta = self.get(url, params)
        try:
            return resposta.json()
        except ValueError:
            raise ErroHttp(f"{resposta.request.url} não devolveu JSON válido") from None

    def _enviar_com_retry(self, requisicao: httpx.Request) -> httpx.Response:
        for tentativa in range(1, self._max_tentativas + 1):
            self._esperar_vez(requisicao.url.host)
            try:
                resposta = self._http.send(requisicao)
            except httpx.TransportError as exc:
                motivo = f"falha de rede ({type(exc).__name__})"
                status = None
                espera = self._espera_exponencial(tentativa)
            else:
                if resposta.status_code < 400:
                    return resposta
                if resposta.status_code != 429 and resposta.status_code < 500:
                    raise ErroHttp(
                        f"{requisicao.url} respondeu {resposta.status_code}",
                        status=resposta.status_code,
                    )
                motivo = f"status {resposta.status_code}"
                status = resposta.status_code
                espera = _retry_after(resposta) or self._espera_exponencial(tentativa)

            if tentativa == self._max_tentativas:
                raise ErroHttp(
                    f"{requisicao.url}: {motivo} após {tentativa} tentativas", status=status
                )
            if espera > ESPERA_MAXIMA_S:
                raise ErroHttp(
                    f"{requisicao.url}: servidor pediu {espera:.0f}s de espera", status=status
                )
            log.warning(
                "%s: %s, nova tentativa em %.1fs (%s/%s)",
                requisicao.url.host,
                motivo,
                espera,
                tentativa,
                self._max_tentativas,
            )
            self._dormir(espera)
        raise AssertionError("inalcançável")

    def _espera_exponencial(self, tentativa: int) -> float:
        return self._espera_base * 2 ** (tentativa - 1)

    def _esperar_vez(self, dominio: str) -> None:
        ultima = self._ultima_por_dominio.get(dominio)
        if ultima is not None:
            falta = self._intervalo - (self._relogio() - ultima)
            if falta > 0:
                self._dormir(falta)
        self._ultima_por_dominio[dominio] = self._relogio()

    def _arquivo_cache(self, url: httpx.URL) -> Path | None:
        if self._pasta_cache is None:
            return None
        chave = hashlib.sha256(str(url).encode()).hexdigest()
        return self._pasta_cache / url.host / f"{chave}.json"

    def _ler_cache(self, requisicao: httpx.Request) -> httpx.Response | None:
        arquivo = self._arquivo_cache(requisicao.url)
        if arquivo is None or not arquivo.exists():
            return None
        try:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            if self._agora() - dados["salvo_em"] > self._validade_cache:
                return None
            corpo = base64.b64decode(dados["corpo"])
        except (ValueError, KeyError):
            return None
        return httpx.Response(
            dados["status"],
            content=corpo,
            headers={"content-type": dados.get("content_type", "")},
            request=requisicao,
        )

    def _gravar_cache(self, resposta: httpx.Response) -> None:
        arquivo = self._arquivo_cache(resposta.request.url)
        if arquivo is None or resposta.status_code != 200:
            return
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        dados = {
            "url": str(resposta.request.url),
            "salvo_em": self._agora(),
            "status": resposta.status_code,
            "content_type": resposta.headers.get("content-type", ""),
            "corpo": base64.b64encode(resposta.content).decode(),
        }
        arquivo.write_text(json.dumps(dados), encoding="utf-8")


def _retry_after(resposta: httpx.Response) -> float | None:
    valor = resposta.headers.get("retry-after", "")
    try:
        return max(float(valor), 0.0)
    except ValueError:
        return None
