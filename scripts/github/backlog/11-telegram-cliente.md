---
numero: 11
titulo: "feat(notificacoes): cliente de envio do Telegram"
responsavel: lucas
labels: feat, notificacoes, backend
pontos: 2
sprint: Sprint 1
---
## O que fazer
- Criar o bot no BotFather (token só no `.env`, nunca no código)
- `notificacoes/telegram.py` com `enviar(chat_id, texto)`
- Formato da mensagem de vaga: título, empresa, cidade/remoto, link

## Critérios de aceite
- [ ] Teste com `httpx.MockTransport` validando a chamada e o formato
- [ ] Erro 429 (limite do Telegram) tratado com nova tentativa

## Dependências
Depende de #1.
