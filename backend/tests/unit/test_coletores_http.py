import httpx
import pytest

from app.coletores.http import USER_AGENT, ClienteHttp, ErroHttp


class RelogioFalso:
    def __init__(self) -> None:
        self.agora = 1000.0
        self.esperas: list[float] = []

    def __call__(self) -> float:
        return self.agora

    def dormir(self, segundos: float) -> None:
        self.esperas.append(segundos)
        self.agora += segundos


class Servidor:
    def __init__(self, *respostas: httpx.Response | Exception) -> None:
        self.respostas = list(respostas)
        self.recebidas: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.recebidas.append(request)
        resposta = self.respostas.pop(0) if len(self.respostas) > 1 else self.respostas[0]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def ok(json: object | None = None) -> httpx.Response:
    return httpx.Response(200, json=json if json is not None else {"ok": True})


@pytest.fixture
def relogio():
    return RelogioFalso()


@pytest.fixture
def criar_cliente(relogio):
    clientes: list[ClienteHttp] = []

    def _criar(servidor: Servidor, **kw) -> ClienteHttp:
        kw.setdefault("relogio", relogio)
        kw.setdefault("agora", relogio)
        kw.setdefault("dormir", relogio.dormir)
        cliente = ClienteHttp(transport=httpx.MockTransport(servidor), **kw)
        clientes.append(cliente)
        return cliente

    yield _criar
    for cliente in clientes:
        cliente.fechar()


def test_envia_user_agent_do_projeto(criar_cliente):
    servidor = Servidor(ok())

    criar_cliente(servidor).get("https://api.exemplo.com/vagas")

    assert servidor.recebidas[0].headers["User-Agent"] == USER_AGENT
    assert "github.com/joaopedrofmontrezor/monitor-de-vagas" in USER_AGENT


def test_get_json_devolve_o_corpo(criar_cliente):
    cliente = criar_cliente(Servidor(ok({"jobs": [1, 2]})))

    assert cliente.get_json("https://api.exemplo.com/vagas") == {"jobs": [1, 2]}


def test_get_json_com_corpo_invalido_vira_erro_http(criar_cliente):
    cliente = criar_cliente(Servidor(httpx.Response(200, text="<html>")))

    with pytest.raises(ErroHttp, match="JSON"):
        cliente.get_json("https://api.exemplo.com/vagas")


def test_rate_limit_espera_entre_requisicoes_do_mesmo_dominio(criar_cliente, relogio):
    cliente = criar_cliente(Servidor(ok()), intervalo_por_dominio=2.0)

    cliente.get("https://api.exemplo.com/a")
    relogio.agora += 0.5
    cliente.get("https://api.exemplo.com/b")

    assert relogio.esperas == [pytest.approx(1.5)]


def test_rate_limit_nao_espera_entre_dominios_diferentes(criar_cliente, relogio):
    cliente = criar_cliente(Servidor(ok()))

    cliente.get("https://a.exemplo.com/x")
    cliente.get("https://b.exemplo.com/x")

    assert relogio.esperas == []


def test_rate_limit_nao_espera_se_o_intervalo_ja_passou(criar_cliente, relogio):
    cliente = criar_cliente(Servidor(ok()), intervalo_por_dominio=2.0)

    cliente.get("https://api.exemplo.com/a")
    relogio.agora += 5
    cliente.get("https://api.exemplo.com/b")

    assert relogio.esperas == []


def test_retry_com_espera_exponencial_ate_dar_certo(criar_cliente, relogio):
    servidor = Servidor(httpx.Response(503), httpx.Response(502), ok())
    cliente = criar_cliente(servidor, intervalo_por_dominio=0, espera_base=1.0)

    resposta = cliente.get("https://api.exemplo.com/vagas")

    assert resposta.status_code == 200
    assert len(servidor.recebidas) == 3
    assert relogio.esperas == [1.0, 2.0]


def test_retry_tambem_vale_para_falha_de_rede(criar_cliente, relogio):
    servidor = Servidor(httpx.ConnectTimeout("lento"), ok())
    cliente = criar_cliente(servidor, intervalo_por_dominio=0)

    assert cliente.get("https://api.exemplo.com/vagas").status_code == 200
    assert relogio.esperas == [1.0]


def test_desiste_depois_do_maximo_de_tentativas(criar_cliente):
    servidor = Servidor(httpx.Response(500))
    cliente = criar_cliente(servidor, intervalo_por_dominio=0, max_tentativas=3)

    with pytest.raises(ErroHttp, match="status 500 após 3 tentativas") as erro:
        cliente.get("https://api.exemplo.com/vagas")
    assert erro.value.status == 500
    assert len(servidor.recebidas) == 3


def test_erro_4xx_nao_tenta_de_novo(criar_cliente):
    servidor = Servidor(httpx.Response(404))
    cliente = criar_cliente(servidor)

    with pytest.raises(ErroHttp, match="404") as erro:
        cliente.get("https://api.exemplo.com/nao-existe")
    assert erro.value.status == 404
    assert len(servidor.recebidas) == 1


def test_429_respeita_retry_after(criar_cliente, relogio):
    servidor = Servidor(httpx.Response(429, headers={"Retry-After": "7"}), ok())
    cliente = criar_cliente(servidor, intervalo_por_dominio=0)

    cliente.get("https://api.exemplo.com/vagas")

    assert relogio.esperas == [7.0]


def test_429_com_espera_longa_demais_desiste(criar_cliente):
    servidor = Servidor(httpx.Response(429, headers={"Retry-After": "3600"}), ok())
    cliente = criar_cliente(servidor, intervalo_por_dominio=0)

    with pytest.raises(ErroHttp, match="3600s"):
        cliente.get("https://api.exemplo.com/vagas")
    assert len(servidor.recebidas) == 1


def test_retry_tambem_respeita_o_rate_limit(criar_cliente, relogio):
    servidor = Servidor(httpx.Response(503), ok())
    cliente = criar_cliente(servidor, intervalo_por_dominio=2.0, espera_base=0.5)

    cliente.get("https://api.exemplo.com/vagas")

    assert relogio.esperas == [0.5, pytest.approx(1.5)]


def test_cache_evita_segunda_requisicao(criar_cliente, tmp_path):
    servidor = Servidor(ok({"n": 1}))
    cliente = criar_cliente(servidor, pasta_cache=tmp_path)

    primeira = cliente.get_json("https://api.exemplo.com/vagas", {"page": 1})
    segunda = cliente.get_json("https://api.exemplo.com/vagas", {"page": 1})

    assert primeira == segunda == {"n": 1}
    assert len(servidor.recebidas) == 1
    assert list((tmp_path / "api.exemplo.com").glob("*.json"))


def test_cache_separa_parametros_diferentes(criar_cliente, tmp_path):
    servidor = Servidor(ok())
    cliente = criar_cliente(servidor, pasta_cache=tmp_path)

    cliente.get("https://api.exemplo.com/vagas", {"page": 1})
    cliente.get("https://api.exemplo.com/vagas", {"page": 2})

    assert len(servidor.recebidas) == 2


def test_cache_vencido_busca_de_novo(criar_cliente, relogio, tmp_path):
    servidor = Servidor(ok({"versao": 1}), ok({"versao": 2}))
    cliente = criar_cliente(servidor, pasta_cache=tmp_path, validade_cache=60)

    cliente.get("https://api.exemplo.com/vagas")
    relogio.agora += 61

    assert cliente.get_json("https://api.exemplo.com/vagas") == {"versao": 2}
    assert len(servidor.recebidas) == 2


def test_cache_corrompido_e_ignorado(criar_cliente, tmp_path):
    servidor = Servidor(ok({"n": 1}))
    cliente = criar_cliente(servidor, pasta_cache=tmp_path)
    cliente.get("https://api.exemplo.com/vagas")
    for arquivo in tmp_path.rglob("*.json"):
        arquivo.write_text("{quebrado", encoding="utf-8")

    assert cliente.get_json("https://api.exemplo.com/vagas") == {"n": 1}
    assert len(servidor.recebidas) == 2


def test_resposta_de_erro_nao_vai_para_o_cache(criar_cliente, tmp_path):
    servidor = Servidor(httpx.Response(404))
    cliente = criar_cliente(servidor, pasta_cache=tmp_path)

    with pytest.raises(ErroHttp):
        cliente.get("https://api.exemplo.com/vagas")
    assert not list(tmp_path.rglob("*.json"))


def test_sem_pasta_de_cache_nao_grava_nada(criar_cliente, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    servidor = Servidor(ok())
    cliente = criar_cliente(servidor)

    cliente.get("https://api.exemplo.com/vagas")
    cliente.get("https://api.exemplo.com/vagas")

    assert len(servidor.recebidas) == 2
    assert not list(tmp_path.iterdir())


def test_usa_como_gerenciador_de_contexto():
    with ClienteHttp(transport=httpx.MockTransport(Servidor(ok())), dormir=lambda _: None) as c:
        assert c.get("https://api.exemplo.com/x").status_code == 200
