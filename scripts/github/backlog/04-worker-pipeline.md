---
numero: 4
titulo: "feat(worker): APScheduler e pipeline v1"
responsavel: vinicius
labels: feat, backend, infra
pontos: 2
sprint: Sprint 1
---
## Contexto
O scheduler roda num processo `worker` separado da API para a coleta não rodar duplicada quando houver mais de um worker do uvicorn (ver ADR-0004).

## O que fazer
- `backend/app/worker/scheduler.py`: um job por coletor do registry
- `backend/app/services/pipeline.py`: coleta → normalização → repositório → registro da execução
- Falha de um coletor não derruba os outros
- Escrever o ADR-0004

## Critérios de aceite
- [ ] Intervalo configurável por variável de ambiente
- [ ] `make coletar` roda o pipeline uma vez, na hora
- [ ] Teste com coletor falso que levanta exceção: a execução fica registrada com erro

## Dependências
Depende de #3 e #6.
