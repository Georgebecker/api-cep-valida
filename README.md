# API CEP Valida

API REST em Python para validar documentos brasileiros — CPF, CNPJ, CEP e UF — com
algoritmos oficiais, frontend estático de teste e consulta de endereço no ViaCEP.
A API não persiste documentos pessoais, não usa banco de dados e não depende de serviço pago.

## Classificação

- **Propósito:** oferecer validação confiável, rápida e sem armazenamento de CPF, CNPJ, CEP, UF e PIS/PASEP, tanto por HTTP/JSON quanto por uma página estática de teste.
- **Maturidade:** usável
- **O que está sendo treinado:** o processo de Loop Engineering (hipótese → mudança pequena → teste → medição → decisão ACEITO/REJEITADO) aplicado à própria API; não há treinamento de modelo de machine learning.
- **Quem usaria:** desenvolvedores e times que precisam validar documentos antes de persistir cadastros, como equipes de backoffice, ERPs, formulários públicos e integrações internas.

---

**Autor:** George Herman Becker
**Gestão em Tecnologia da Informação**


**Apoie o autor:**
- **PIX:** `a8b68e14-edfe-4450-88f2-c2af4aca2a6c`
- **Buy Me a Coffee:** <https://buymeacoffee.com/georgehbecker>
- **LinkedIn:** <https://www.linkedin.com/in/georgehbecker/>

---

## Método: Loop Engineering

O projeto nasceu da base [`meu-loop-agente/`](meu-loop-agente/) e mantém o ciclo de
melhoria: cada mudança pós-MVP tem hipótese, métrica, decisão e registro. Os três
ciclos executados (PIS/PASEP, cache do ViaCEP e rate limiting) estão em
[`log_loop.md`](log_loop.md).

---

## Endpoints

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/health` | Saúde do serviço |
| POST | `/validate/cpf` | Valida CPF (algoritmo oficial) |
| POST | `/validate/cnpj` | Valida CNPJ (algoritmo oficial) |
| POST | `/validate/cep` | Valida formato e consulta o ViaCEP |
| POST | `/validate/uf` | Valida uma das 27 siglas de UF |
| POST | `/validate/pis` | Valida PIS/PASEP (algoritmo oficial) |
| GET | `/` | Frontend estático de teste |

O corpo dos endpoints de validação é sempre `{"value": "<documento>"}`. Campos extras,
valores vazios ou com mais de 32 caracteres recebem `422`.

### Exemplos

```bash
curl -s -X POST http://127.0.0.1:8000/validate/cpf \
  -H "Content-Type: application/json" \
  -d '{"value": "529.982.247-25"}'
```

```json
{"valid": true, "document": "cpf", "normalized": "52998224725", "message": "CPF válido"}
```

```bash
curl -s -X POST http://127.0.0.1:8000/validate/cep \
  -H "Content-Type: application/json" \
  -d '{"value": "01001-000"}'
```

```json
{
  "valid": true,
  "document": "cep",
  "normalized": "01001-000",
  "message": "CEP válido e encontrado no ViaCEP",
  "source": "viacep",
  "address": {"cep": "01001-000", "street": "Praça da Sé", "city": "São Paulo", "state": "SP"}
}
```

Se o ViaCEP estiver indisponível, o CEP continua validado pelo formato e a resposta traz
`"source": "local"` e `"address": null`, sem erro 5xx. Se o ViaCEP responder que o CEP
não existe, a resposta é `"valid": false` com `"source": "viacep"`.

## Regras de validação

- **CPF:** 11 dígitos, rejeita sequência repetida, valida os dois dígitos verificadores; aceita `.` e `-`.
- **CNPJ:** 14 dígitos, rejeita sequência repetida, valida os dois dígitos verificadores; aceita `.`, `/` e `-`.
- **CEP:** 8 dígitos no padrão `NNNNN-NNN`, rejeita `00000-000`; consulta o ViaCEP com timeout de 3 s, até 3 tentativas e cache em memória de 5 minutos.
- **UF:** uma das 27 siglas oficiais, sem diferenciar maiúsculas de minúsculas.
- **PIS/PASEP:** 11 dígitos, rejeita sequência repetida e confere o dígito verificador pelos pesos oficiais.
- Entradas com letras ou símbolos fora dos separadores usuais são rejeitadas, não limpas silenciosamente.

## Estrutura do projeto

```
api-cep-valida/
├── src/
│   ├── main.py              # aplicação FastAPI e rotas
│   ├── schemas.py           # modelos Pydantic de entrada e saída
│   ├── middleware.py        # rate limiting por cliente
│   ├── services/viacep.py   # consulta externa com retry e fallback
│   └── validators/          # CPF, CNPJ, CEP, UF e PIS/PASEP
├── tests/                   # suíte pytest (inclui teste da classificação)
├── frontend/                # página estática de teste
├── requirements.txt         # versões exatas
├── docker-compose.yml       # execução em container
├── pytest.ini               # pythonpath = .
├── Dockerfile
├── NOTES.md                 # decisões e pendências
├── log_loop.md              # ciclos de melhoria
└── LICENSE                  # MIT
```

## Como rodar

Requisitos: **Python 3.11+** e Git. Docker é opcional.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.main:app --reload
```

- API: <http://127.0.0.1:8000> (documentação interativa em `/docs`)
- Frontend: <http://127.0.0.1:8000/>
- Testes: `python -m pytest`

## Frontend

A página em `/` é estática, sem build e sem dependências de frontend. Ela oferece abas
para CPF, CNPJ, CEP, UF e PIS/PASEP, indicador de status da API, exemplos clicáveis,
resultado detalhado (fonte, endereço e tempo de resposta) e histórico apenas em memória na
página, apagado ao recarregar. Nada do histórico é enviado para a API.

## Docker

```bash
docker build -t api-cep-valida .
docker run --rm -p 8000:8000 api-cep-valida
```

Ou com Docker Compose:

```bash
docker compose up --build
```

A interface fica em <http://127.0.0.1:8000/> e a documentação interativa em `/docs`.

## Configuração

| Variável | Padrão | Uso |
| --- | --- | --- |
| `VIA_CEP_BASE_URL` | `https://viacep.com.br/ws` | Base da API do ViaCEP |
| `VIA_CEP_TIMEOUT` | `3` | Timeout em segundos por tentativa |
| `VIA_CEP_CACHE_TTL` | `300` | Tempo de vida do cache de CEP, em segundos (`0` desativa) |
| `RATE_LIMIT_ENABLED` | `1` | Liga/desliga o limite (`0` desativa) |
| `RATE_LIMIT_REQUESTS` | `60` | Requisições permitidas por janela e por cliente |
| `RATE_LIMIT_WINDOW` | `60` | Tamanho da janela em segundos |

### Limites de uso

As rotas `/validate/*` aceitam, por cliente, **60 requisições por minuto** (janela deslizante).
A chave do limite é o SHA-256 do IP, não o IP em claro. Ao exceder, a API responde `429` com
o cabeçalho `Retry-After`. O `/health` e os arquivos estáticos não são limitados. O contador
fica em memória de cada processo — reiniciar o servidor zera o histórico e múltiplas
instâncias não compartilham o limite.

Nenhuma chave ou segredo é necessária. O `.env` é local e não versionado; veja `.env.example`.
As variáveis são lidas do ambiente do processo: o `.env.example` documenta os nomes e, se você
usar um `.env`, carregue-o no shell/IDE (o projeto não depende de `python-dotenv`).

## Segurança e privacidade

- A API não persiste CPF, CNPJ, CEP, UF ou PIS/PASEP; não há banco de dados.
- CPF, CNPJ, UF e PIS/PASEP são validados localmente e nunca saem do servidor; somente o CEP é enviado ao ViaCEP.
- O frontend mantém o histórico apenas em memória; recarregar a página apaga tudo.
- O rate limiting guarda apenas o SHA-256 do IP, em memória, durante a janela configurada.
- `.env` é ignorado pelo git e os hooks bloqueiam commit/push de segredo; nenhuma chave é usada.
- Entradas são limitadas a 32 caracteres e validadas por schema; não há SQL, shell ou avaliação dinâmica.
- Para exposição pública ainda faltam: HTTPS (proxy reverso), CORS restrito ao domínio do frontend,
  limite de tamanho de corpo e, se necessário, autenticação/quotas por cliente. O MVP local roda em HTTP.

## Decisões e limitações

- Sem banco de dados, autenticação ou armazenamento de dados pessoais.
- CORS liberado no MVP para permitir o frontend estático.
- PIS/PASEP, cache do ViaCEP e rate limiting foram aceitos nos ciclos 1, 2 e 3, com
  decisão registrada em [`log_loop.md`](log_loop.md).
- O rate limiting vive em memória por processo: múltiplas instâncias não compartilham o
  contador e um proxy reverso deve ser configurado para preservar o IP do cliente.
- Decisões de implementação, versões e ideias futuras estão em [`NOTES.md`](NOTES.md).

## Licença

MIT — veja [`LICENSE`](LICENSE).