# ADR-0004: Worker separado com APScheduler e pipeline de coleta

- **Status:** aceito
- **Data:** 30/11/2026
- **Autor:** Vinicius (issue #4)

## Contexto

A coleta tem que rodar sozinha, em intervalos (mínimo de 6 h por fonte, ADR-0003),
e cada rodada precisa deixar rastro: quantas vagas vieram, quantas eram novas e se
deu erro. A API (FastAPI) roda com uvicorn e pode ter vários workers; um agendador
dentro dela rodaria a coleta uma vez **por worker do uvicorn**, duplicando
requisições às fontes e furando o rate limit.

## Decisão

1. **Processo `worker` separado da API** (`python -m app.worker.scheduler`, serviço
   `worker` do compose). Ele usa o `BlockingScheduler` do APScheduler 3 e cria **um
   job por coletor** do `registro_padrao()`, com `max_instances=1` (uma coleta não
   começa antes da anterior terminar) e `coalesce=True` (atrasos acumulados viram
   uma execução só).
2. **Intervalo:** cada coletor declara `intervalo_horas`. A variável
   `COLETA_INTERVALO_HORAS` sobrescreve o intervalo de todos; valor abaixo de 6 é
   recusado na hora de subir o worker.
3. **Reinício não fura o intervalo.** Ao subir, o worker lê o `inicio` da última
   linha de `execucoes_coleta` de cada coletor e agenda a próxima para
   `última + intervalo` (ou agora, se nunca rodou ou se já passou). Assim, um
   `docker compose restart` não dispara uma coleta nova a cada vez.
4. **Pipeline em `app/services/pipeline.py`**, uma função por etapa:
   - `para_vaga()` converte `VagaColetada` → `Vaga`: `limpar_titulo`,
     `normalizar_cidade`, `limpar_html` na descrição, `detectar_remoto` (cidade e
     título, somado ao que o coletor já informou), `url_canonica` e
     `chave_conteudo` calculadas **com os valores já normalizados**. Textos maiores
     que a coluna são cortados; vaga sem título depois da limpeza ou com URL acima
     de 2000 caracteres é descartada com aviso no log.
   - `executar_coletor()` grava a linha em `execucoes_coleta` **antes** de coletar
     (uma linha com `fim` vazio indica coleta travada ou worker que caiu no meio),
     chama o coletor, salva com `VagaRepository.salvar_novas()` e completa a linha
     com `fim`, `total_coletadas`, `novas`, `duplicadas` e `erro`.
   - `executar_todos()` roda os coletores um depois do outro, cada um com a sua
     sessão. **Falha de um coletor não derruba os outros**: a exceção é registrada
     em `execucoes_coleta.erro` (`Tipo: mensagem`, até 2000 caracteres) e no log.
5. **Coleta parcial.** Um coletor com várias origens (as empresas do Greenhouse)
   não deve perder tudo porque uma delas deu 404. Para isso existe
   `ColetaParcial(vagas, erros)` em `app/coletores/base.py`: o coletor levanta essa
   exceção com o que conseguiu, o pipeline grava as vagas e junta os erros em
   `execucoes_coleta.erro`. O Protocol `Coletor` não mudou.
6. **Transação:** o repositório não commita (#3); quem commita é o pipeline. Se o
   banco recusar o lote (ex.: valor maior que a coluna), o lote é desfeito e a
   execução fica registrada com o erro.
7. **`make coletar`** (`python -m app.worker.coletar [nomes...]`) roda o mesmo
   pipeline uma vez, na hora, e imprime o resumo. Sai com código 1 se algum coletor
   teve erro e 2 se o nome não existe. Ele **não** respeita o intervalo: é a
   ferramenta de quem está desenvolvendo, e o cache em disco do `ClienteHttp` evita
   repetir requisições dentro de 1 h.

## Consequências

- `ids_novos` sai do pipeline em `ResultadoColeta`: é a entrada do matching e dos
  alertas (#24), que vão rodar logo depois de cada coleta.
- As migrations continuam manuais (`make migrate`). Se o worker subir antes delas,
  ele avisa no log e as execuções falham com erro registrado até as tabelas
  existirem.
- Um worker só. Com mais de um, o mesmo job rodaria em dobro; aí a saída é um
  job store compartilhado ou Celery + Redis (fora do MVP).

## Alternativas consideradas

- **Agendador dentro da API (evento de startup do FastAPI):** um processo a menos,
  mas duplica a coleta com vários workers do uvicorn e mistura falha de coleta com
  a disponibilidade da API.
- **Cron do sistema ou GitHub Actions agendado:** simples, mas fora do compose e
  difícil de testar localmente; no Actions o banco nem é alcançável.
- **Celery + Redis:** é o caminho para escalar, mas traz mais dois serviços para um
  MVP com 2 fontes e uma coleta a cada 6 h.
- **APScheduler 4:** a API muda toda e ainda não é estável; ficamos no 3.x
  (`apscheduler>=3.11,<4`).
