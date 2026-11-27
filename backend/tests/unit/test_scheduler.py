from datetime import UTC, datetime, timedelta

import pytest
from apscheduler.schedulers.blocking import BlockingScheduler

from app.coletores.base import VagaColetada
from app.coletores.registry import RegistroColetores
from app.worker.scheduler import (
    TOLERANCIA_ATRASO_S,
    agendar,
    intervalo_efetivo,
    proxima_execucao,
)

AGORA = datetime(2026, 12, 1, 12, 0, tzinfo=UTC)


class ColetorFalso:
    def __init__(self, nome: str, intervalo_horas: int = 6) -> None:
        self.nome = nome
        self.intervalo_horas = intervalo_horas

    def coletar(self) -> list[VagaColetada]:
        return []


def test_intervalo_usa_o_do_coletor_quando_nao_ha_variavel():
    assert intervalo_efetivo(ColetorFalso("a", 8), None) == 8


def test_intervalo_da_variavel_vale_para_todos():
    assert intervalo_efetivo(ColetorFalso("a", 8), 12) == 12


def test_intervalo_da_variavel_abaixo_do_minimo_e_recusado():
    with pytest.raises(ValueError, match="mínimo é 6h"):
        intervalo_efetivo(ColetorFalso("a"), 2)


def test_sem_coleta_anterior_roda_na_hora():
    assert proxima_execucao(None, 6, AGORA) == AGORA


def test_coleta_recente_espera_completar_o_intervalo():
    ultima = AGORA - timedelta(hours=2)

    assert proxima_execucao(ultima, 6, AGORA) == AGORA + timedelta(hours=4)


def test_coleta_antiga_roda_na_hora():
    assert proxima_execucao(AGORA - timedelta(days=1), 6, AGORA) == AGORA


def registro_com(*coletores: ColetorFalso) -> RegistroColetores:
    registro = RegistroColetores()
    for coletor in coletores:
        registro.registrar(coletor)
    return registro


def test_agendar_cria_um_job_por_coletor():
    scheduler = BlockingScheduler(timezone=UTC)
    executados: list[str] = []
    ultimas = {"github": AGORA - timedelta(hours=1)}
    registro = registro_com(ColetorFalso("greenhouse"), ColetorFalso("github", 12))

    agendar(
        scheduler,
        registro,
        executar=lambda c: executados.append(c.nome),
        ultima=ultimas.get,
        agora=lambda: AGORA,
    )

    jobs = {job.id: job for job in scheduler.get_jobs()}
    assert sorted(jobs) == ["github", "greenhouse"]
    assert jobs["greenhouse"].next_run_time == AGORA
    assert jobs["github"].next_run_time == AGORA + timedelta(hours=11)
    assert jobs["greenhouse"].trigger.interval == timedelta(hours=6)
    assert jobs["github"].trigger.interval == timedelta(hours=12)
    assert jobs["greenhouse"].max_instances == 1
    assert jobs["greenhouse"].coalesce is True
    assert jobs["greenhouse"].misfire_grace_time == TOLERANCIA_ATRASO_S

    jobs["github"].func(*jobs["github"].args)
    assert executados == ["github"]


def test_agendar_com_intervalo_sobrescrito():
    scheduler = BlockingScheduler(timezone=UTC)

    agendar(
        scheduler,
        registro_com(ColetorFalso("greenhouse")),
        executar=lambda c: None,
        ultima=lambda nome: None,
        intervalo_sobrescrito=24,
        agora=lambda: AGORA,
    )

    (job,) = scheduler.get_jobs()
    assert job.trigger.interval == timedelta(hours=24)


def test_agendar_sem_coletores_nao_cria_jobs():
    scheduler = BlockingScheduler(timezone=UTC)

    agendar(scheduler, RegistroColetores(), executar=print, ultima=lambda nome: None)

    assert scheduler.get_jobs() == []
