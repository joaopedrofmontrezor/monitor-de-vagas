import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models import ExecucaoColeta, Vaga
from app.repositories import vagas as modulo_repositorio
from app.repositories.vagas import ResultadoUpsert, VagaRepository
from app.services.deduplicacao import chave_conteudo, url_canonica

pytestmark = pytest.mark.integracao


def nova_vaga(
    titulo: str = "Estágio em Dados",
    empresa: str = "Acme",
    cidade: str = "São Paulo - SP",
    url: str = "https://boards.greenhouse.io/acme/jobs/1",
    **extra,
) -> Vaga:
    return Vaga(
        fonte="greenhouse",
        titulo=titulo,
        empresa=empresa,
        cidade=cidade,
        url=url,
        url_canonica=url_canonica(url),
        chave_conteudo=chave_conteudo(titulo, empresa, cidade),
        **extra,
    )


def total_de_vagas(sessao) -> int:
    return sessao.scalar(select(func.count()).select_from(Vaga))


def test_mesma_vaga_duas_vezes_grava_uma_e_conta_uma_duplicada(sessao):
    repositorio = VagaRepository(sessao)

    primeira = repositorio.salvar_novas([nova_vaga()])
    segunda = repositorio.salvar_novas([nova_vaga()])

    assert (primeira.novas, primeira.duplicadas) == (1, 0)
    assert segunda == ResultadoUpsert(novas=0, duplicadas=1, ids_novos=[])
    assert total_de_vagas(sessao) == 1


def test_duplicada_dentro_do_mesmo_lote(sessao):
    resultado = VagaRepository(sessao).salvar_novas([nova_vaga(), nova_vaga()])

    assert (resultado.novas, resultado.duplicadas) == (1, 1)


def test_mesma_url_com_rastreamento_e_duplicada(sessao):
    repositorio = VagaRepository(sessao)
    repositorio.salvar_novas([nova_vaga(url="https://x.com/vaga/1")])

    resultado = repositorio.salvar_novas(
        [nova_vaga(titulo="Outro título", url="https://x.com/vaga/1/?utm_source=lnkd")]
    )

    assert resultado.duplicadas == 1


def test_mesmo_conteudo_em_outra_url_e_duplicada(sessao):
    repositorio = VagaRepository(sessao)
    repositorio.salvar_novas([nova_vaga(url="https://boards.greenhouse.io/acme/jobs/1")])

    resultado = repositorio.salvar_novas([nova_vaga(url="https://github.com/frontendbr/vagas/9")])

    assert resultado.duplicadas == 1
    assert total_de_vagas(sessao) == 1


def test_vagas_diferentes_sao_todas_novas_e_devolvem_os_ids(sessao):
    vagas = [nova_vaga(titulo=f"Estágio {i}", url=f"https://x.com/{i}") for i in range(3)]

    resultado = VagaRepository(sessao).salvar_novas(vagas)

    assert (resultado.novas, resultado.duplicadas) == (3, 0)
    ids_no_banco = sessao.scalars(select(Vaga.id)).all()
    assert sorted(resultado.ids_novos) == sorted(ids_no_banco)


def test_aplica_os_padroes_e_preenche_coletada_em(sessao):
    VagaRepository(sessao).salvar_novas([nova_vaga()])

    vaga = sessao.scalars(select(Vaga)).one()
    assert vaga.tipo == "estagio"
    assert vaga.remoto is False
    assert vaga.descricao == ""
    assert vaga.coletada_em is not None
    assert vaga.coletada_em.tzinfo is not None


def test_lista_vazia_nao_vai_ao_banco(sessao):
    assert VagaRepository(sessao).salvar_novas([]) == ResultadoUpsert(novas=0, duplicadas=0)


def test_divide_em_lotes(sessao, monkeypatch):
    monkeypatch.setattr(modulo_repositorio, "TAMANHO_LOTE", 2)
    vagas = [nova_vaga(titulo=f"Estágio {i}", url=f"https://x.com/{i}") for i in range(5)]

    resultado = VagaRepository(sessao).salvar_novas(vagas)

    assert resultado.novas == 5
    assert total_de_vagas(sessao) == 5


def test_banco_recusa_tipo_fora_da_lista(sessao):
    with pytest.raises(IntegrityError, match="ck_vagas_tipo"):
        VagaRepository(sessao).salvar_novas([nova_vaga(tipo="clt")])


def test_execucao_coleta_grava_com_padroes(sessao):
    execucao = ExecucaoColeta(coletor="greenhouse")
    sessao.add(execucao)
    sessao.flush()
    sessao.refresh(execucao)

    assert execucao.inicio is not None
    assert (execucao.total_coletadas, execucao.novas, execucao.duplicadas) == (0, 0, 0)
    assert execucao.fim is None and execucao.erro is None
