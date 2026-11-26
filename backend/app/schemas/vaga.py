from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VagaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fonte: str = Field(examples=["greenhouse"])
    tipo: str = Field(examples=["estagio"])
    titulo: str = Field(examples=["Estágio em Engenharia de Dados"])
    empresa: str | None = Field(examples=["Acme"])
    cidade: str | None = Field(examples=["São Paulo - SP"])
    remoto: bool
    url: str = Field(examples=["https://boards.greenhouse.io/acme/jobs/123"])
    publicada_em: datetime | None
    coletada_em: datetime


class PaginaVagas(BaseModel):
    itens: list[VagaSaida]
    total: int = Field(description="Quantas vagas atendem aos filtros, somando todas as páginas")
    pagina: int
    por_pagina: int
    total_paginas: int
