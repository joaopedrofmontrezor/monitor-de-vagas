---
numero: 5
titulo: "spike(coleta): pesquisar e escolher as 2 fontes do MVP"
responsavel: joao
labels: spike, coleta, p0
pontos: 1
sprint: Sprint 1
---
## O que fazer
Avaliar 4 a 5 sites de vagas de estágio:
- Tem API pública ou RSS?
- O que diz o robots.txt?
- Os termos de uso permitem coleta automatizada?
- O HTML é estático ou depende de JavaScript?

Evitar fontes cujos termos proíbem coleta (ex.: LinkedIn, Indeed).

## Critérios de aceite
- [ ] Tabela comparativa no ADR-0003 (scraping responsável)
- [ ] 2 fontes escolhidas, ao menos uma via API/RSS ou HTML estático
- [ ] Exemplos reais de cidade/remoto anotados para os testes da #7

## Dependências
Nenhuma.
