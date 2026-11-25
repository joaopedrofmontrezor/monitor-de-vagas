import argparse
import html
import logging
import time
from collections.abc import Callable
from typing import Protocol

import httpx

from app.config import settings

log = logging.getLogger(__name__)

API_TELEGRAM = "https://api.telegram.org"
ESPERA_MAXIMA_S = 30
LIMITE_TITULO = 200


class ErroTelegram(Exception):
    pass


class VagaParaAlerta(Protocol):
    titulo: str
    url: str
    empresa: str | None
    cidade: str | None
    remoto: bool


def formatar_vaga(vaga: VagaParaAlerta) -> str:
    titulo = vaga.titulo.strip()
    if len(titulo) > LIMITE_TITULO:
        titulo = titulo[: LIMITE_TITULO - 1].rstrip() + "…"

    locais = [x for x in (vaga.cidade, "Remoto" if vaga.remoto else None) if x]
    linhas = [f"<b>{html.escape(titulo)}</b>"]
    if vaga.empresa:
        linhas.append(f"🏢 {html.escape(vaga.empresa)}")
    linhas.append(f"📍 {html.escape(' · '.join(locais) or 'Local não informado')}")
    linhas.append(f'🔗 <a href="{html.escape(vaga.url, quote=True)}">Ver vaga</a>')
    return "\n".join(linhas)


class ClienteTelegram:
    def __init__(
        self,
        token: str,
        *,
        http: httpx.Client | None = None,
        max_tentativas: int = 3,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN vazio: configure o .env (ver README)")
        self._url = f"{API_TELEGRAM}/bot{token}/sendMessage"
        self._http = http or httpx.Client(timeout=10)
        self._max_tentativas = max_tentativas
        self._dormir = dormir

    def enviar(self, chat_id: int | str, texto: str) -> None:
        corpo = {
            "chat_id": chat_id,
            "text": texto,
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": True},
        }
        for tentativa in range(1, self._max_tentativas + 1):
            try:
                resp = self._http.post(self._url, json=corpo)
            except httpx.HTTPError as exc:
                raise ErroTelegram(
                    f"falha de rede ao falar com o Telegram ({type(exc).__name__})"
                ) from None

            if resp.status_code == 200:
                return

            dados = _json_ou_vazio(resp)
            descricao = dados.get("description", "sem descrição")
            pode_repetir = resp.status_code == 429 or resp.status_code >= 500
            if not pode_repetir or tentativa == self._max_tentativas:
                raise ErroTelegram(f"Telegram respondeu {resp.status_code}: {descricao}")

            espera = float(dados.get("parameters", {}).get("retry_after", 2**tentativa))
            if espera > ESPERA_MAXIMA_S:
                raise ErroTelegram(f"Telegram pediu para esperar {espera:.0f}s; desistindo")
            log.warning(
                "Telegram respondeu %s, nova tentativa em %.0fs (%s/%s)",
                resp.status_code,
                espera,
                tentativa,
                self._max_tentativas,
            )
            self._dormir(espera)


def _json_ou_vazio(resp: httpx.Response) -> dict:
    try:
        dados = resp.json()
    except ValueError:
        return {}
    return dados if isinstance(dados, dict) else {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Envia uma mensagem de teste pelo bot")
    parser.add_argument("--chat-id", required=True, help="seu chat_id (veja o README)")
    parser.add_argument("texto", nargs="?", default="Teste do Monitor de Vagas ✅")
    args = parser.parse_args(argv)

    try:
        ClienteTelegram(settings.telegram_bot_token).enviar(args.chat_id, args.texto)
    except (ValueError, ErroTelegram) as exc:
        print(f"Erro: {exc}")
        return 1
    print("Mensagem enviada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
