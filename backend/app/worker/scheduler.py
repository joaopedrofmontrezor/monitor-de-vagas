import logging
import signal
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.base import BaseScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.coletores.base import Coletor
from app.coletores.registry import INTERVALO_MINIMO_HORAS, RegistroColetores, registro_padrao
from app.config import settings
from app.db import SessionLocal
from app.services.pipeline import agora_utc, executar_todos, ultima_execucao

log = logging.getLogger("worker")

TOLERANCIA_ATRASO_S = 3600


def intervalo_efetivo(coletor: Coletor, sobrescrito: int | None) -> int:
    if sobrescrito is None:
        return coletor.intervalo_horas
    if sobrescrito < INTERVALO_MINIMO_HORAS:
        raise ValueError(
            f"COLETA_INTERVALO_HORAS={sobrescrito}; o mínimo é {INTERVALO_MINIMO_HORAS}h (ADR-0003)"
        )
    return sobrescrito


def proxima_execucao(ultima: datetime | None, intervalo_horas: int, agora: datetime) -> datetime:
    if ultima is None:
        return agora
    return max(agora, ultima + timedelta(hours=intervalo_horas))


def agendar(
    scheduler: BaseScheduler,
    registro: RegistroColetores,
    *,
    executar: Callable[[Coletor], object],
    ultima: Callable[[str], datetime | None],
    intervalo_sobrescrito: int | None = None,
    agora: Callable[[], datetime] = agora_utc,
) -> None:
    for coletor in registro.todos():
        horas = intervalo_efetivo(coletor, intervalo_sobrescrito)
        quando = proxima_execucao(ultima(coletor.nome), horas, agora())
        scheduler.add_job(
            executar,
            IntervalTrigger(hours=horas, timezone=UTC),
            args=[coletor],
            id=coletor.nome,
            name=f"coleta {coletor.nome}",
            next_run_time=quando,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=TOLERANCIA_ATRASO_S,
        )
        log.info("%s: a cada %dh, próxima em %s", coletor.nome, horas, quando.isoformat())


def _executar(coletor: Coletor) -> None:
    executar_todos([coletor], SessionLocal)


def _ultima(nome: str) -> datetime | None:
    try:
        with SessionLocal() as sessao:
            return ultima_execucao(sessao, nome)
    except Exception:
        log.warning("não deu para ler a última coleta de %s; rodou o make migrate?", nome)
        return None


def main() -> None:
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(name)s %(message)s")
    registro = registro_padrao()
    scheduler = BlockingScheduler(timezone=UTC)
    agendar(
        scheduler,
        registro,
        executar=_executar,
        ultima=_ultima,
        intervalo_sobrescrito=settings.coleta_intervalo_horas,
    )
    if not len(registro):
        log.warning("nenhum coletor registrado; o worker fica no ar sem jobs")

    def parar(*_: object) -> None:
        log.info("parando o worker")
        scheduler.shutdown(wait=False)

    signal.signal(signal.SIGTERM, parar)
    signal.signal(signal.SIGINT, parar)

    log.info("worker no ar (ambiente=%s, %d coletores)", settings.ambiente, len(registro))
    scheduler.start()
    log.info("worker encerrado")


if __name__ == "__main__":
    main()
