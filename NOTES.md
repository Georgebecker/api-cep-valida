# NOTES — decisões, problemas e pendências

Registro das decisões não triviais do projeto. Cada escolha tem motivo; ideias fora
do escopo ficam na seção de ideias futuras e não são implementadas no MVP.

## Contrato e escopo

- **Contrato v3.0 recebido em 2026-10-17.** O texto termina em "O relatório final deve
  seguir exatamente este formato:" sem o formato. Decisão conservadora: manter um
  relatório estruturado com status, checklist item a item, entregáveis, evidências de
  teste, ciclos de loop, bloqueios e links. Registrado aqui conforme R10.
- **Base existente preservada.** O repositório já continha a base do Loop Engineering
  (`meu-loop-agente/`, `.githooks/`, `docs/`). A entrega adiciona `src/`, `tests/` e
  `frontend/` sem remover a base; o README passa a descrever a API.

## Stack e versões

- **Versões exatas** em `requirements.txt`, conforme a política para evitar conflito:
  fastapi 0.143.3, pydantic 2.14.1, uvicorn 0.54.0, requests 2.34.2, tenacity 9.2.1,
  pytest 9.1.1, httpx 0.28.1.
- **Python local 3.14.6; Docker em 3.13-slim.** O contrato exige 3.11+; o código usa
  apenas sintaxe compatível com 3.11 (`str | None`, `list[...]`). A imagem 3.13 foi
  escolhida por ter wheels estáveis das dependências no momento da entrega.
- **HTTPX** é usado apenas pelo `TestClient` do FastAPI; está fixado porque a suíte
  depende dele.

## Contrato da API

- **Corpo único `{"value": "..."}`** em todos os endpoints de validação, em vez de um
  campo por documento. Reduz duplicação de schema e simplifica o frontend.
- **`extra="forbid"` e limites 1..32** no schema de entrada: entrada vazia, campo
  desconhecido, tipo errado ou valor longo retornam `422`, sem chegar ao validador.
- **Respostas sempre modeladas** (`ValidationResponse`, `CepResponse`, `Address`),
  nunca dicionários soltos, para garantir o contrato declarado no OpenAPI.
- **Status HTTP 200 para documento inválido**: o pedido foi processado e a resposta é
  `valid: false`. `422` fica reservado para entrada malformada.
- **CORS liberado** (`allow_origins=["*"]`) no MVP para o frontend estático funcionar
  aberto por `file://` ou por outra porta. Sem autenticação, não há credencial exposta.
- **Frontend montado em `/`** via `StaticFiles`, somente se a pasta existir. As rotas
  da API são declaradas antes, então não são capturadas pelo mount.

## Algoritmos e normalização

- **CPF e CNPJ** seguem os algoritmos oficiais da Receita Federal, com rejeição de
  sequências repetidas e validação dos dois dígitos verificadores.
- **Normalização restrita**: apenas `.`, `-`, `/` e espaço são removidos. Letras e
  outros símbolos são rejeitados, em vez de descartados silenciosamente.
- **UF**: comparação após `strip()` e `upper()`; a lista tem exatamente 27 siglas,
  incluindo DF.
- **CEP `00000000` é inválido**; os demais oito dígitos são aceitos no formato
  `NNNNN-NNN`.

## ViaCEP (fonte externa única)

- **Timeout de 3 s por tentativa, 3 tentativas, backoff exponencial** (0,15 s até 1 s),
  configuráveis por `VIA_CEP_BASE_URL` e `VIA_CEP_TIMEOUT`.
- **Falha de rede nunca vira 5xx**: `lookup_cep` retorna `unavailable` e o endpoint
  responde com `valid` calculado pelo formato, `source: "local"` e `address: null`.
- **`{"erro": true}` do ViaCEP** vira `not_found` e o endpoint responde `valid: false`
  com `source: "viacep"`.
- **Resposta JSON inesperada** (lista, texto) é tratada como indisponibilidade.
- **Testes não dependem de rede**: `requests.get` é substituído por mocks em todos os
  cenários (sucesso, não encontrado, queda e resposta inesperada).

## Qualidade e verificação

- **`pytest.ini` com `pythonpath = .`** desde o primeiro commit, evitando falha de
  descoberta do pacote `src`.
- **Encoding UTF-8 explícito** na leitura do README no teste de classificação.
- **Teste da classificação** valida a seção `## Classificação`, os quatro campos
  preenchidos, a maturidade declarada e os entregáveis quando a maturidade é `usável`.

## Loop de melhoria

- **Ciclo 1 (ACEITO): PIS/PASEP.** Algoritmo oficial com pesos
  `3,2,9,8,7,6,5,4,3,2`; dígito calculado como `11 - (soma % 11)` e convertido para `0`
  quando o resultado é 10 ou 11. Rejeita sequências repetidas. Endpoint `/validate/pis`.
- **Ciclo 2 (ACEITO): cache do ViaCEP.** Cache em memória com TTL de 300 s
  (`VIA_CEP_CACHE_TTL`), limite de 1024 entradas e `Lock` para acesso concorrente.
  Apenas respostas `found` e `not_found` são cacheadas; `unavailable` não é, para não
  prolongar uma indisponibilidade. Métrica: duas consultas iguais passam de 2 para 1
  chamada HTTP.
- **Ciclo 3 (ACEITO): rate limiting.** Janela deslizante em `src/middleware.py` aplicada
  a `/validate/*`, com padrão de 60 requisições por 60 s por IP. Escolhas: usa
  `request.client.host` (não confia em `X-Forwarded-For` sem proxy confiável), `/health`
  fica isento, o estado é por processo e `reset()` existe para testes.

## Ideias futuras (não implementadas no MVP)

- Consulta de CEP em lote.
- Suporte a PIS/PASEP — implementado no loop de melhoria.
- Cache de respostas do ViaCEP — implementado no loop de melhoria.
- Rate limiting — implementado no loop de melhoria.
- Autenticação por chave de API para uso público.
- Métricas Prometheus e tracing.

## Pendências

- Nenhuma pendência funcional conhecida ao fim do MVP.
- Publicação no GitHub depende de autenticação da CLI `gh` (verificada antes do push).
