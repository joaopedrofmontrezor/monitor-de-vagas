---
name: Novo coletor
about: Adicionar uma nova fonte de vagas
title: "feat(coletores): coletor da fonte "
labels: feat, coleta, backend
---

## Fonte
- Nome:
- URL:

## Checklist de scraping responsável (preencher ANTES de codar)
- [ ] Existe API pública ou RSS? Se sim, usar no lugar do HTML.
- [ ] robots.txt permite os caminhos que vamos acessar? (colar o trecho relevante)
- [ ] Os termos de uso não proíbem coleta automatizada? (link do trecho)
- [ ] O conteúdo é HTML estático (httpx + BeautifulSoup) ou precisa de JavaScript (Playwright)?
- [ ] Intervalo de coleta definido (mínimo de horas entre execuções):

## Critérios de aceite
- [ ] Usa o cliente HTTP compartilhado (`coletores/http.py`), nunca httpx direto
- [ ] Fixture salva em `backend/tests/fixtures/` e teste do coletor sem acesso à rede
- [ ] Passa no teste de contrato dos coletores
- [ ] Linha adicionada na tabela de fontes do ADR-0003
