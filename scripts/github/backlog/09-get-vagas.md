---
numero: 9
titulo: "feat(api): GET /vagas com paginação e filtros"
responsavel: lucas
labels: feat, backend
pontos: 2
sprint: Sprint 1
---
## O que fazer
- Parâmetros: `q` (busca no título), `cidade`, `remoto`, `pagina`, `por_pagina` (máx. 50)
- Ordem: mais recentes primeiro
- Schema de saída em `schemas/vaga.py`

## Critérios de aceite
- [ ] Testes com `TestClient`: filtros combinados, paginação e lista vazia
- [ ] Documentado no `/docs` do FastAPI

## Dependências
Depende de #3 (até lá, desenvolver com um repositório falso).
