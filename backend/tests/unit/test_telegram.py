import json
from dataclasses import dataclass

import httpx
import pytest

from app.notificacoes import telegram
from app.notificacoes.telegram import ClienteTelegram, ErroTelegram, formatar_vaga

TOKEN = "123456:TOKEN-DE-TESTE"


@dataclass
class VagaFake:
    titulo: str = "Estágio em Dados"
    url: str = "https://empresa.com/vagas/1"
    empresa: str | None = "ACME"
    cidade: str | None = "São Paulo - SP"
    remoto: bool = False


def cliente_com(respostas, chamadas):
    fila = list(respostas)

    def responder(request: httpx.Request) -> httpx.Response:
        chamadas.append(request)
        resposta = fila.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    esperas = []
    cliente = ClienteTelegram(
        TOKEN,
        http=httpx.Client(transport=httpx.MockTransport(responder)),
        dormir=esperas.append,
    )
    return cliente, esperas


def ok():
    return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})


def limite(retry_after):
    return httpx.Response(
        429,
        json={
            "ok": False,
            "error_code": 429,
            "description": "Too Many Requests: retry after 3",
            "parameters": {"retry_after": retry_after},
        },
    )


def test_enviar_chama_sendmessage_com_o_corpo_certo():
    chamadas = []
    cliente, _ = cliente_com([ok()], chamadas)

    cliente.enviar(987, "<b>oi</b>")

    assert len(chamadas) == 1
    req = chamadas[0]
    assert req.method == "POST"
    assert str(req.url) == f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    corpo = json.loads(req.content)
    assert corpo == {
        "chat_id": 987,
        "text": "<b>oi</b>",
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
    }


def test_429_espera_o_retry_after_e_tenta_de_novo():
    chamadas = []
    cliente, esperas = cliente_com([limite(3), ok()], chamadas)

    cliente.enviar(987, "oi")

    assert len(chamadas) == 2
    assert esperas == [3.0]


def test_5xx_tambem_tenta_de_novo_com_espera_crescente():
    chamadas = []
    cliente, esperas = cliente_com([httpx.Response(502), httpx.Response(503), ok()], chamadas)

    cliente.enviar(987, "oi")

    assert len(chamadas) == 3
    assert esperas == [2.0, 4.0]


def test_429_em_todas_as_tentativas_levanta_erro():
    chamadas = []
    cliente, esperas = cliente_com([limite(1), limite(1), limite(1)], chamadas)

    with pytest.raises(ErroTelegram, match="429"):
        cliente.enviar(987, "oi")
    assert len(chamadas) == 3
    assert esperas == [1.0, 1.0]


def test_retry_after_longo_demais_desiste_sem_travar_o_worker():
    chamadas = []
    cliente, esperas = cliente_com([limite(120)], chamadas)

    with pytest.raises(ErroTelegram, match="esperar 120s"):
        cliente.enviar(987, "oi")
    assert esperas == []


def test_erro_400_nao_tenta_de_novo():
    chamadas = []
    resp = httpx.Response(400, json={"ok": False, "description": "Bad Request: chat not found"})
    cliente, _ = cliente_com([resp], chamadas)

    with pytest.raises(ErroTelegram, match="chat not found"):
        cliente.enviar(987, "oi")
    assert len(chamadas) == 1


def test_resposta_sem_json_nao_quebra():
    chamadas = []
    cliente, _ = cliente_com([httpx.Response(403, text="<html>Forbidden</html>")], chamadas)

    with pytest.raises(ErroTelegram, match="403: sem descrição"):
        cliente.enviar(987, "oi")


def test_erro_http_nao_expoe_o_token():
    chamadas = []
    resp = httpx.Response(401, json={"ok": False, "description": "Unauthorized"})
    cliente, _ = cliente_com([resp], chamadas)

    with pytest.raises(ErroTelegram) as exc_info:
        cliente.enviar(987, "oi")
    assert TOKEN not in str(exc_info.value)


def test_erro_de_rede_nao_expoe_o_token():
    chamadas = []
    falha = httpx.ConnectError(f"falhou em https://api.telegram.org/bot{TOKEN}/sendMessage")
    cliente, _ = cliente_com([falha], chamadas)

    with pytest.raises(ErroTelegram) as exc_info:
        cliente.enviar(987, "oi")
    assert TOKEN not in str(exc_info.value)
    assert exc_info.value.__cause__ is None


def test_token_vazio_falha_logo():
    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        ClienteTelegram("")


def test_formatar_vaga_completa():
    texto = formatar_vaga(VagaFake())

    assert texto == (
        "<b>Estágio em Dados</b>\n"
        "🏢 ACME\n"
        "📍 São Paulo - SP\n"
        '🔗 <a href="https://empresa.com/vagas/1">Ver vaga</a>'
    )


def test_formatar_vaga_remota_sem_cidade_e_sem_empresa():
    texto = formatar_vaga(VagaFake(empresa=None, cidade=None, remoto=True))

    assert "🏢" not in texto
    assert "📍 Remoto" in texto


def test_formatar_vaga_cidade_e_remoto():
    assert "📍 São Paulo - SP · Remoto" in formatar_vaga(VagaFake(remoto=True))


def test_formatar_vaga_sem_local():
    assert "📍 Local não informado" in formatar_vaga(VagaFake(cidade=None))


def test_formatar_vaga_escapa_html():
    vaga = VagaFake(titulo="Estágio <C++> & Dados", empresa="A&B", url='https://x.com/?a=1&b="2"')

    texto = formatar_vaga(vaga)

    assert "<b>Estágio &lt;C++&gt; &amp; Dados</b>" in texto
    assert "🏢 A&amp;B" in texto
    assert 'href="https://x.com/?a=1&amp;b=&quot;2&quot;"' in texto


def test_formatar_vaga_corta_titulo_gigante():
    texto = formatar_vaga(VagaFake(titulo="x" * 500))

    titulo = texto.splitlines()[0]
    assert titulo == "<b>" + "x" * 199 + "…</b>"


def test_cli_sem_token_avisa(monkeypatch, capsys):
    monkeypatch.setattr(telegram.settings, "telegram_bot_token", "")

    assert telegram.main(["--chat-id", "1"]) == 1
    assert "TELEGRAM_BOT_TOKEN" in capsys.readouterr().out


def test_cli_envia(monkeypatch, capsys):
    enviados = []
    monkeypatch.setattr(telegram.settings, "telegram_bot_token", TOKEN)
    monkeypatch.setattr(ClienteTelegram, "enviar", lambda self, c, t: enviados.append((c, t)))

    assert telegram.main(["--chat-id", "42", "olá"]) == 0
    assert enviados == [("42", "olá")]
    assert "enviada" in capsys.readouterr().out
