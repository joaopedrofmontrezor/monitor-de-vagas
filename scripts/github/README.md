# Importação do backlog para o GitHub

Cria no repositório as labels, as milestones (Sprint 1 e Sprint 2) e as 25 issues do MVP,
a partir dos arquivos em `backlog/`. Cada issue é um `.md` com um cabeçalho simples
(número, título, responsável, labels, pontos, sprint) e o corpo em markdown.

## Passo a passo (uma pessoa faz, uma vez)

1. **Crie uma organização gratuita no GitHub** (ex.: `monitor-de-vagas`) e convide os outros
   dois como *Owner*. O projeto fica "do time", e mesmo assim os commits contam no perfil
   de cada um.
2. **Crie o repositório público e vazio** (sem README, .gitignore nem licença). Precisa ser
   público: no plano gratuito, a proteção de branch só funciona em repositório público.
3. **Primeiro commit direto na `main`** com estes arquivos (`.github/` e `scripts/`). É a
   única exceção à regra de "sem push na main", porque a proteção ainda não existe.
4. **Autentique o `gh`:**
   ```bash
   gh auth login
   gh auth refresh -s project   # só se for usar --projeto
   ```
   O importador usa só a API REST do GitHub (`gh api`). Apenas o `--projeto` depende da
   API GraphQL e do escopo `project`.
5. **Crie o board** em *Organização → Projects → New project → Board* e anote o número
   dele (aparece na URL: `.../projects/1`).
6. **Teste sem alterar nada:**
   ```bash
   python scripts/github/importar_backlog.py --repo monitor-de-vagas/monitor-de-vagas --dry-run
   ```
7. **Importe de verdade:**
   ```bash
   python scripts/github/importar_backlog.py --repo monitor-de-vagas/monitor-de-vagas \
     --responsavel joao=USUARIO_DO_JOAO \
     --responsavel vinicius=USUARIO_DO_VINICIUS \
     --responsavel lucas=USUARIO_DO_LUCAS \
     --projeto monitor-de-vagas/1
   ```
8. A proteção da `main` (1 aprovação + CI verde) é ligada pelo Vinicius na issue #2, depois que
   os workflows existirem. Antes disso, não há check de CI para exigir.

## Por que a numeração importa

Os textos das issues citam outras pelo número ("Depende de #6"). Num repositório novo, o
GitHub numera issues e PRs na mesma sequência. Então **rode o script antes de abrir
qualquer issue ou PR**, assim os números batem de 1 a 25. Se não baterem, o script avisa.

## Rodar de novo é seguro

Labels são atualizadas; milestones e issues com o mesmo título são puladas.
Para adicionar uma issue nova ao backlog, crie `26-alguma-coisa.md` e rode outra vez.

## Testes

```bash
python -m pytest scripts/github/tests
```

Um dos testes confere que o backlog continua equilibrado: em cada sprint, a diferença de
pontos entre os três integrantes é no máximo 1.
