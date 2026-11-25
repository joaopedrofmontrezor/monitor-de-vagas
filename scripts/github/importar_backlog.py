
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

PASTA_BACKLOG = Path(__file__).parent / "backlog"

LABELS: dict[str, tuple[str, str]] = {
    "feat": ("1d76db", "Nova funcionalidade"),
    "fix": ("d73a4a", "Correção de bug"),
    "chore": ("cfd3d7", "Manutenção, configuração, estrutura"),
    "docs": ("0075ca", "Documentação"),
    "test": ("bfd4f2", "Testes"),
    "ci": ("5319e7", "Integração contínua"),
    "spike": ("fbca04", "Pesquisa com prazo curto antes de implementar"),
    "backend": ("0e8a16", "API e regras de negócio (FastAPI)"),
    "frontend": ("c2e0c6", "Next.js"),
    "coleta": ("006b75", "Coletores e scraping"),
    "dados": ("7057ff", "Estatísticas e painel"),
    "notificacoes": ("e99695", "Telegram e e-mail"),
    "infra": ("5a5a5a", "Docker, banco, CI, deploy"),
    "p0": ("b60205", "Sem isso a demo da sprint não acontece"),
    "p1": ("f9d0c4", "Importante, mas não bloqueia a demo"),
}

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
    pass


def parse_issue(texto: str, arquivo: str = "") -> Issue:
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
    resumo: dict[str, dict[str, int]] = {}
    for i in issues:
        sprint = resumo.setdefault(i.sprint, {})
        sprint[i.responsavel] = sprint.get(i.responsavel, 0) + i.pontos
    return resumo


def parse_responsaveis(pares: list[str]) -> dict[str, str]:
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


def montar_payload_issue(
    issue: Issue, milestones: dict[str, int], responsaveis: dict[str, str]
) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": issue.titulo,
        "body": issue.corpo_completo(),
        "labels": issue.labels,
    }
    if issue.sprint in milestones:
        payload["milestone"] = milestones[issue.sprint]
    if issue.responsavel in responsaveis:
        payload["assignees"] = [responsaveis[issue.responsavel]]
    return payload


def numero_da_url(url: str) -> int | None:
    m = re.search(r"/issues/(\d+)\s*$", url.strip())
    return int(m.group(1)) if m else None




def _api(caminho: str, metodo: str = "GET", corpo: dict | None = None):
    args = ["gh", "api", caminho, "--method", metodo]
    if metodo == "GET":
        args += ["--paginate", "--jq", ".[] | tojson"]
    if corpo is not None:
        args += ["--input", "-"]
    res = subprocess.run(
        args, check=True, text=True, capture_output=True, encoding="utf-8",
        input=json.dumps(corpo) if corpo is not None else None,
    )
    if metodo == "GET":
        return [json.loads(linha) for linha in res.stdout.splitlines() if linha.strip()]
    return json.loads(res.stdout) if res.stdout.strip() else None


def _mostrar(acao: str, detalhe: str) -> None:
    print(f"  [dry-run] {acao}: {detalhe}")


def importar(repo: str, responsaveis: dict[str, str], projeto: str | None, dry_run: bool) -> None:
    issues = carregar_backlog()
    print(f"Backlog válido: {len(issues)} issues.")
    for sprint, pessoas in pontos_por_pessoa(issues).items():
        print(f"  {sprint}: " + ", ".join(f"{p} {pts} pts" for p, pts in sorted(pessoas.items())))
    sem_dono = RESPONSAVEIS_VALIDOS - responsaveis.keys()
    if sem_dono:
        print(f"Aviso: sem usuário do GitHub para {sorted(sem_dono)}; essas issues ficam sem assignee.")

    print("\nLabels")
    labels_existentes = set() if dry_run else {l["name"] for l in _api(f"repos/{repo}/labels?per_page=100")}
    for nome, (cor, descricao) in LABELS.items():
        dados = {"color": cor, "description": descricao}
        if dry_run:
            _mostrar("label", nome)
        elif nome in labels_existentes:
            _api(f"repos/{repo}/labels/{nome}", "PATCH", dados)
            print(f"  atualizada: {nome}")
        else:
            _api(f"repos/{repo}/labels", "POST", {"name": nome, **dados})
            print(f"  criada: {nome}")

    print("\nMilestones")
    milestones: dict[str, int] = {}
    if not dry_run:
        milestones = {m["title"]: m["number"] for m in _api(f"repos/{repo}/milestones?state=all&per_page=100")}
    for titulo, data in MILESTONES.items():
        if dry_run:
            _mostrar("milestone", f"{titulo} (entrega {data})")
        elif titulo in milestones:
            print(f"  já existe: {titulo}")
        else:
            criada = _api(f"repos/{repo}/milestones", "POST", {"title": titulo, "due_on": f"{data}T23:59:59Z"})
            milestones[titulo] = criada["number"]
            print(f"  criada: {titulo}")

    print("\nIssues")
    ja_criadas: set[str] = set()
    if not dry_run:
        ja_criadas = {
            i["title"] for i in _api(f"repos/{repo}/issues?state=all&per_page=100") if "pull_request" not in i
        }
    for issue in issues:
        if issue.titulo in ja_criadas:
            print(f"  já existe: #{issue.numero} {issue.titulo}")
            continue
        payload = montar_payload_issue(issue, milestones, responsaveis)
        if dry_run:
            dono = payload.get("assignees", ["(sem assignee)"])[0]
            _mostrar(f"issue #{issue.numero}", f"{issue.titulo} [{issue.sprint}, {dono}, {', '.join(issue.labels)}]")
            continue
        criada = _api(f"repos/{repo}/issues", "POST", payload)
        print(f"  criada: #{criada['number']} {issue.titulo}")
        if criada["number"] != issue.numero:
            print(f"  ATENÇÃO: esperava #{issue.numero}, o GitHub criou #{criada['number']}. "
                  "As referências '#N' nos textos podem apontar para a issue errada.")
        if responsaveis.get(issue.responsavel) and not criada.get("assignees"):
            print(f"  ATENÇÃO: {responsaveis[issue.responsavel]} não foi atribuído "
                  "(convite de colaborador pendente?)")
        if projeto:
            dono_proj, _, numero_projeto = projeto.partition("/")
            subprocess.run(["gh", "project", "item-add", numero_projeto, "--owner", dono_proj,
                            "--url", criada["html_url"]], check=True, text=True, capture_output=True)

    print("\nPronto.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Importa o backlog do MVP para o GitHub: labels, milestones e issues.", formatter_class=argparse.RawDescriptionHelpFormatter)
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
