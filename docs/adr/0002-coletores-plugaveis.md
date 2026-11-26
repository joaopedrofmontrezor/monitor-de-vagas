# ADR-0002: Coletores plugáveis com um cliente HTTP compartilhado

- **Status:** aceito
- **Data:** 30/11/2026
- **Autor:** João Pedro (issue #6)

## Contexto

O MVP começa com 2 fontes (Greenhouse e repositórios do GitHub, ADR-0003) e o
plano é crescer: Lever, Nube, editais. Cada fonte tem formato próprio, mas o resto
do sistema (normalização, dedup, banco, matching, alertas) não pode depender disso.
Também precisamos garantir que todo coletor siga as regras de scraping responsável
sem que cada um reimplemente rate limit, retry e User-Agent.

## Decisão

1. **Contrato único em `app/coletores/base.py`.** Todo coletor cumpre o Protocol
   `Coletor`: atributos `nome` e `intervalo_horas` e o método
   `coletar() -> list[VagaColetada]`.
2. **`VagaColetada` é um dataclass imutável, não o model do banco.** O coletor não
   conhece SQLAlchemy, sessão nem transação; o teste dele roda sem Postgres. A
   conversão para o model `Vaga` acontece uma vez só, no pipeline (#4). O próprio
   dataclass recusa vaga sem URL, sem título ou com `tipo` fora de `estagio`/`edital`,
   para o erro aparecer no coletor que errou, e não lá no banco.
3. **Registro explícito em `app/coletores/registry.py`.** `RegistroColetores` guarda
   os coletores por nome e valida na entrada: nome em `snake_case`, sem repetição e
   `intervalo_horas` de no mínimo 6 (regra do ADR-0003). A função `registro_padrao()`
   monta o registro com os coletores reais; o worker (#4) cria um job para cada um.
   Coletor novo = uma classe + uma linha em `registro_padrao()` (#8 e #13).
   Os testes criam o próprio `RegistroColetores()` com coletores falsos.
4. **Cliente HTTP compartilhado em `app/coletores/http.py`.** Nenhum coletor usa
   `httpx` direto. O `ClienteHttp` já traz:
   - User-Agent `MonitorDeVagas/0.1 (+https://github.com/joaopedrofmontrezor/monitor-de-vagas)`;
   - timeout de 15 s;
   - no máximo 1 requisição a cada 2 s **por domínio** (domínios diferentes não esperam);
   - retry em falha de rede, 429 e 5xx, com espera exponencial (1 s, 2 s...) ou o
     `Retry-After` do servidor; desiste se o servidor pedir mais de 60 s;
   - erro 4xx (exceto 429) falha na hora, sem insistir;
   - cache simples em disco (opcional, `pasta_cache`), válido por 1 hora, só de
     respostas 200. Serve para não repetir chamadas quando alguém roda `make coletar`
     várias vezes seguidas enquanto desenvolve.
   Relógio e `sleep` são injetáveis: os testes usam um relógio falso e
   `httpx.MockTransport`, então rodam em milissegundos e sem rede.

## Consequências

- Adicionar fonte não mexe em pipeline, banco nem API.
- O teste de contrato (#14) pode percorrer o `registro_padrao()` e validar todo
  coletor do mesmo jeito.
- O rate limit vale por instância do `ClienteHttp`. Como o worker é um processo só
  (ADR-0004), basta cada coletor usar o seu cliente. Se um dia houver vários workers
  (Celery), o limite terá que ir para um lugar compartilhado (Redis).
- O cache em disco não tem limpeza automática; os arquivos ficam em `.cache/http/`
  (no `.gitignore`). Apagar a pasta é seguro.

## Alternativas consideradas

- **Classe base abstrata (`ABC`) em vez de Protocol:** obrigaria herança. Com Protocol,
  qualquer objeto com `nome`, `intervalo_horas` e `coletar()` serve, inclusive os
  falsos dos testes.
- **Descoberta automática de coletores (importar todo módulo da pasta):** menos uma
  linha por coletor, mas esconde o que está ativo e cria efeito colateral no import.
  Para 2 ou 3 fontes, a lista explícita é mais fácil de entender e de desligar.
- **`hishel`/`requests-cache` para o cache:** mais completos, mas são mais uma
  dependência para um cache de desenvolvimento. Fica como próximo passo se o cache
  precisar respeitar `Cache-Control`.
