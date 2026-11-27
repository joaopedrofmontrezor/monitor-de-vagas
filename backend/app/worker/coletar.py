import argparse
import logging
import sys
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.coletores.registry import RegistroColetores, registro_padrao
from app.config import settings
from app.db import SessionLocal
from app.services.pipeline import ResultadoColeta, executar_todos


def formatar(resultado: ResultadoColeta) -> str:
    linha = (
        f"{resultado.coletor}: {resultado.total_coletadas} coletadas, "
        f"{resultado.novas} novas, {resultado.duplicadas} duplicadas"
    )
    return f"{linha} | ERRO: {resultado.erro}" if resultado.erro else linha


def main(
    argv: list[str] | None = None,
    registro: RegistroColetores | None = None,
    fabrica_sessao: Callable[[], Session] = SessionLocal,
) -> int:
    parser = argparse.ArgumentParser(
        prog="make coletar", description="Roda o pipeline de coleta uma vez, na hora."
    )
    parser.add_argument("coletores", nargs="*", help="nomes dos coletores (vazio = todos)")
    args = parser.parse_args(argv)

    if registro is None:
        registro = registro_padrao()
    try:
        coletores = [registro.obter(nome) for nome in args.coletores] or registro.todos()
    except KeyError as exc:
        print(exc.args[0], file=sys.stderr)
        return 2
    if not coletores:
        print("Nenhum coletor registrado em registro_padrao().")
        return 0

    resultados = executar_todos(coletores, fabrica_sessao)
    for resultado in resultados:
        print(formatar(resultado))
    return 1 if any(r.erro for r in resultados) else 0


if __name__ == "__main__":
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(name)s %(message)s")
    sys.exit(main())
