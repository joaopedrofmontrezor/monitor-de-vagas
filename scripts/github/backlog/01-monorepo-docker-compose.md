---
numero: 1
titulo: "chore(infra): estrutura do monorepo e Docker Compose"
responsavel: vinicius
labels: chore, infra, p0
pontos: 3
sprint: Sprint 1
---
## Contexto
Primeira issue da sprint: bloqueia todas as outras. Precisa sair na segunda/terça.

## O que fazer
Criar a estrutura de pastas do monorepo (`backend/`, `frontend/`, `docs/adr/`, `scripts/`), `docker-compose.yml` com `db` (Postgres), `api`, `worker` e `frontend`, `.env.example`, `Makefile` (`make up`, `make test`, `make migrate`, `make coletar`) e `.pre-commit-config.yaml` (ruff + eslint). Escrever o ADR-0001 (monorepo).

## Critérios de aceite
- [ ] `make up` sobe tudo numa máquina limpa
- [ ] `GET /health` responde 200 e confirma a conexão com o banco
- [ ] Nenhum segredo no repositório; `.env` no `.gitignore`
- [ ] ADR-0001 em `docs/adr/`

## Dependências
Nenhuma.
