---
numero: 24
titulo: "feat(matching): motor de matching e registro de alertas"
responsavel: lucas
labels: feat, backend, notificacoes, p0
pontos: 3
sprint: Sprint 2
---
## O que fazer
`services/matching.py` com a função pura `vaga_combina(vaga, perfil) -> bool`. A vaga combina quando:
- o tipo é igual; e
- a cidade é igual (normalizada) **ou** a vaga é remota e o perfil aceita remoto; e
- pelo menos uma palavra-chave aparece no título ou na descrição (sem acento, palavra inteira)

Integrar ao pipeline: vagas novas → perfis ativos → Telegram → `alertas_enviados` com `UNIQUE(usuario_id, vaga_id)`.

## Critérios de aceite
- [ ] Testes parametrizados com pelo menos 10 casos, incluindo "java" não casar com "javascript"
- [ ] Rodar o pipeline duas vezes não envia o mesmo alerta duas vezes
- [ ] Cobertura ≥ 80%

## Dependências
Depende de #4, #11 e #22.
