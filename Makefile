# Atalhos do dia a dia. No Windows: winget install ezwinports.make
# Sem make, rode o comando da direita direto no PowerShell (tabela no README).

.PHONY: up down logs ps test lint format migrate coletar psql

up:  ## sobe db, api e worker
	docker compose up -d --build

down:  ## para tudo (os dados do banco continuam no volume)
	docker compose down

logs:  ## acompanha os logs da api e do worker
	docker compose logs -f api worker

ps:
	docker compose ps

test:  ## roda os testes dentro do container (com Postgres de verdade)
	docker compose run --rm api pytest

lint:
	docker compose run --rm api ruff check .
	docker compose run --rm api ruff format --check .

format:
	docker compose run --rm api ruff check --fix .
	docker compose run --rm api ruff format .

migrate:  ## passa a rodar o Alembic na issue 3
	@echo make migrate chega com a issue 3, Alembic

coletar:  ## passa a rodar o pipeline uma vez na issue 4
	@echo make coletar chega com a issue 4, worker e pipeline

psql:  ## abre o psql dentro do container do banco
	docker compose exec db psql -U monitor -d monitor_vagas
