---
numero: 21
titulo: "test(e2e): teste de fumaça com Playwright no CI"
responsavel: vinicius
labels: test, frontend, infra
pontos: 2
sprint: Sprint 2
---
## O que fazer
Um único teste que percorre cadastro → perfil → lista de vagas, com o Compose de pé no CI e o banco semeado.

## Critérios de aceite
- [ ] Roda em todo PR que mexe no front
- [ ] Em caso de falha, salva screenshot/trace como artefato do workflow

## Dependências
Depende de #19 e #23.
