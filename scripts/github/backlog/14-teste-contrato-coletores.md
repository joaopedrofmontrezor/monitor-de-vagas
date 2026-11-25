---
numero: 14
titulo: "test(coletores): teste de contrato para todo coletor registrado"
responsavel: joao
labels: test, coleta
pontos: 1
sprint: Sprint 2
---
## O que fazer
Teste parametrizado pelo registry: todo coletor tem `nome` e `intervalo_horas` e, com sua fixture, devolve `VagaColetada` com `url` e `titulo` preenchidos. Coletor novo já nasce testado.

## Critérios de aceite
- [ ] Falha com mensagem clara se um coletor não tiver fixture

## Dependências
Depende de #8.
