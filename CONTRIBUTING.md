# Como contribuir

Este guia vale para os três integrantes e para quem quiser contribuir depois.
Ninguém faz push direto na `main`: toda mudança entra por Pull Request revisado.

## Fluxo de uma issue, do começo ao fim

1. **Pegue a issue** no board (coluna "Sprint atual") e mova para "Em andamento".
   No máximo 2 issues por pessoa em andamento.
2. **Atualize a `main` e crie a branch** (um comando por vez no PowerShell):

```powershell
git checkout main
```

```powershell
git pull --prune
```

```powershell
git checkout -b feat/8-coletor-fonte-a
```

3. **Commite** em pedaços pequenos, seguindo o padrão abaixo.
4. **Abra o PR** com o título em Conventional Commits e `Closes #8` na descrição.
   O template já traz o checklist.
5. **Peça revisão** para a pessoa do rodízio (abaixo) e mova a issue para "Em revisão".
6. **Depois da aprovação e do CI verde**, faça *Squash and merge*. A branch é
   apagada automaticamente. Volte para a `main`:

```powershell
git checkout main
```

```powershell
git pull --prune
```

## Nome da branch

`tipo/numero-descricao-curta`, com o número da issue:

| Exemplo | Quando |
|---|---|
| `feat/8-coletor-fonte-a` | funcionalidade nova |
| `fix/31-dedup-url-com-barra` | correção de bug |
| `docs/12-readme-contributing` | só documentação |
| `chore/1-monorepo-docker` | infra, configuração, dependências |
| `test/14-contrato-coletores` | só testes |
| `ci/2-workflows` | GitHub Actions |
| `spike/5-fontes-coleta` | pesquisa que termina num ADR |

## Mensagens de commit (Conventional Commits)

Formato: `tipo(area): descrição no imperativo, em minúsculas`.

```
feat(coletores): adiciona coletor do Greenhouse
fix(dedup): ignora barra final na url canônica
docs: explica como rodar os testes no Windows
test(matching): cobre palavra-chave com acento
chore(infra): sobe o postgres para a versão 17
```

- **Tipos:** `feat`, `fix`, `docs`, `test`, `chore`, `ci`, `refactor`, `spike`
- **Áreas:** `api`, `front`, `db`, `worker`, `coletores`, `dados`, `matching`,
  `notificacoes`, `auth`, `infra`
- O título do PR segue o mesmo formato. Como o merge é *squash*, **o título do PR
  vira o commit na `main`**: é ele que precisa estar bem escrito.

## Pull Requests

- Pequeno: idealmente menos de 400 linhas alteradas. PR grande não é revisado de
  verdade, é aprovado no cansaço. Se crescer, quebre em dois.
- Um assunto por PR. Achou outra coisa para arrumar? Abra uma issue.
- Mexeu no front? Coloque print ou GIF no PR.

### Rodízio de revisão

| Autor do PR | Revisor |
|---|---|
| Vinicius | João |
| Lucas | Vinicius |
| João | Lucas |

Quando o PR mexe na área de outra pessoa (coleta, infra ou notificações), o dono da
área entra como segundo revisor.

**Como revisar:** rode o código na sua máquina, leia os testes primeiro e prefira
perguntas a ordens ("o que acontece se a cidade vier vazia?"). Aprovar sem rodar
não vale.

## Definition of Done

Uma issue só vai para "Feito" quando:

1. Os critérios de aceite estão marcados.
2. O CI está verde e o PR tem pelo menos 1 aprovação.
3. A lógica nova tem teste (regra de negócio: unitário; endpoint: `TestClient`;
   banco: integração).
4. Nenhum segredo ou token foi commitado.
5. README ou `.env.example` foram atualizados se a forma de rodar mudou.
6. Está na `main` e funciona com `make up`.

## Antes do primeiro commit: pre-commit

O pre-commit roda o ruff (lint e formatação) e outras checagens em todo `git commit`,
antes do CI. Instale uma vez por máquina, dentro da pasta do repositório:

```powershell
pip install pre-commit
```

```powershell
pre-commit install
```

Se um hook corrigir arquivos, o commit é interrompido: confira as mudanças, rode
`git add` de novo e repita o commit.

## Regras de código

- Siga a estrutura de pastas: regra de negócio em `services/` (funções puras, sem
  banco e sem rede), queries em `repositories/`, rotas em `api/routes/`.
- Coletores sempre usam o cliente `coletores/http.py` e têm fixture em
  `backend/tests/fixtures/`. Nenhum teste acessa a internet.
- Configuração vem de `app/config.py`. Nunca leia `os.environ` direto nem escreva
  token no código.
- Decisão difícil de desfazer (trocar biblioteca, mudar arquitetura) vira um ADR em
  `docs/adr/`, no mesmo formato dos que já existem.

## Travou?

Travado há mais de 2 horas: peça ajuda no grupo. Isso é sinal de maturidade, não
de fraqueza.
