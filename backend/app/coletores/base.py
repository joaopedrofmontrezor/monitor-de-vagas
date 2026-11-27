from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

TIPOS_VAGA = ("estagio", "edital")


@dataclass(frozen=True)
class VagaColetada:
    fonte: str
    url: str
    titulo: str
    empresa: str | None = None
    cidade: str | None = None
    remoto: bool = False
    tipo: str = "estagio"
    descricao: str = ""
    publicada_em: datetime | None = None

    def __post_init__(self) -> None:
        if not self.url.strip():
            raise ValueError("VagaColetada sem url")
        if not self.titulo.strip():
            raise ValueError(f"VagaColetada sem título ({self.url})")
        if self.tipo not in TIPOS_VAGA:
            raise ValueError(f"tipo inválido {self.tipo!r}; use um de {TIPOS_VAGA}")


class ColetaParcial(Exception):
    def __init__(self, vagas: list[VagaColetada], erros: list[str]) -> None:
        super().__init__("; ".join(erros))
        self.vagas = vagas
        self.erros = erros


class Coletor(Protocol):
    nome: str
    intervalo_horas: int

    def coletar(self) -> list[VagaColetada]: ...
