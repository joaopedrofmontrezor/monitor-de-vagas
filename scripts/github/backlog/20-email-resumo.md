---
numero: 20
titulo: "feat(notificacoes): e-mail de resumo diário"
responsavel: vinicius
labels: feat, notificacoes, infra
pontos: 2
sprint: Sprint 2
---
## O que fazer
- Mailpit no `docker-compose.yml` para ver os e-mails localmente
- `notificacoes/email.py` via SMTP
- Job diário no worker com as vagas compatíveis das últimas 24 h (lidas de `alertas_enviados`)

## Critérios de aceite
- [ ] Usuário sem vaga nova no dia não recebe e-mail
- [ ] Teste com SMTP falso

## Dependências
Depende de #24.
