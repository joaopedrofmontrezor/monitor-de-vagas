"""Importa o backlog do MVP para o GitHub: labels, milestones e issues.

Uso (rode da raiz do repositório):

    # 1) veja o que seria feito, sem tocar no GitHub
    python scripts/github/importar_backlog.py --repo ORG/monitor-de-vagas --dry-run

    # 2) importe de verdade, já atribuindo os responsáveis
    python scripts/github/importar_backlog.py --repo ORG/monitor-de-vagas \
        --responsavel joao=usuario-do-joao \
        --responsavel vinicius=usuario-do-vinicius \
        --responsavel lucas=usuario-do-lucas \
        --projeto ORG/1

Requisitos: GitHub CLI (`gh`) autenticado (`gh auth login`). Para usar
--projeto, o token precisa do escopo `project` (`gh auth refresh -s project`).

O script é idempotente: labels são atualizadas, milestones e issues que já
existem (mesmo título) são puladas. Pode rodar de novo sem duplicar nada.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

PASTA_BACKLOG = Path(__file__).parent / "backlog"

# nome -> (cor sem #, descrição)
LABELS: dict[str, tuple[str, str]] = {
    # tipo (bate com o Conventional Commit)
    "feat": ("1d76db", "Nova funcionalidade"),
    "fix": ("d73a4a", "Correção de bug"),
    "chore": ("cfd3d7", "Manutenção, configuração, estrutura"),
    "docs": ("0075ca", "Documentação"),
    "test": ("bfd4f2", "Testes"),
    "ci": ("5319e7", "Integração contínua"),
    "spike": ("fbca04", "Pesquisa com prazo curto antes de implementar"),
    # área
    "backend": ("0e8a16", "API e regras de negócio (FastAPI)"),
    "frontend": ("c2e0c6", "Next.js"),
    "coleta": ("006b75", "Coletores e scraping"),
    "dados": ("7057ff", "Estatísticas e painel"),
    "notificacoes": ("e99695", "Telegram e e-mail"),
    "infra": ("5a5a5a", "Docker, banco, CI, deploy"),
    # prioridade
    "p0": ("b60205", "Sem isso a demo da sprint não acontece"),
    "p1": ("f9d0c4", "Importante, mas não bloqueia a demo"),
}

# título -> data de entrega (sexta-feira da sprint)
MILESTONES: dict[str, str] = {
    "Sprint 1": "2026-12-04",
    "Sprint 2": "2026-12-11",
}

RESPONSAVEIS_VALIDOS = {"joao", "vinicius", "lucas"}


@dataclass
class Issue:
    numero: int
    titulo: str
    responsavel: str
    labels: list[str]
    pontos: int
    sprint: str
    corpo: str
    arquivo: str = ""
    extras: dict[str, str] = field(default_factory=dict)

    def corpo_completo(self) -> str:
        return f"{self.corpo.rstrip()}\n\n---\n**Estimativa:** {self.pontos} pts"


class ErroBacklog(ValueError):
    """Arquivo de backlog inválido."""


def parse_issue(texto: str, arquivo: str = "") -> Issue:
    """Lê um arquivo de issue: front matter simples (chave: valor) + corpo markdown."""
    partes = texto.split("---", 2)
    if len(partes) < 3 or partes[0].strip():
        raise ErroBacklog(f"{arquivo}: front matter ausente (precisa começar com ---)")

    meta: dict[str, str] = {}
    for linha in partes[1].strip().splitlines():
        if not linha.strip():
            continue
        if ":" not in linha:
            raise ErroBacklog(f"{arquivo}: linha inválida no front matter: {linha!r}")
        chave, valor = linha.split(":", 1)
        meta[chave.strip()] = valor.strip().strip('"')

    obrigatorios = ("numero", "titulo", "responsavel", "labels", "pontos", "sprint")
    faltando = [c for c in obrigatorios if not meta.get(c)]
    if faltando:
        raise ErroBacklog(f"{arquivo}: campos obrigatórios ausentes: {', '.join(faltando)}")

    try:
        numero = int(meta.pop("numero"))
        pontos = int(meta.pop("pontos"))
    except ValueError as exc:
        raise ErroBacklog(f"{arquivo}: numero e pontos precisam ser inteiros") from exc

    return Issue(
        numero=numero,
        titulo=meta.pop("titulo"),
        responsavel=meta.pop("responsavel").lower(),
        labels=[l.strip() for l in meta.pop("labels").split(",") if l.strip()],
        pontos=pontos,
        sprint=meta.pop("sprint"),
        corpo=partes[2].strip(),
        arquivo=arquivo,
        extras=meta,
    )


def validar(issues: list[Issue]) -> None:
    """Garante numeração 1..N sem buracos e labels/sprints/responsáveis conhecidos."""
    erros: list[str] = []
    numeros = [i.numero for i in issues]
    if sorted(numeros) != list(range(1, len(issues) + 1)):
        erros.append(f"numeração precisa ser 1..{len(issues)} sem repetir: {sorted(numeros)}")

    for i in issues:
        desconhecidas = set(i.labels) - LABELS.keys()
        if desconhecidas:
            erros.append(f"{i.arquivo}: labels desconhecidas {sorted(desconhecidas)}")
        if i.sprint not in MILESTONES:
            erros.append(f"{i.arquivo}: sprint desconhecida {i.sprint!r}")
        if i.responsavel not in RESPONSAVEIS_VALIDOS:
            erros.append(f"{i.arquivo}: responsável desconhecido {i.responsavel!r}")
        if not 1 <= i.pontos <= 3:
            erros.append(f"{i.arquivo}: pontos devem ser 1, 2 ou 3 (maior que isso, quebre a issue)")

    if erros:
        raise ErroBacklog("\n".join(erros))


def carregar_backlog(pasta: Path = PASTA_BACKLOG) -> list[Issue]:
    issues = [parse_issue(p.read_text(encoding="utf-8"), p.name) for p in sorted(pasta.glob("*.md"))]
    validar(issues)
    return sorted(issues, key=lambda i: i.numero)


def pontos_por_pessoa(issues: list[Issue]) -> dict[str, dict[str, int]]:
    """{sprint: {responsavel: pontos}} para conferir o equilíbrio."""
    resumo: dict[str, dict[str, int]] = {}
    for i in issues:
        sprint = resumo.setdefault(i.sprint, {})
        sprint[i.responsavel] = sprint.get(i.responsavel, 0) + i.pontos
    return resumo


def parse_responsaveis(pares: list[str]) -> dict[str, str]:
    """['joao=jp-dev'] -> {'joao': 'jp-dev'}"""
    resultado: dict[str, str] = {}
    for par in pares:
        apelido, sep, usuario = par.partition("=")
        apelido = apelido.strip().lower()
        if not sep or not usuario.strip() or apelido not in RESPONSAVEIS_VALIDOS:
            raise ErroBacklog(
                f"--responsavel inválido: {par!r} (use joao=usuario, vinicius=usuario ou lucas=usuario)"
            )
        resultado[apelido] = usuario.strip().lstrip("@")
    return resultado


def montar_comando_issue(issue: Issue, repo: str, responsaveis: dict[str, str]) -> list[str]:
    cmd = [
        "gh", "issue", "create",
        "--repo", repo,
        "--title", issue.titulo,
        "--body", issue.corpo_completo(),
        "--milestone", issue.sprint,
    ]
    for label in issue.labels:
        cmd += ["--label", label]
    if issue.responsavel in responsaveis:
        cmd += ["--assignee", responsaveis[issue.responsavel]]
    return cmd


def numero_da_url(url: str) -> int | None:
    """https://github.com/org/repo/issues/12 -> 12"""
    m = re.search(r"/issues/(\d+)\s*$", url.strip())
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------- execução


def _gh(args: list[str], dry_run: bool, capturar: bool = False) -> str:
    if dry_run:
        exibicao = [a if len(a) < 80 else a[:77] + "..." for a in args]
        print("  [dry-run]", " ".join(exibicao).replace("\n", " "))
        return ""
    res = subprocess.run(args, check=True, text=True, capture_output=True)
    return res.stdout if capturar else res.stdout.strip()


def _titulos_existentes(repo: str) -> set[str]:
    saida = subprocess.run(
        ["gh", "issue", "list", "--repo", repo, "--state", "all", "--limit", "500", "--json", "title"],
        check=True, text=True, capture_output=True,
    ).stdout
    return {i["title"] for i in json.loads(saida or "[]")}


def _milestones_existentes(repo: str) -> set[str]:
    saida = subprocess.run(
        ["gh", "api", f"repos/{repo}/milestones?state=all&per_page=100", "--jq", ".[].title"],
        check=True, text=True, capture_output=True,
    ).stdout
    return {l for l in saida.splitlines() if l}


def importar(repo: str, responsaveis: dict[str, str], projeto: str | None, dry_run: bool) -> None:
    issues = carregar_backlog()
    print(f"Backlog válido: {len(issues)} issues.")
    for sprint, pessoas in pontos_por_pessoa(issues).items():
        print(f"  {sprint}: " + ", ".join(f"{p} {pts} pts" for p, pts in sorted(pessoas.items())))
    sem_dono = RESPONSAVEIS_VALIDOS - responsaveis.keys()
    if sem_dono:
        print(f"Aviso: sem usuário do GitHub para {sorted(sem_dono)}; essas issues ficam sem assignee.")

    print("\nLabels")
    for nome, (cor, descricao) in LABELS.items():
        _gh(["gh", "label", "create", nome, "--repo", repo, "--color", cor,
             "--description", descricao, "--force"], dry_run)

    print("\nMilestones")
    existentes = set() if dry_run else _milestones_existentes(repo)
    for titulo, data in MILESTONES.items():
        if titulo in existentes:
            print(f"  já existe: {titulo}")
            continue
        _gh(["gh", "api", f"repos/{repo}/milestones", "-f", f"title={titulo}",
             "-f", f"due_on={data}T23:59:59Z"], dry_run)

    print("\nIssues")
    ja_criadas = set() if dry_run else _titulos_existentes(repo)
    for issue in issues:
        if issue.titulo in ja_criadas:
            print(f"  já existe: #{issue.numero} {issue.titulo}")
            continue
        url = _gh(montar_comando_issue(issue, repo, responsaveis), dry_run)
        if dry_run:
            continue
        criado = numero_da_url(url)
        print(f"  criada: {url}")
        if criado is not None and criado != issue.numero:
            print(f"  ATENÇÃO: esperava #{issue.numero}, o GitHub criou #{criado}. "
                  "As referências '#N' nos textos podem apontar para a issue errada.")
        if projeto:
            dono, _, numero_projeto = projeto.partition("/")
            _gh(["gh", "project", "item-add", numero_projeto, "--owner", dono, "--url", url], dry_run)

    print("\nPronto.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True, help="dono/repositório, ex.: monitor-de-vagas/monitor-de-vagas")
    parser.add_argument("--responsavel", action="append", default=[], metavar="APELIDO=USUARIO",
                        help="mapeia joao/vinicius/lucas para o usuário do GitHub (repita para cada um)")
    parser.add_argument("--projeto", metavar="DONO/NUMERO",
                        help="adiciona as issues a um GitHub Project, ex.: monitor-de-vagas/1")
    parser.add_argument("--dry-run", action="store_true", help="só mostra os comandos, não altera nada")
    args = parser.parse_args(argv)

    try:
        responsaveis = parse_responsaveis(args.responsavel)
        importar(args.repo, responsaveis, args.projeto, args.dry_run)
    except ErroBacklog as exc:
        print(f"Erro no backlog:\n{exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Falha ao chamar o gh: {' '.join(exc.cmd[:4])}...\n{exc.stderr}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
