from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.coletores.base import ColetaParcial, VagaColetada
from app.coletores.registry import RegistroColetores
from app.models import ExecucaoColeta, Vaga
from app.services.pipeline import executar_coletor, executar_todos, ultima_execucao
from app.worker import coletar

pytestmark = pytest.mark.integracao


def vaga(n: int, **campos) -> VagaColetada:
    padrao = {
        "fonte": "falso",
        "url": f"https://exemplo.com/vagas/{n}",
        "titulo": f"Estágio {n}",
        "empresa": "Acme",
        "cidade": "São Paulo, SP",
    }
    return VagaColetada(**(padrao | campos))


class ColetorFalso:
    intervalo_horas = 6

    def __init__(self, nome: str = "falso", vagas=(), erro: Exception | None = None) -> None:
        self.nome = nome
        self.vagas = list(vagas)
        self.erro = erro

    def coletar(self) -> list[VagaColetada]:
        if self.erro is not None:
            raise self.erro
        return self.vagas


class Relogio:
    def __init__(self) -> None:
        self.atual = datetime(2026, 12, 1, 9, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        self.atual += timedelta(seconds=5)
        return self.atual


def execucoes(sessao, coletor: str = "falso") -> list[ExecucaoColeta]:
    consulta = select(ExecucaoColeta).where(ExecucaoColeta.coletor == coletor)
    return list(sessao.scalars(consulta.order_by(ExecucaoColeta.id)))


def test_coleta_grava_as_vagas_e_registra_a_execucao(sessao):
    relogio = Relogio()
    coletor = ColetorFalso(vagas=[vaga(1), vaga(2), vaga(3)])

    resultado = executar_coletor(coletor, sessao, agora=relogio)

    assert (resultado.total_coletadas, resultado.novas, resultado.duplicadas) == (3, 3, 0)
    assert resultado.erro is None
    assert len(resultado.ids_novos) == 3
    titulos = sessao.scalars(select(Vaga.titulo).where(Vaga.fonte == "falso").order_by(Vaga.id))
    assert list(titulos) == ["Estágio 1", "Estágio 2", "Estágio 3"]
    (execucao,) = execucoes(sessao)
    assert execucao.inicio < execucao.fim
    assert (execucao.total_coletadas, execucao.novas, execucao.duplicadas) == (3, 3, 0)
    assert execucao.erro is None


def test_vagas_ja_vistas_contam_como_duplicadas(sessao):
    executar_coletor(ColetorFalso(vagas=[vaga(1), vaga(2)]), sessao)

    resultado = executar_coletor(
        ColetorFalso(vagas=[vaga(1), vaga(2, url="https://exemplo.com/outra"), vaga(3)]), sessao
    )

    assert (resultado.novas, resultado.duplicadas) == (1, 2)
    assert [e.novas for e in execucoes(sessao)] == [2, 1]


def test_duplicada_dentro_da_mesma_coleta_entra_uma_vez(sessao):
    resultado = executar_coletor(
        ColetorFalso(vagas=[vaga(1), vaga(1, titulo="[Novo] Estágio 1")]), sessao
    )

    assert (resultado.novas, resultado.duplicadas) == (1, 1)


def test_coletor_que_levanta_excecao_fica_registrado_com_erro(sessao):
    coletor = ColetorFalso(erro=RuntimeError("fonte mudou o formato"))

    resultado = executar_coletor(coletor, sessao)

    assert resultado.erro == "RuntimeError: fonte mudou o formato"
    assert (resultado.total_coletadas, resultado.novas) == (0, 0)
    (execucao,) = execucoes(sessao)
    assert execucao.erro == "RuntimeError: fonte mudou o formato"
    assert execucao.fim is not None


def test_coleta_parcial_grava_o_que_veio_e_registra_os_erros(sessao):
    parcial = ColetaParcial([vaga(1), vaga(2)], ["empresa_x: 404", "empresa_y: timeout"])

    resultado = executar_coletor(ColetorFalso(erro=parcial), sessao)

    assert (resultado.total_coletadas, resultado.novas) == (2, 2)
    (execucao,) = execucoes(sessao)
    assert execucao.erro == "empresa_x: 404; empresa_y: timeout"
    assert execucao.novas == 2


def test_falha_de_um_coletor_nao_derruba_os_outros(sessao):
    coletores = [
        ColetorFalso("quebrado", erro=ValueError("json inválido")),
        ColetorFalso("bom", vagas=[vaga(1, fonte="bom")]),
    ]

    resultados = executar_todos(coletores, lambda: sessao)

    assert [r.coletor for r in resultados] == ["quebrado", "bom"]
    assert resultados[0].erro == "ValueError: json inválido"
    assert resultados[1].novas == 1
    assert execucoes(sessao, "quebrado")[0].erro is not None
    assert execucoes(sessao, "bom")[0].erro is None


def test_erro_do_banco_desfaz_o_lote_e_fica_registrado(sessao):
    coletor = ColetorFalso("fonte_longa", vagas=[vaga(1), vaga(2, fonte="f" * 60)])

    resultado = executar_coletor(coletor, sessao)

    assert resultado.novas == 0
    assert resultado.erro.startswith("DataError")
    assert sessao.scalar(select(Vaga.id).where(Vaga.url == "https://exemplo.com/vagas/1")) is None
    (execucao,) = execucoes(sessao, "fonte_longa")
    assert execucao.total_coletadas == 2
    assert execucao.erro.startswith("DataError")


def test_ultima_execucao_devolve_o_inicio_mais_recente(sessao):
    relogio = Relogio()
    assert ultima_execucao(sessao, "falso") is None

    executar_coletor(ColetorFalso(), sessao, agora=relogio)
    executar_coletor(ColetorFalso(), sessao, agora=relogio)

    assert ultima_execucao(sessao, "falso") == execucoes(sessao)[-1].inicio
    assert ultima_execucao(sessao, "outro") is None


def test_make_coletar_grava_no_banco(sessao, capsys):
    registro = RegistroColetores()
    registro.registrar(ColetorFalso(vagas=[vaga(1), vaga(2)]))

    codigo = coletar.main([], registro=registro, fabrica_sessao=lambda: sessao)

    assert codigo == 0
    assert "falso: 2 coletadas, 2 novas, 0 duplicadas" in capsys.readouterr().out
    assert execucoes(sessao)[0].novas == 2
