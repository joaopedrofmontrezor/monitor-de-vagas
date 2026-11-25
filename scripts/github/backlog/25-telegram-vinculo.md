---
numero: 25
titulo: "feat(notificacoes): vínculo do Telegram pelo /start"
responsavel: lucas
labels: feat, notificacoes, backend
pontos: 2
sprint: Sprint 2
---
## O que fazer
- O site gera um código de 6 dígitos que expira em 10 minutos
- O usuário manda `/start 123456` para o bot
- O worker lê as mensagens com `getUpdates` (polling: mais simples que webhook e não exige URL pública) e salva o `chat_id` no usuário

## Critérios de aceite
- [ ] Código expirado ou inválido gera resposta clara no bot
- [ ] Testes do fluxo com o cliente Telegram mockado

## Dependências
Depende de #11 e #18.
