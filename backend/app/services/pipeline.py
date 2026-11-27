import logging
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.coletores.base import ColetaParcial, Coletor, VagaColetada
from app.models import ExecucaoColeta, Vaga
from app.repositories.vagas import ResultadoUpsert, VagaRepository
from app.services.deduplicacao import chave_conteudo, url_canonica
from app.services.normalizacao import (
    detectar_remoto,
    limpar_html,
    limpar_titulo,
    normalizar_cidade,
)

log = logging.getLogger(__name__)

TAMANHO_MAXIMO_ERRO = 2000
_LIMITES = {"titulo": 300, "empresa": 200, "cidade": 120, "url": 2000}


@dataclass(frozen=True)
class ResultadoColeta:
    coletor: str
    total_coletadas: int = 0
    novas: int = 0
    duplicadas: int = 0
    erro: str | None = None
    ids_novos: list[int] = field(default_factory=list)


def agora_utc() -> datetime:
    return datetime.now(UTC)


def para_vaga(coletada: VagaColetada) -> Vaga | None:
    titulo = _cortar(limpar_titulo(coletada.titulo), "titulo")
    url = coletada.url.strip()
    if not titulo or len(url) > _LIMITES["url"]:
        return None
    empresa = _cortar((coletada.empresa or "").strip(), "empresa") or None
    cidade = _cortar(normalizar_cidade(coletada.cidade) or "", "cidade") or None
    return Vaga(
        fonte=coletada.fonte,
        tipo=coletada.tipo,
        titulo=titulo,
        empresa=empresa,
        cidade=cidade,
        remoto=coletada.remoto or detectar_remoto(coletada.cidade, coletada.titulo),
        descricao=limpar_html(coletada.descricao),
        url=url,
        url_canonica=url_canonica(url),
        chave_conteudo=chave_conteudo(titulo, empresa, cidade),
        publicada_em=coletada.publicada_em,
    )


def converter(coletadas: Iterable[VagaColetada]) -> list[Vaga]:
    vagas: list[Vaga] = []
    for coletada in coletadas:
        vaga = para_vaga(coletada)
        if vaga is None:
            log.warning("vaga descartada na conversão: %s", coletada.url[:200])
            continue
        vagas.append(vaga)
    return vagas


def executar_coletor(
    coletor: Coletor, sessao: Session, agora: Callable[[], datetime] = agora_utc
) -> ResultadoColeta:
    execucao = ExecucaoColeta(coletor=coletor.nome, inicio=agora())
    sessao.add(execucao)
    sessao.commit()

    erros: list[str] = []
    total = 0
    salvas = ResultadoUpsert(novas=0, duplicadas=0)
    try:
        coletadas, erros = _coletar(coletor)
        total = len(coletadas)
        salvas = VagaRepository(sessao).salvar_novas(converter(coletadas))
    except Exception as exc:
        sessao.rollback()
        log.exception("coletor %s falhou", coletor.nome)
        erros.append(_descrever(exc))

    execucao.fim = agora()
    execucao.total_coletadas = total
    execucao.novas = salvas.novas
    execucao.duplicadas = salvas.duplicadas
    execucao.erro = _juntar(erros)
    sessao.commit()

    resultado = ResultadoColeta(
        coletor=coletor.nome,
        total_coletadas=total,
        novas=salvas.novas,
        duplicadas=salvas.duplicadas,
        erro=execucao.erro,
        ids_novos=list(salvas.ids_novos),
    )
    log.info(
        "%s: %d coletadas, %d novas, %d duplicadas%s",
        resultado.coletor,
        resultado.total_coletadas,
        resultado.novas,
        resultado.duplicadas,
        f", erro: {resultado.erro}" if resultado.erro else "",
    )
    return resultado


def executar_todos(
    coletores: Iterable[Coletor], fabrica_sessao: Callable[[], Session]
) -> list[ResultadoColeta]:
    resultados: list[ResultadoColeta] = []
    for coletor in coletores:
        try:
            with fabrica_sessao() as sessao:
                resultados.append(executar_coletor(coletor, sessao))
        except Exception as exc:
            log.exception("não deu para registrar a execução de %s", coletor.nome)
            resultados.append(ResultadoColeta(coletor=coletor.nome, erro=_descrever(exc)))
    return resultados


def ultima_execucao(sessao: Session, coletor: str) -> datetime | None:
    consulta = select(func.max(ExecucaoColeta.inicio)).where(ExecucaoColeta.coletor == coletor)
    return sessao.scalar(consulta)


def _coletar(coletor: Coletor) -> tuple[list[VagaColetada], list[str]]:
    try:
        return list(coletor.coletar()), []
    except ColetaParcial as parcial:
        return list(parcial.vagas), list(parcial.erros)


def _cortar(texto: str, campo: str) -> str:
    return texto[: _LIMITES[campo]].strip()


def _descrever(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def _juntar(erros: Sequence[str]) -> str | None:
    if not erros:
        return None
    texto = "; ".join(erros)
    if len(texto) <= TAMANHO_MAXIMO_ERRO:
        return texto
    return texto[: TAMANHO_MAXIMO_ERRO - 3] + "..."
