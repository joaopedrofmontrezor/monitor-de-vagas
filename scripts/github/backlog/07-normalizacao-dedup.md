---
numero: 7
titulo: "feat(dados): normalização e deduplicação"
responsavel: joao
labels: feat, coleta, backend
pontos: 2
sprint: Sprint 1
---
## O que fazer
- `services/deduplicacao.py`: `normalizar_texto`, `url_canonica`, `chave_conteudo` (código de partida e testes no doc de planejamento, seção 4)
- `services/normalizacao.py`: limpar HTML da descrição, padronizar cidade ("São Paulo - SP", "sp", "São Paulo/SP" → uma forma só), detectar remoto pelo texto

## Critérios de aceite
- [ ] Testes parametrizados com casos reais levantados na #5
- [ ] Cobertura ≥ 80% nos dois módulos

## Dependências
Nenhuma (funções puras).
