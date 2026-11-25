"""Processo `worker`: por enquanto só mantém o container vivo.

Na issue #4 este arquivo passa a usar o APScheduler para disparar um job por
coletor. Já existe agora para o `docker compose up` subir o serviço `worker` e o
time ver, desde o primeiro dia, que API e worker são processos separados (ADR-0004).
"""

import logging
import signal
import threading

from app.config import settings

log = logging.getLogger("worker")


def main() -> None:
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(name)s %(message)s")
    parar = threading.Event()

    
    signal.signal(signal.SIGTERM, lambda *_: parar.set())
    signal.signal(signal.SIGINT, lambda *_: parar.set())

    log.info("worker no ar (ambiente=%s); agendamento chega na issue #4", settings.ambiente)
    while not parar.wait(timeout=60):
        log.debug("worker ativo")
    log.info("worker encerrado")


if __name__ == "__main__":
    main()
