# ADR-0005: O front busca as vagas no servidor do Next.js

- **Status:** aceito
- **Data:** 30/11/2026
- **Autor:** Lucas (issue #10)

## Contexto

A página `/vagas` lista o `GET /vagas` da API (#9) com busca, filtros e paginação, e
a URL precisa refletir os filtros (`/vagas?q=dados&remoto=true`) para dar para
compartilhar o link e usar o botão Voltar. A API roda em outra porta (8000), então
chamar a API direto do navegador exigiria CORS na API e uma URL pública da API
embutida no JavaScript.

## Decisão

1. **A página é um Server Component.** `src/app/vagas/page.tsx` lê os filtros de
   `searchParams` (`lerFiltros`) e o componente `ListaVagas` chama a API no servidor
   do Next. No compose, o servidor fala com `http://api:8000` pela rede interna
   (variável `API_URL`, só do servidor; sem o prefixo `NEXT_PUBLIC_`). O navegador
   nunca chama a API: **sem CORS** e sem mexer no backend.
2. **`src/lib/api.ts` é o único lugar que chama a API.** `listarVagas()` monta a URL
   (`urlDeVagas`), usa `cache: "no-store"` (vaga nova tem que aparecer na hora) e
   transforma status de erro e falha de rede em `ErroApi`. O `fetch` é injetável,
   então os testes não sobem servidor.
3. **A URL é a fonte da verdade dos filtros.** O formulário (`FormularioFiltros`,
   único Client Component) só monta a URL com `montarBusca()` e navega; filtro
   vazio não aparece na URL e uma busca nova volta para a página 1. A paginação usa
   links comuns com os mesmos filtros.
4. **Estados:** carregando com `<Suspense key=...>` (a chave muda a cada filtro, então
   o esqueleto aparece a cada busca) e `loading.tsx` na primeira carga; vazio com
   duas mensagens (com filtro: sugere limpar; sem filtro: a coleta ainda não rodou);
   erro da API mostrado no lugar da lista, e `error.tsx` para qualquer outra falha.
5. **Testes com Vitest + Testing Library** (`npm test`, roda no CI): funções de
   `lib/` e os componentes, inclusive o `ListaVagas` (async) com uma busca falsa.

## Consequências

- Sem JavaScript, a lista e a paginação continuam funcionando (vêm prontas do
  servidor); só o botão Buscar depende do JS.
- Quando houver login (#18/#19), o token pode ficar num cookie lido no servidor, no
  mesmo lugar (`lib/api.ts`).
- O E2E com Playwright (#21) cobre o fluxo pela URL.

## Alternativas consideradas

- **Buscar no navegador (`useEffect`/SWR) com CORS na API:** mais familiar, mas exige
  CORS, expõe a URL da API e mostra a lista só depois do JavaScript carregar.
- **`rewrites` do Next como proxy de `/api`:** resolve o CORS, mas continua com a
  busca no navegador e o estado duplicado entre URL e componente.
