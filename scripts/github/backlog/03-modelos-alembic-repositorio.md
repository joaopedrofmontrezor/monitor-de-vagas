---
numero: 3
titulo: "feat(db): modelos iniciais, Alembic e repositório de vagas"
responsavel: vinicius
labels: feat, backend, infra
pontos: 2
sprint: Sprint 1
---
## O que fazer
- Modelos `Vaga` (com `tipo`, `url_canonica`, `chave_conteudo`, `coletada_em`) e `ExecucaoColeta` (início, fim, coletor, totais, erro)
- Primeira migration do Alembic
- `VagaRepository.salvar_novas(vagas) -> ResultadoUpsert` (quantas novas, quantas duplicadas)
- `UNIQUE` em `url_canonica` e em `chave_conteudo`: quem garante "sem duplicata" é o banco

## Critérios de aceite
- [ ] `make migrate` cria as tabelas
- [ ] Teste de integração: salvar a mesma vaga duas vezes grava uma só e retorna 1 duplicada

## Dependências
Depende de #1. Usa as funções de #7 (pode começar com um stub).
