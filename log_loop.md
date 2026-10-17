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

_(preenchido ao longo da execução)_
