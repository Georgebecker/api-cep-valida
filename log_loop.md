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

_(ciclos 2 e 3 preenchidos ao longo da execução)_
