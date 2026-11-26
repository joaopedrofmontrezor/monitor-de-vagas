from pathlib import Path

import pytest
from checar_comentarios import achados_no_codigo, arquivos_python, main

ARQUIVO = Path("x.py")


def tipos_e_linhas(codigo: str) -> list[tuple[str, int]]:
    return [(a.tipo, a.linha) for a in achados_no_codigo(codigo, ARQUIVO)]


def test_codigo_limpo_nao_tem_achados():
    assert tipos_e_linhas("x = 1\n\ndef f():\n    return '# não é comentário'\n") == []


def test_acha_comentario_de_linha_e_no_fim_da_linha():
    assert tipos_e_linhas("# topo\nx = 1  # fim\n") == [("comentário", 1), ("comentário", 2)]


@pytest.mark.parametrize(
    "codigo",
    [
        '"""modulo"""\nx = 1\n',
        'def f():\n    """faz algo"""\n    return 1\n',
        'class A:\n    """classe"""\n',
        'async def g():\n    """assíncrona"""\n',
    ],
)
def test_acha_docstring_de_modulo_funcao_classe(codigo):
    assert [t for t, _ in tipos_e_linhas(codigo)] == ["docstring"]


def test_string_no_meio_da_funcao_nao_e_docstring():
    assert tipos_e_linhas("def f():\n    x = 1\n    'solta'\n    return x\n") == []


def test_ignora_pastas_de_ambiente(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "a.py").write_text("x = 1\n")
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "b.py").write_text("# de terceiros\n")

    assert arquivos_python([tmp_path]) == [tmp_path / "app" / "a.py"]


def test_main_retorna_1_e_lista_os_achados(tmp_path, capsys):
    (tmp_path / "ruim.py").write_text("x = 1  # oi\n")

    assert main([str(tmp_path)]) == 1
    assert "ruim.py:1: comentário" in capsys.readouterr().out


def test_main_retorna_0_sem_achados(tmp_path):
    (tmp_path / "bom.py").write_text("x = 1\n")

    assert main([str(tmp_path)]) == 0
