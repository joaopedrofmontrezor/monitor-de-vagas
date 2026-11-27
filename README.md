# Monitor de Vagas

Monitor automático de vagas de estágio: coleta vagas de fontes públicas em horários
agendados, guarda sem duplicatas, cruza com o perfil de cada usuário e avisa por
Telegram e e-mail. Um painel mostra quantas vagas chegam por dia e por área.

> **Status:** em construção (Sprint 1 de 2). Hoje sobem o banco, a API com `/health` e
> `GET /vagas` (lista com filtros e paginação) e o processo `worker`, que agenda a coleta
> e grava cada execução em `execucoes_coleta`, e o front em Next.js com a página `/vagas`
> (busca, filtros e paginação). Alertas, login e painel chegam nas próximas issues.

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

- <http://localhost:3000/vagas> é o site (lista de vagas com busca e filtros)
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

Os serviços `db`, `api`, `worker` e `frontend` devem aparecer como `running` (o `db` e
a `api` como `healthy`).

### 4. Comandos do dia a dia

Com `make` instalado, use a coluna da esquerda. Sem `make`, a da direita faz o mesmo.

| Atalho | Comando equivalente |
|---|---|
| `make up` | `docker compose up -d --build` |
| `make down` | `docker compose down` |
| `make logs` | `docker compose logs -f api worker frontend` |
| `make test` | `docker compose run --rm api pytest` |
| `make lint` | `docker compose run --rm api ruff check .` |
| `make format` | `docker compose run --rm api ruff format .` |
| `make psql` | `docker compose exec db psql -U monitor -d monitor_vagas` |
| `make migrate` | `docker compose run --rm api alembic upgrade head` |
| `make migration m="..."` | `docker compose run --rm api alembic revision --autogenerate -m "..."` |
| `make coletar` | `docker compose run --rm worker python -m app.worker.coletar` |
| `make coletar c=greenhouse` | `docker compose run --rm worker python -m app.worker.coletar greenhouse` |

O `make coletar` roda a coleta uma vez, na hora, e mostra quantas vagas vieram, quantas
eram novas e quantas já estavam no banco. O worker faz a mesma coisa sozinho, no
intervalo de cada coletor (veja `docker compose logs -f worker`). Quando o worker
reinicia, ele olha a última coleta no banco e não coleta de novo antes do intervalo.

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

Os testes **não usam o banco do app**: eles criam e usam um banco separado com o mesmo
nome e o sufixo `_teste` (ex.: `monitor_vagas_teste`), no mesmo Postgres. Assim as
vagas coletadas de verdade não atrapalham os testes, e os testes não mexem nelas. Vale
também para o `make test` / `docker compose run --rm api pytest`.

Se o PowerShell bloquear o `Activate.ps1`, libere scripts só para o seu usuário:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 6. Desenvolver o front fora do Docker (opcional)

O serviço `frontend` do compose serve para ver tudo junto. Para mexer no front, o
`npm run dev` direto no Windows recarrega mais rápido. Precisa do
[Node.js 24](https://nodejs.org/) e da API no ar (`docker compose up -d db api`).

```powershell
cd frontend
```

```powershell
npm ci
```

```powershell
npm run dev -- --port 3001
```

Abra <http://localhost:3001/vagas>. Sem a variável `API_URL`, o front usa
`http://localhost:8000`. Antes do commit, rode `npm run lint` e `npm test` (o CI roda
os dois, mais `tsc --noEmit` e `npm run build`).

### Problemas comuns

- **`port is already allocated`**: outra coisa usa a porta. Troque `POSTGRES_PORTA`,
  `API_PORTA` ou `FRONT_PORTA` no `.env` (a `FRONT_PORTA` não vem no `.env.example`:
  acrescente a linha, ex. `FRONT_PORTA=3002`) e rode `docker compose up -d` de novo.
- **A API não recarrega quando salvo um arquivo**: o compose já liga o modo polling
  para o Windows. Se continuar, rode `docker compose restart api`.
- **`/health` responde 503**: o banco não está de pé. Veja `docker compose logs db`.

## Estrutura do repositório

```
backend/    API, worker, coletores e testes (Python)
frontend/   site em Next.js (src/app, src/components, src/lib/api.ts)
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
