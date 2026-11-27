# Atalhos do dia a dia. No Windows: winget install ezwinports.make
# Sem make, rode o comando da direita direto no PowerShell (tabela no README).

.PHONY: up down logs ps test lint format migrate migration coletar psql

up:  ## sobe db, api, worker e frontend
	docker compose up -d --build

down:  ## para tudo (os dados do banco continuam no volume)
	docker compose down

logs:  ## acompanha os logs da api, do worker e do frontend
	docker compose logs -f api worker frontend

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

migrate:  ## aplica as migrations pendentes (cria/atualiza as tabelas)
	docker compose run --rm api alembic upgrade head

migration:  ## gera migration a partir dos models. Uso: make migration m="adiciona perfis"
	docker compose run --rm api alembic revision --autogenerate -m "$(m)"

coletar:  ## roda o pipeline uma vez, na hora. Só um coletor: make coletar c=greenhouse
	docker compose run --rm worker python -m app.worker.coletar $(c)

psql:  ## abre o psql dentro do container do banco
	docker compose exec db psql -U monitor -d monitor_vagas
