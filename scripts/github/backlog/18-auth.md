---
numero: 18
titulo: "feat(auth): cadastro, login e JWT"
responsavel: vinicius
labels: feat, backend, infra, p0
pontos: 3
sprint: Sprint 2
---
## Contexto
A #22 depende disto. Abrir primeiro um PR pequeno com o model `Usuario` e a assinatura de `get_usuario_atual` em `api/deps.py`, para o Lucas trabalhar em paralelo com `app.dependency_overrides`.

## O que fazer
- `POST /auth/cadastro`, `POST /auth/login`, `POST /auth/logout`
- Senha com hash (bcrypt ou argon2), JWT em cookie httpOnly
- `get_usuario_atual` em `api/deps.py`

## Critérios de aceite
- [ ] Testes: senha errada, e-mail repetido, rota protegida sem cookie retorna 401
- [ ] Senha nunca aparece em log nem em resposta

## Dependências
Depende de #3.
