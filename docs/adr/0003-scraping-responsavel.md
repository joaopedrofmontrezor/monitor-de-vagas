# ADR-0003: Scraping responsável e escolha das fontes do MVP

- **Status:** aceito
- **Data:** 30/11/2026 (pesquisa feita em 25/11/2026)
- **Autor:** João Pedro (spike #5)

## Contexto

O MVP precisa de 2 fontes de vagas de estágio. O projeto se vende como "scraping
responsável", então a fonte tem que passar por quatro perguntas antes de qualquer
código: tem API pública ou RSS? O robots.txt permite? Os termos de uso permitem
coleta automatizada? O conteúdo é HTML estático ou depende de JavaScript?

## Fontes avaliadas

| Fonte | Acesso | robots.txt | Termos de uso | Estágio hoje | Veredito |
|---|---|---|---|---|---|
| [Greenhouse Job Board API](https://docs.greenhouse.io/job-board.html) (várias empresas) | API JSON pública, GET sem autenticação | não se aplica (API documentada) | documentada para as empresas montarem páginas de carreira; não encontramos restrição à leitura por terceiros | baixo e sazonal (0 em QuintoAndar, VTEX, Ebanx e iFood no dia da pesquisa) | **Fonte A** |
| Repositórios de vagas no GitHub ([frontendbr/vagas](https://github.com/frontendbr/vagas), [backend-br/vagas](https://github.com/backend-br/vagas)) | API REST do GitHub | não se aplica (API) | uso da API permitido; conteúdo público feito para divulgar vagas | baixo (0 abertas com label de estágio no dia), só TI | **Fonte B** |
| [Gupy](https://portal.gupy.io) | API JSON do portal (não documentada para terceiros) | libera tudo (`Disallow:` vazio) | proíbe "agregar, copiar ou duplicar partes" da plataforma ([termos](https://www.gupy.io/termos-de-uso-recrutamento-e-selecao-candidatos)) | alto | descartada |
| [Vagas.com](https://www.vagas.com.br) | HTML estático | bloqueia `/vagas/pesquisas` e `/api/` | proíbe reproduzir o conteúdo, total ou parcialmente (seção 12 dos [termos](https://www.vagas.com.br/candidatos/termos-de-uso)) | alto | descartada |
| [Nube](https://www.nube.com.br/estudantes/vagas) | lista montada por JavaScript | libera a área pública (só bloqueia `/gestor/`) | não encontrei os termos publicados | alto | adiada (precisa de Playwright e de checar os termos) |
| LinkedIn, Indeed | — | — | proíbem coleta automatizada | alto | descartadas de saída |

O padrão é claro: as fontes com mais vagas de estágio são justamente as que
proíbem agregação nos termos. Seguir o robots.txt não basta — a Gupy libera tudo
no robots.txt e proíbe nos termos.

## Decisão

1. **Fonte A (#8): Greenhouse Job Board API.** Endpoint
   `GET https://boards-api.greenhouse.io/v1/boards/{empresa}/jobs?content=true`.
   O coletor recebe uma lista de empresas (configurável) e fica só com as vagas cujo
   título indica estágio (`estágio`, `estagiário(a)`, `intern`, `internship`).
2. **Fonte B (#13): repositórios de vagas do GitHub**, via
   `GET https://api.github.com/repos/{dono}/{repo}/issues?labels=...&state=open`,
   filtrando pela label de estágio de cada repositório (`Estágio` no frontendbr,
   `Estagiário` no backend-br).
3. As duas são API. O BeautifulSoup continua no projeto para limpar o HTML das
   descrições (o Greenhouse manda HTML). Coletor de HTML com Playwright (Nube, por
   exemplo) fica para depois do MVP, e só depois de ler os termos.

### Regras de coleta (valem para todo coletor)

- Sempre pelo cliente compartilhado `coletores/http.py` (#6): User-Agent
  `MonitorDeVagas/0.1 (+https://github.com/joaopedrofmontrezor/monitor-de-vagas)`,
  timeout, no máximo 1 requisição a cada 2 s por domínio, retry com espera e cache.
- Intervalo mínimo entre coletas da mesma fonte: 6 horas.
- GitHub sem token aceita 60 requisições por hora: sobra, com 2 repositórios a cada 6 h.
- Testes nunca acessam a rede: usam respostas salvas em `backend/tests/fixtures/`.
- Guardamos só dados da vaga. Nada de dados pessoais de quem publicou (no GitHub,
  o autor da issue não é salvo).

## Consequências

- **Risco principal: pouco volume de estágio.** Programas de estágio são sazonais.
  Mitigação na #8: montar a lista de empresas do Greenhouse com as que têm programa
  de estágio aberto na semana (buscar `job-boards.greenhouse.io estágio`) e anotar o
  volume coletado em `docs/metricas.md`. Se a demo de sexta ficar sem vaga de
  estágio, o filtro de título vira configurável e a demo roda com "júnior" incluso,
  dizendo isso abertamente.
- Locais vêm em formatos bem diferentes nas fontes. Os exemplos reais
  ("Osasco, Sao Paulo, Brazil", "Híbrido em São Paulo/SP", "Curitiba | On-site",
  "Remote in Buenos Aires") viraram os casos de teste da #7, em
  `backend/tests/unit/test_normalizacao.py`.
- Nos repositórios do GitHub as labels nem sempre batem com o texto (vaga "[HÍBRIDO]"
  com label "Presencial", vagas de pleno marcadas também como estágio). O coletor B
  precisa confiar mais no título e no corpo do que nas labels.

## Alternativas consideradas

- **Gupy ou Vagas.com mesmo assim:** dariam volume, mas contrariam os termos de uso.
  Para um projeto que se apresenta como scraping responsável, seria o pior exemplo
  possível em entrevista.
- **Lever Postings API** (`api.lever.co/v0/postings/{empresa}`): mesma ideia do
  Greenhouse e também pública. Fica como terceira fonte se o volume do Greenhouse
  for baixo demais.
