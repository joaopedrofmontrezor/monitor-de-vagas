# ADR-0001: Monorepo com front e back no mesmo repositório

- **Status:** aceito
- **Data:** 30/11/2026
- **Autor:** Vinicius (issue #1)

## Contexto

O time tem 3 pessoas e todo mundo mexe em front e back. Uma feature como "tela de
perfil" altera a API (`backend/`) e a tela (`frontend/`) ao mesmo tempo. Precisamos
decidir se isso vive em um repositório só ou em dois.

## Decisão

Um repositório só, com as pastas `backend/`, `frontend/`, `docs/` e `scripts/`, e um
`docker-compose.yml` na raiz que sobe tudo.

## Consequências

**A favor**
- Uma feature que cruza front e back vira um PR só, com uma revisão só.
- Um `docker compose up` sobe o projeto inteiro; o README tem um único "como rodar".
- Issues, ADRs e histórico ficam juntos, o que facilita explicar o projeto em entrevista.

**Contra (e como lidamos)**
- O CI rodaria tudo a cada PR. Resolvido na #2 com um workflow só (`ci.yml`) e um
  job por pasta: o job do back só roda quando `backend/` muda, o do front quando
  `frontend/` muda, e o job `ci-ok` resume o resultado (é o check obrigatório da `main`).
- Deploy separado (Vercel para o front, Render para a API) precisa apontar para a
  subpasta certa. As duas plataformas aceitam "root directory"; fica para a Sprint 3.

## Alternativas consideradas

- **Dois repositórios (front e back):** isola melhor, mas obriga a abrir dois PRs
  coordenados para cada feature e a manter o contrato da API sincronizado à mão.
  Para 3 pessoas e 2 sprints, o custo de coordenação não compensa.
