---
numero: 8
titulo: "feat(coletores): coletor da fonte A"
responsavel: joao
labels: feat, coleta, backend
pontos: 3
sprint: Sprint 1
---
## O que fazer
Primeiro coletor real, usando o cliente HTTP de #6 e seguindo o template "Novo coletor".

## Critérios de aceite
- [ ] Checklist de scraping responsável preenchido
- [ ] Fixture em `backend/tests/fixtures/` e teste que verifica quantas vagas e quais campos são extraídos
- [ ] Com `make coletar`, grava vagas reais no banco local

## Dependências
Depende de #5 e #6.
