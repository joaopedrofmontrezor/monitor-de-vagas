import pytest
from importar_backlog import (
    ErroBacklog,
    Issue,
    carregar_backlog,
    montar_payload_issue,
    numero_da_url,
    parse_issue,
    parse_responsaveis,
    pontos_por_pessoa,
    validar,
)

EXEMPLO = """---
numero: 3
titulo: "feat(db): modelos iniciais"
responsavel: Vinicius
labels: feat, backend, infra
pontos: 2
sprint: Sprint 1
---
## O que fazer
Criar os modelos.

---
Separador no corpo não pode quebrar o parser.
"""


def _issue(numero=1, **kw):
    base = {
        "numero": numero, "titulo": f"feat: issue {numero}", "responsavel": "lucas",
        "labels": ["feat"], "pontos": 2, "sprint": "Sprint 1", "corpo": "corpo", "arquivo": f"{numero}.md",
    }
    base.update(kw)
    return Issue(**base)


def test_parse_issue_le_front_matter_e_corpo():
    issue = parse_issue(EXEMPLO, "03.md")
    assert issue.numero == 3
    assert issue.titulo == "feat(db): modelos iniciais"
    assert issue.responsavel == "vinicius"
    assert issue.labels == ["feat", "backend", "infra"]
    assert issue.pontos == 2
    assert issue.sprint == "Sprint 1"
    assert issue.corpo.startswith("## O que fazer")
    assert "Separador no corpo" in issue.corpo


def test_corpo_completo_inclui_estimativa():
    assert parse_issue(EXEMPLO).corpo_completo().endswith("**Estimativa:** 2 pts")


@pytest.mark.parametrize(
    "texto",
    [
        "sem front matter",
        "---\nnumero: 1\n---\ncorpo",
        "---\nnumero: um\ntitulo: x\nresponsavel: lucas\nlabels: feat\npontos: 1\nsprint: Sprint 1\n---\n",
        "---\nlinha sem dois pontos\n---\n",
    ],
)
def test_parse_issue_rejeita_arquivo_invalido(texto):
    with pytest.raises(ErroBacklog):
        parse_issue(texto, "ruim.md")


def test_validar_detecta_buraco_na_numeracao():
    with pytest.raises(ErroBacklog, match="numeração"):
        validar([_issue(1), _issue(3)])


@pytest.mark.parametrize(
    ("campo", "valor", "mensagem"),
    [
        ("labels", ["feat", "inexistente"], "labels desconhecidas"),
        ("sprint", "Sprint 9", "sprint desconhecida"),
        ("responsavel", "maria", "responsável desconhecido"),
        ("pontos", 5, "pontos devem ser"),
    ],
)
def test_validar_detecta_campos_invalidos(campo, valor, mensagem):
    with pytest.raises(ErroBacklog, match=mensagem):
        validar([_issue(1, **{campo: valor})])


def test_parse_responsaveis():
    assert parse_responsaveis(["joao=jp-dev", "Lucas=@lucas"]) == {"joao": "jp-dev", "lucas": "lucas"}


@pytest.mark.parametrize("par", ["joao", "joao=", "maria=x"])
def test_parse_responsaveis_rejeita_invalidos(par):
    with pytest.raises(ErroBacklog):
        parse_responsaveis([par])


def test_montar_payload_com_e_sem_assignee():
    issue = _issue(7, labels=["feat", "coleta"], responsavel="joao")

    sem = montar_payload_issue(issue, {"Sprint 1": 4}, {})
    assert sem["title"] == issue.titulo
    assert sem["labels"] == ["feat", "coleta"]
    assert sem["milestone"] == 4
    assert "assignees" not in sem
    assert sem["body"].endswith("**Estimativa:** 2 pts")

    com = montar_payload_issue(issue, {}, {"joao": "jp-dev"})
    assert com["assignees"] == ["jp-dev"]
    assert "milestone" not in com


@pytest.mark.parametrize(
    ("url", "esperado"),
    [
        ("https://github.com/org/repo/issues/12\n", 12),
        ("https://github.com/org/repo/pull/12", None),
        ("", None),
    ],
)
def test_numero_da_url(url, esperado):
    assert numero_da_url(url) == esperado


def test_backlog_real_e_valido_e_equilibrado():
    issues = carregar_backlog()
    assert [i.numero for i in issues] == list(range(1, 26))

    resumo = pontos_por_pessoa(issues)
    for sprint, pessoas in resumo.items():
        assert set(pessoas) == {"joao", "vinicius", "lucas"}, sprint
        assert max(pessoas.values()) - min(pessoas.values()) <= 1, (sprint, pessoas)
