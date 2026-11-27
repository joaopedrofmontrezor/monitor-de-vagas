import re

from app.coletores.base import Coletor
from app.coletores.greenhouse import ColetorGreenhouse, empresas_configuradas
from app.config import settings

INTERVALO_MINIMO_HORAS = 6
_NOME_VALIDO = re.compile(r"^[a-z][a-z0-9_]*$")


class RegistroColetores:
    def __init__(self) -> None:
        self._coletores: dict[str, Coletor] = {}

    def registrar(self, coletor: Coletor) -> Coletor:
        if not _NOME_VALIDO.match(coletor.nome):
            raise ValueError(
                f"nome de coletor inválido {coletor.nome!r}: use minúsculas, números e _"
            )
        if coletor.nome in self._coletores:
            raise ValueError(f"coletor {coletor.nome!r} já registrado")
        if coletor.intervalo_horas < INTERVALO_MINIMO_HORAS:
            raise ValueError(
                f"coletor {coletor.nome!r} com intervalo de {coletor.intervalo_horas}h; "
                f"o mínimo é {INTERVALO_MINIMO_HORAS}h (ADR-0003)"
            )
        self._coletores[coletor.nome] = coletor
        return coletor

    def obter(self, nome: str) -> Coletor:
        try:
            return self._coletores[nome]
        except KeyError:
            disponiveis = ", ".join(self.nomes()) or "nenhum"
            raise KeyError(
                f"coletor {nome!r} não registrado (disponíveis: {disponiveis})"
            ) from None

    def nomes(self) -> list[str]:
        return sorted(self._coletores)

    def todos(self) -> list[Coletor]:
        return [self._coletores[nome] for nome in self.nomes()]

    def __len__(self) -> int:
        return len(self._coletores)


def registro_padrao() -> RegistroColetores:
    registro = RegistroColetores()
    registro.registrar(ColetorGreenhouse(empresas_configuradas(settings.greenhouse_empresas)))
    return registro
