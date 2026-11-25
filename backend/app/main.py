"""Ponto de entrada da API: cria o FastAPI e registra as rotas."""

from fastapi import FastAPI

from app.api.routes import health

app = FastAPI(
    title="Monitor de Vagas",
    description="Coleta vagas de estágio, cruza com o perfil do usuário e envia alertas.",
    version="0.1.0",
)

app.include_router(health.router)
