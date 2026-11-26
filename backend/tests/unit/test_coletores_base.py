from dataclasses import FrozenInstanceError

import pytest

from app.coletores.base import VagaColetada
from app.coletores.registry import INTERVALO_MINIMO_HORAS, RegistroColetores, registro_padrao


class ColetorFalso:
    def __init__(self, nome: str = "falso", intervalo_horas: int = 6) -> None:
        self.nome = nome
        self.intervalo_horas = intervalo_horas

    def coletar(self) -> list[VagaColetada]:
        return [VagaColetada(fonte=self.nome, url="https://x.com/1", titulo="Estágio")]


def test_vaga_coletada_tem_padroes_do_mvp():
    vaga = VagaColetada(fonte="greenhouse", url="https://x.com/1", titulo="Estágio em Dados")

    assert vaga.tipo == "estagio"
    assert vaga.remoto is False
    assert vaga.descricao == ""
    assert vaga.empresa is None and vaga.cidade is None and vaga.publicada_em is None


def test_vaga_coletada_e_imutavel():
    vaga = VagaColetada(fonte="f", url="https://x.com/1", titulo="t")

    with pytest.raises(FrozenInstanceError):
        vaga.titulo = "outro"


@pytest.mark.parametrize(
    ("campos", "mensagem"),
    [
        ({"url": " ", "titulo": "t"}, "sem url"),
        ({"url": "https://x.com/1", "titulo": ""}, "sem título"),
        ({"url": "https://x.com/1", "titulo": "t", "tipo": "clt"}, "tipo inválido"),
    ],
)
def test_vaga_coletada_rejeita_dados_invalidos(campos, mensagem):
    with pytest.raises(ValueError, match=mensagem):
        VagaColetada(fonte="f", **campos)


def test_registro_guarda_e_devolve_em_ordem_de_nome():
    registro = RegistroColetores()
    b = registro.registrar(ColetorFalso("github"))
    a = registro.registrar(ColetorFalso("greenhouse"))

    assert registro.nomes() == ["github", "greenhouse"]
    assert registro.todos() == [b, a]
    assert registro.obter("greenhouse") is a
    assert len(registro) == 2


def test_registro_recusa_nome_repetido():
    registro = RegistroColetores()
    registro.registrar(ColetorFalso("greenhouse"))

    with pytest.raises(ValueError, match="já registrado"):
        registro.registrar(ColetorFalso("greenhouse"))


@pytest.mark.parametrize("nome", ["", "Green House", "1fonte", "fonte-a"])
def test_registro_recusa_nome_invalido(nome):
    with pytest.raises(ValueError, match="nome de coletor inválido"):
        RegistroColetores().registrar(ColetorFalso(nome))


def test_registro_recusa_intervalo_menor_que_o_minimo():
    with pytest.raises(ValueError, match="mínimo"):
        RegistroColetores().registrar(ColetorFalso(intervalo_horas=INTERVALO_MINIMO_HORAS - 1))


def test_obter_coletor_inexistente_lista_os_disponiveis():
    registro = RegistroColetores()
    registro.registrar(ColetorFalso("github"))

    with pytest.raises(KeyError, match="disponíveis: github"):
        registro.obter("gupy")


def test_coletor_falso_cumpre_o_protocolo():
    vagas = ColetorFalso().coletar()

    assert all(isinstance(v, VagaColetada) for v in vagas)


def test_registro_padrao_comeca_vazio_ate_a_issue_8():
    assert registro_padrao().nomes() == []
