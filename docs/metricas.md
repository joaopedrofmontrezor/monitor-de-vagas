# Métricas do Monitor de Vagas

Números medidos de verdade, para o README e para a apresentação. Cada linha diz
quando e como foi medida.

## Volume coletado

| Data | Fonte | Empresas/repos | Vagas no Brasil (lista) | Estágios gravados | Duração | Erros |
|---|---|---|---|---|---|---|
| 2026-11-27 | Greenhouse (#8) | 36 | não medido | 25 | 2 min 01 s | 0 |

Como medir (depois do `make coletar` no banco local):

```sql
SELECT inicio, total_coletadas, novas, duplicadas, fim - inicio AS duracao, erro
FROM execucoes_coleta WHERE coletor = 'greenhouse' ORDER BY id DESC LIMIT 1;
```

```sql
SELECT empresa, count(*) FROM vagas WHERE fonte = 'greenhouse' GROUP BY empresa ORDER BY 2 DESC;
```

### Primeira coleta real (27/11/2026, 11h26 de Brasília)

Feita pelo worker do João ao subir (`execucoes_coleta.id = 1`): as 36 empresas
responderam, nenhum token deu erro (nem `gympass`, nem `stone`) e 25 estágios no
Brasil foram gravados. Só 8 das 36 empresas tinham estágio aberto:

| Empresa | Estágios |
|---|---|
| Inter Carreiras | 5 |
| BTG Pactual | 5 |
| Wildlife Studios | 5 |
| BEES | 4 |
| SumUp | 2 |
| Brex | 2 |
| C6 Bank | 1 |
| XP Inc. | 1 |

Uma segunda coleta 17 minutos depois (`make coletar`) trouxe as mesmas 25 vagas:
0 novas e 25 duplicadas, em 2,6 s, porque o cache em disco de 1 h do `ClienteHttp`
evitou as requisições. A deduplicação e o cache funcionaram como previsto.

A coluna "Vagas no Brasil (lista)" fica como "não medido": o coletor só grava os
estágios que passam no filtro, não o total de vagas no Brasil de cada quadro.

## Observações

- O levantamento manual de 27/11 contou 40 "estágios" em 36 empresas, mas a conta
  pegava "Interna"/"Internos" (no BTG eram 9 estágios de verdade, não 11). O número
  oficial é o da tabela acima, com o filtro por palavra inteira do coletor.
- Estágio é sazonal: anote uma linha nova a cada medição em vez de sobrescrever.
- O nome da empresa vem do `company_name` da API quando ele existe; por isso aparece
  "Inter Carreiras" (nome do quadro) e não "Inter" (nome em `EMPRESAS_PADRAO`).
- 25 estágios é pouco para um painel com tendências: é o risco do ADR-0003. A fonte B
  (#13) e o acompanhamento ao longo dos dias vão dizer se precisa de mais fontes.
