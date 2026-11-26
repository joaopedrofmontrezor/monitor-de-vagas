# Monitor de Vagas

Monitor automático de vagas de estágio: coleta vagas de fontes públicas em horários
agendados, guarda sem duplicatas, cruza com o perfil de cada usuário e avisa por
Telegram e e-mail. Um painel mostra quantas vagas chegam por dia e por área.

> **Status:** em construção (Sprint 1 de 2). Hoje sobem o banco, a API com `/health` e
> `GET /vagas` (lista com filtros e paginação) e o processo `worker`. Coleta, alertas e telas chegam nas próximas issues.

## Como funciona

```
worker (agendado) → coletores → normalização → dedup → banco (Postgres)
                                                         ↓
              Telegram / e-mail ← matching com os perfis ← vagas novas
                                                         ↓
                                      API (FastAPI) → front (Next.js)
```

| Camada | Tecnologia |
|---|---|
| Front | Next.js, TypeScript, Tailwind, Recharts |
| API | FastAPI |
| Coleta | httpx + BeautifulSoup, agendada com APScheduler num processo `worker` |
| Banco | PostgreSQL, SQLAlchemy, Alembic |
| Testes | pytest, Playwright (E2E) |
| Infra | Docker Compose, GitHub Actions |

As decisões de arquitetura estão em [`docs/adr/`](docs/adr/).

## Como rodar localmente

Os comandos abaixo são para **PowerShell** (Windows). Rode um por vez.

### 1. Pré-requisitos

- [Git](https://git-scm.com/download/win)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) aberto e rodando
- Opcional: `make`, para usar os atalhos. Instale com:

```powershell
winget install --id ezwinports.make -e
```

Depois de instalar, feche e abra o terminal para o `make` entrar no PATH.

### 2. Baixar o projeto e criar o `.env`

```powershell
git clone https://github.com/joaopedrofmontrezor/monitor-de-vagas.git
```

```powershell
cd monitor-de-vagas
```

```powershell
Copy-Item .env.example .env
```

Os valores padrão do `.env` já funcionam. Só mude `POSTGRES_PORTA` se você já tiver
um Postgres instalado usando a porta 5432.

### 3. Subir tudo

```powershell
docker compose up -d --build
```

A primeira vez demora alguns minutos (baixa as imagens e instala as dependências).
Depois confira:

- <http://localhost:8000/health> deve mostrar `{"status":"ok","banco":"ok"}`
- <http://localhost:8000/docs> mostra a documentação interativa da API

```powershell
docker compose ps
```

Na primeira vez (e sempre que alguém adicionar uma migration), crie/atualize as
tabelas do banco:

```powershell
docker compose run --rm api alembic upgrade head
```

Os serviços `db`, `api` e `worker` devem aparecer como `running` (o `db` e a `api`
como `healthy`).

### 4. Comandos do dia a dia

Com `make` instalado, use a coluna da esquerda. Sem `make`, a da direita faz o mesmo.

| Atalho | Comando equivalente |
|---|---|
| `make up` | `docker compose up -d --build` |
| `make down` | `docker compose down` |
| `make logs` | `docker compose logs -f api worker` |
| `make test` | `docker compose run --rm api pytest` |
| `make lint` | `docker compose run --rm api ruff check .` |
| `make format` | `docker compose run --rm api ruff format .` |
| `make psql` | `docker compose exec db psql -U monitor -d monitor_vagas` |
| `make migrate` | `docker compose run --rm api alembic upgrade head` |
| `make migration m="..."` | `docker compose run --rm api alembic revision --autogenerate -m "..."` |
| `make coletar` | chega com a issue #4 |

### 5. Rodar os testes fora do Docker (opcional)

Útil para o VS Code achar os imports e rodar os testes pelo editor. Precisa do
[Python 3.12+](https://www.python.org/downloads/).

```powershell
cd backend
```

```powershell
python -m venv .venv
```

```powershell
.venv\Scripts\Activate.ps1
```

```powershell
pip install -e ".[dev]"
```

```powershell
pytest
```

Os testes de integração precisam do banco: com o `docker compose up` rodando, eles
usam o Postgres do container pela porta 5432 e aplicam as migrations sozinhos antes
de rodar. Sem o banco, eles são pulados (aparecem
como `SKIPPED`), e os testes unitários rodam normalmente.

Se o PowerShell bloquear o `Activate.ps1`, libere scripts só para o seu usuário:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Problemas comuns

- **`port is already allocated`**: outra coisa usa a porta. Troque `POSTGRES_PORTA` ou
  `API_PORTA` no `.env` e rode `docker compose up -d` de novo.
- **A API não recarrega quando salvo um arquivo**: o compose já liga o modo polling
  para o Windows. Se continuar, rode `docker compose restart api`.
- **`/health` responde 503**: o banco não está de pé. Veja `docker compose logs db`.

## Estrutura do repositório

```
backend/    API, worker, coletores e testes (Python)
frontend/   Next.js (chega na issue #10)
docs/adr/   decisões de arquitetura
scripts/    utilitários (importador do backlog para o GitHub)
```

## Scraping responsável

O projeto só coleta de fontes cujos termos de uso permitem, prefere API a HTML,
respeita o `robots.txt`, se identifica no User-Agent e limita a frequência das
requisições. Os testes nunca acessam os sites: usam respostas salvas. A análise das
fontes está no [ADR-0003](docs/adr/0003-scraping-responsavel.md).

## Contribuindo

Fluxo de branch, padrão de commits e Definition of Done estão no
[CONTRIBUTING.md](CONTRIBUTING.md).

## Time

| | GitHub | Área |
|---|---|---|
| João Pedro | [@joaopedrofmontrezor](https://github.com/joaopedrofmontrezor) | Dados e coleta |
| Vinicius | [@ViniciusBovo](https://github.com/ViniciusBovo) | Infra e qualidade |
| Lucas | [@Lucascatto-z](https://github.com/Lucascatto-z) | Produto e notificações |
