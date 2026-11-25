---
numero: 22
titulo: "feat(perfis): modelo e API de perfil"
responsavel: lucas
labels: feat, backend
pontos: 2
sprint: Sprint 2
---
## O que fazer
- Model `Perfil` (1 por usuário): área, palavras-chave (lista), cidade, aceita remoto, tipo, ativo
- `GET /perfil` e `PUT /perfil` do usuário logado

## Critérios de aceite
- [ ] Usuário só lê e altera o próprio perfil (teste)
- [ ] Máximo de 10 palavras-chave, cada uma com até 40 caracteres

## Dependências
Depende da assinatura de `get_usuario_atual` (#18).
