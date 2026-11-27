# Métricas do Monitor de Vagas

Números medidos de verdade, para o README e para a apresentação. Cada linha diz
quando e como foi medida.

## Volume coletado

| Data | Fonte | Empresas/repos | Vagas no Brasil (lista) | Estágios gravados | Duração | Erros |
|---|---|---|---|---|---|---|
| AAAA-MM-DD | Greenhouse (#8) | 36 | preencher | preencher | preencher | preencher |

Como medir (depois do `make coletar` no banco local):

```sql
SELECT inicio, total_coletadas, novas, duplicadas, fim - inicio AS duracao, erro
FROM execucoes_coleta WHERE coletor = 'greenhouse' ORDER BY id DESC LIMIT 1;
```

```sql
SELECT empresa, count(*) FROM vagas WHERE fonte = 'greenhouse' GROUP BY empresa ORDER BY 2 DESC;
```

## Observações

- O levantamento manual de 27/11 contou 40 "estágios" em 36 empresas, mas a conta
  pegava "Interna"/"Internos" (no BTG eram 9 estágios de verdade, não 11). O número
  oficial é o da tabela acima, com o filtro por palavra inteira do coletor.
- Estágio é sazonal: anote uma linha nova a cada medição em vez de sobrescrever.
