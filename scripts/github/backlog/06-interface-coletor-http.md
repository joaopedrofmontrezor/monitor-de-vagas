---
numero: 6
titulo: "feat(coletores): interface Coletor, registry e cliente HTTP responsável"
responsavel: joao
labels: feat, coleta, backend, p0
pontos: 3
sprint: Sprint 1
---
## Contexto
É o contrato que todos usam (#4, #7, #8, #13). Abrir primeiro um PR pequeno só com `base.py` para revisão rápida.

## O que fazer
- `coletores/base.py`: `VagaColetada` (dataclass) e `Coletor` (Protocol) com `nome`, `intervalo_horas` e `coletar() -> list[VagaColetada]`
- `coletores/registry.py`: registro dos coletores
- `coletores/http.py`: User-Agent com nome do projeto e contato, timeout, no máximo 1 requisição a cada X segundos por domínio, retry com espera exponencial, cache simples em disco
- ADR-0002 (coletores plugáveis)

## Critérios de aceite
- [ ] Testes do rate limit e do retry com `httpx.MockTransport` (sem rede)
- [ ] ADR-0002 em `docs/adr/`

## Dependências
Depende de #1.
