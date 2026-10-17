# log_loop.md — ciclos de melhoria

Cada ciclo segue o mesmo formato: hipótese, mudança, arquivos, métrica antes/depois,
verificação e decisão (ACEITO mantém; REJEITADO reverte). A linha de base só avança
com melhoria medida e suíte verde.

## Linha de base (fim do MVP)

- Suíte: 118 testes verdes.
- Endpoints: `/health`, `/validate/cpf`, `/validate/cnpj`, `/validate/cep`, `/validate/uf`.
- Frontend estático em `/`.
- ViaCEP: timeout 3 s, 3 tentativas, fallback para validação de formato.
- Sem cache, sem rate limiting, sem PIS/PASEP.

## Ciclos

### Ciclo 1 — PIS/PASEP

- **Hipótese:** adicionar PIS/PASEP aumenta a cobertura documental sem alterar o
  comportamento dos endpoints existentes.
- **Mudança:** validador local em `src/validators/pis.py`, endpoint `POST /validate/pis`,
  opção no frontend, testes e documentação.
- **Métrica:** suíte verde antes **118 testes** → depois **131 testes**; o endpoint aceita
  casos válidos e rejeita dígito errado, sequência repetida, tamanho errado e letras.
- **Verificação:** `python -m pytest` → `131 passed`.
- **Decisão:** **ACEITO** — nenhum endpoint anterior mudou de comportamento e o novo
  endpoint tem cobertura válida/inválida.

### Ciclo 2 — Cache do ViaCEP

- **Hipótese:** cachear respostas do ViaCEP reduz chamadas externas em consultas
  repetidas sem alterar o contrato da API.
- **Mudança:** cache em memória com TTL configurável em `src/services/viacep.py`,
  `clear_cache()` para testes e três testes de comportamento (reuso, TTL zero e falha).
- **Métrica:** consultas repetidas ao mesmo CEP: **2 chamadas HTTP antes** → **1 depois**;
  TTL `0` volta a fazer 2 chamadas e falha de rede não é cacheada.
- **Verificação:** `python -m pytest` → `134 passed` (131 → 134).
- **Decisão:** **ACEITO** — redução de chamadas externas sem mudar o corpo da resposta
  e sem cachear indisponibilidade.

### Ciclo 3 — Rate limiting

- **Hipótese:** limitar requisições por IP protege a API e a fonte externa sem
  prejudicar o uso normal.
- **Mudança:** middleware de janela deslizante em `src/middleware.py`, configuração por
  ambiente, resposta `429` com `Retry-After` e quatro testes. A chave do limite é o
  SHA-256 do IP, para não manter o endereço em claro na memória.
- **Métrica:** com limite 3 e janela 60 s, quatro requisições resultam em
  **[200, 200, 200, 429]**; com `RATE_LIMIT_ENABLED=0`, cinco requisições resultam em
  **5×200**; `/health` permanece `200` mesmo com limite 1; após a janela, o acesso é
  liberado novamente.
- **Verificação:** `python -m pytest` → `138 passed` (134 → 138).
- **Decisão:** **ACEITO** — limite é respeitado, desligável por ambiente e não afeta
  saúde nem frontend.

## Resultado final

- Suíte: **139 testes verdes** (inclui o teste do limite do cache).
- Endpoints: `/health`, `/validate/cpf`, `/validate/cnpj`, `/validate/cep`, `/validate/uf`,
  `/validate/pis`.
- Cache do ViaCEP e rate limiting ativos por padrão e configuráveis por ambiente.
- Classificação do README reavaliada: **usável** (testes verdes, README completo, push feito).
