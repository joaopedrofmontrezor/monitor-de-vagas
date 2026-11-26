import argparse
import ast
import io
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

PASTAS_IGNORADAS = {".venv", "venv", "__pycache__", "node_modules", ".git", "build", "dist"}


@dataclass(frozen=True)
class Achado:
    arquivo: Path
    linha: int
    tipo: str

    def __str__(self) -> str:
        return f"{self.arquivo}:{self.linha}: {self.tipo}"


def achados_no_codigo(codigo: str, arquivo: Path) -> list[Achado]:
    achados = [
        Achado(arquivo, tok.start[0], "comentário")
        for tok in tokenize.generate_tokens(io.StringIO(codigo).readline)
        if tok.type == tokenize.COMMENT
    ]
    nos = [ast.parse(codigo)]
    nos += [
        n
        for n in ast.walk(nos[0])
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
    ]
    for no in nos:
        primeiro = no.body[0] if no.body else None
        if (
            isinstance(primeiro, ast.Expr)
            and isinstance(primeiro.value, ast.Constant)
            and isinstance(primeiro.value.value, str)
        ):
            achados.append(Achado(arquivo, primeiro.lineno, "docstring"))
    return sorted(achados, key=lambda a: a.linha)


def arquivos_python(caminhos: list[Path]) -> list[Path]:
    encontrados: list[Path] = []
    for caminho in caminhos:
        if caminho.is_file():
            encontrados.append(caminho)
            continue
        encontrados += [
            p for p in caminho.rglob("*.py") if not PASTAS_IGNORADAS.intersection(p.parts)
        ]
    return sorted(encontrados)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Falha se algum .py tiver comentário ou docstring")
    parser.add_argument("caminhos", nargs="+", type=Path)
    args = parser.parse_args(argv)

    achados = [
        achado
        for arquivo in arquivos_python(args.caminhos)
        for achado in achados_no_codigo(arquivo.read_text(encoding="utf-8"), arquivo)
    ]
    for achado in achados:
        print(achado)
    if achados:
        print(f"\n{len(achados)} comentário(s)/docstring(s). Regra do time: CONTRIBUTING.md")
        return 1
    print("Nenhum comentário nem docstring nos .py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
