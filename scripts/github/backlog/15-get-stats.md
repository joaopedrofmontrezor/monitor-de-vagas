---
numero: 15
titulo: "feat(api): GET /stats"
responsavel: joao
labels: feat, backend, dados
pontos: 2
sprint: Sprint 2
---
## O que fazer
Vagas por dia (últimos 30 dias), por área, por fonte, total de alertas enviados e de usuários. Agregação em SQL (`GROUP BY`); Pandas não é necessário nesse volume.

## Critérios de aceite
- [ ] Testes com dados semeados conferindo os números

## Dependências
Depende de #3 e #24 (para alertas; pode retornar 0 até lá).
