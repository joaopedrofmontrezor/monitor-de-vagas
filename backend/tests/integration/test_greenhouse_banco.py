import json
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select

from app.coletores.greenhouse import ColetorGreenhouse
from app.coletores.http import ClienteHttp
from app.models import Vaga
from app.services.pipeline import executar_coletor

pytestmark = pytest.mark.integracao

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "greenhouse"


def servidor(request: httpx.Request) -> httpx.Response:
    lista = json.loads((FIXTURES / "btgpactual_jobs.json").read_text(encoding="utf-8"))
    if request.url.path.endswith("/jobs"):
        return httpx.Response(200, json=lista)
    if request.url.path.endswith("/4012001"):
        detalhe = (FIXTURES / "btgpactual_job_4012001.json").read_text(encoding="utf-8")
        return httpx.Response(200, json=json.loads(detalhe))
    id_vaga = int(request.url.path.rsplit("/", 1)[1])
    return httpx.Response(200, json=next(j for j in lista["jobs"] if j["id"] == id_vaga))


def coletor() -> ColetorGreenhouse:
    return ColetorGreenhouse(
        {"btgpactual": "BTG Pactual"},
        criar_cliente=lambda: ClienteHttp(
            transport=httpx.MockTransport(servidor), intervalo_por_dominio=0
        ),
    )


def test_pipeline_grava_as_vagas_do_greenhouse_normalizadas(sessao):
    resultado = executar_coletor(coletor(), sessao)

    assert (resultado.total_coletadas, resultado.novas, resultado.erro) == (5, 5, None)
    vagas = {
        v.url.rsplit("/", 1)[1]: v
        for v in sessao.scalars(select(Vaga).where(Vaga.fonte == "greenhouse"))
    }
    assert vagas["4012001"].cidade == "São Paulo - SP"
    assert vagas["4012001"].descricao.startswith("Sobre a vaga\nVocê vai apoiar o time de")
    assert vagas["4012005"].cidade == "Campinas - SP"
    assert vagas["4012007"].remoto is True
    assert vagas["4012007"].cidade is None


def test_segunda_coleta_nao_duplica(sessao):
    executar_coletor(coletor(), sessao)

    resultado = executar_coletor(coletor(), sessao)

    assert (resultado.novas, resultado.duplicadas) == (0, 5)
