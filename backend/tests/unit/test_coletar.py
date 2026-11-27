import pytest

from app.coletores.base import VagaColetada
from app.coletores.registry import RegistroColetores
from app.services.pipeline import ResultadoColeta
from app.worker import coletar


class ColetorFalso:
    intervalo_horas = 6

    def __init__(self, nome: str) -> None:
        self.nome = nome

    def coletar(self) -> list[VagaColetada]:
        return []


@pytest.fixture
def registro():
    registro = RegistroColetores()
    registro.registrar(ColetorFalso("github"))
    registro.registrar(ColetorFalso("greenhouse"))
    return registro


@pytest.fixture
def executados(monkeypatch):
    chamados: list[list[str]] = []
    respostas: dict[str, ResultadoColeta] = {}

    def executar_todos(coletores, fabrica_sessao):
        nomes = [c.nome for c in coletores]
        chamados.append(nomes)
        return [respostas.get(n, ResultadoColeta(coletor=n, total_coletadas=3)) for n in nomes]

    monkeypatch.setattr(coletar, "executar_todos", executar_todos)
    return chamados, respostas


def test_sem_argumentos_roda_todos_os_coletores(registro, executados, capsys):
    chamados, _ = executados

    codigo = coletar.main([], registro=registro)

    assert codigo == 0
    assert chamados == [["github", "greenhouse"]]
    saida = capsys.readouterr().out
    assert "greenhouse: 3 coletadas, 0 novas, 0 duplicadas" in saida


def test_com_nome_roda_so_aquele_coletor(registro, executados):
    chamados, _ = executados

    assert coletar.main(["greenhouse"], registro=registro) == 0
    assert chamados == [["greenhouse"]]


def test_nome_desconhecido_sai_com_codigo_2(registro, executados, capsys):
    chamados, _ = executados

    assert coletar.main(["lever"], registro=registro) == 2
    assert chamados == []
    assert "não registrado" in capsys.readouterr().err


def test_erro_em_algum_coletor_sai_com_codigo_1(registro, executados, capsys):
    _, respostas = executados
    respostas["github"] = ResultadoColeta(coletor="github", erro="ErroHttp: 503")

    assert coletar.main([], registro=registro) == 1
    assert "github: 0 coletadas, 0 novas, 0 duplicadas | ERRO: ErroHttp: 503" in (
        capsys.readouterr().out
    )


def test_registro_vazio_avisa_e_sai_com_zero(executados, capsys):
    chamados, _ = executados

    assert coletar.main([], registro=RegistroColetores()) == 0
    assert chamados == []
    assert "Nenhum coletor registrado" in capsys.readouterr().out
