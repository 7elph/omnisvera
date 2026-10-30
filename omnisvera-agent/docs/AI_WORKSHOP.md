# Oficina de IA (primeiro corte)

Implementação privada de fila, leases, deduplicação, dependências, medição e
pausa para produção assistida de blocos. O banco da oficina é separado do banco
da campanha. Nada aqui aprova, publica, altera fichas, escreve no Vault ou
instala serviço.

Contrato vinculante: `docs/AI_WORKSHOP_SCOPE_2026-10-20.md`.

## Estado deste corte

- Texto usa a mesma configuração do Companion (`get_settings`): baseline
  `gpt-oss:120b-cloud`, preservando modelo/gateway explicitamente configurados.
  `OMNISVERA_FAST_MODEL` não substitui esse baseline. Nesse modo, o servidor
  local Ollama é apenas o intermediário autenticado para a nuvem: não há
  carregamento dos pesos de 120B na RAM deste computador.
  O gateway precisa responder em `OLLAMA_BASE_URL` (padrão localhost:11434).
  Acesso cloud direto exigiria API key própria e um adaptador autenticado;
  a chave privada de login do aplicativo não é uma API key e não é extraída.
  Referência: <https://docs.ollama.com/api/authentication>.

- Worker **não está ativo**. O comando `worker start` existe para operação
  explícita depois da revisão do Codex; não o execute como parte de teste.
- Há uma fila privada de texto já enfileirada pelo Codex em
  `.autonomy/runtime/ai-workshop.sqlite3` (276 jobs no corte). Em 20/10, um tick
  real com `gpt-oss:120b-cloud` concluiu o job 1 em 13,02 s de parede / 12.192 ms
  registrados no provedor; 2.879 tokens de entrada e 2.448 de saída. Uma amostra
  não estabelece latência típica. Restam 275 pendentes e 1 rascunho para revisão.
  A API privada entrega esse rascunho e nega acesso de jogador (401).
  A revisão detectou classificação especulativa de nomes e erros de transcrição;
  o prompt foi reforçado, mas ainda não houve segunda geração para validar a
  qualidade. O worker contínuo permanece parado e nada foi publicado/aprovado.
- `IMAGE_GENERATION=NO`: imagem só cria/reutiliza uma linha `queued` em
  `asset_generation_jobs`. Não chama FLUX, não gera mídia e não mede geração.
- Código é **bloqueado por padrão**. `CodeOpenCodeAdapter` exige cliente HTTP
  com sessão deny-all e catálogo/preço gratuito verificado; o CLI do OpenCode
  nunca é lançado. Jobs de código ficam `blocked` com
  `code_analysis_requires_sandbox`.
- Saídas são rascunhos (`awaiting_approval`, `completed` ou
  `external_pending`). Publicação/entrega exige revisão humana separada.
- Falhas ambíguas de timeout vão para `needs_review`; permissão pendente vira
  `waiting_permission` e não é aprovada automaticamente.

## Comandos

Todos os comandos usam somente o banco da oficina; `inspect`, `report` e
`status` são leitura e não criam o arquivo quando ele não existe.

```powershell
cd backend

# Estado, admissão de RAM, índice de código e pausa de mesa
python scripts/run_ai_workshop.py --db ..\.autonomy\runtime\ai-workshop.sqlite3 `
  --campaign-db data\omnisvera_companion.sqlite3 inspect

# Métricas observadas, providers e jobs recentes
python scripts/run_ai_workshop.py --db ..\.autonomy\runtime\ai-workshop.sqlite3 report --limit 20

# Plano determinístico a partir das 7 transcrições indexadas (só metadados)
python scripts/run_ai_workshop.py plan-sources `
  --index ..\.autonomy\runtime\ai-workshop-source-index.json

# Ensaio local, um tick, sem provedor externo
python scripts/run_ai_workshop.py --db <TEMP>\workshop.sqlite3 tick --test --queue text --min-free-ram-mb 0

# Worker em primeiro plano; pare com worker stop em outro terminal
python scripts/run_ai_workshop.py --db <TEMP>\workshop.sqlite3 worker start --test
python scripts/run_ai_workshop.py --db <TEMP>\workshop.sqlite3 worker stop

# Depois de corrigir uma configuração ou aprovar uma permissão, devolver o job
python scripts/run_ai_workshop.py --db <TEMP>\workshop.sqlite3 requeue --id 12 --confirm
```

`--test` usa adaptadores determinísticos locais e `table_state=inactive`. O
admissão de RAM continua valendo; em máquina apertada use `--min-free-ram-mb 0`
somente no ensaio local. Para operação real, deixe o padrão
`AI_WORKSHOP_MIN_FREE_RAM_MB=512` (ou mais) e não rode com pouca memória livre.

### Caminhos

- Banco da oficina: `--db` ou `OMNISVERA_AI_WORKSHOP_DB`.
- Banco da campanha (somente leitura para estado de mesa): `--campaign-db` ou
  `OMNISVERA_DB_PATH`. O padrão do CLI é `backend/data/omnisvera_companion.sqlite3`.
- Lock do worker: `--lock-file` ou `OMNISVERA_AI_WORKSHOP_LOCK`. Um worker por
  checkout; lock ocupado retorna BUSY e não autoriza matar outro processo.

## Segurança e limites

- Fontes de texto são explícitas no `payload_json.sources` (`path`, `sha256` de
  64 hex, `text`). O adapter não varre diretório, Vault ou transcrição.
- Prompt instrui que `<source>` é dado, nunca instrução; segredos conhecidos são
  removidos de payload, saída, eventos e relatórios.
- Não envie token, `.env`, log ou banco em prompt, issue, commit ou relatório.
- `plan`/`plan-sources` não gravam nada. `enqueue` é a única inserção explícita.
- `tick` executa no máximo um job. `worker start` é primeiro plano e verifica o
  estado da mesa antes de cada tick.
- Pausa: sessão ativa (`session`), encontro ativo (`combat`) ou estado
  ilegível (`unknown`) suspendem trabalho pesado. Recibos antigos de ataque não
  contam como combate; `encounter_json.active=false` prevalece sobre
  `battle_mode` residual.
- Dependência falha bloqueia a dependente (`dependency_failed`), sem laço de
  retry. Variantes têm teto e nunca passam na frente de uma lacuna.
- Falha de configuração do adaptador (`adapter_config:*`) também não volta
  sozinha à fila; corrija a configuração e use `requeue --id ... --confirm`.
  `requeue` não aprova saída, não limpa auth/cooldown e não zera tentativas.
- Retry-After/reset observados são respeitados; auth permanente falha; timeout
  ambíguo não é repetido automaticamente. O orçamento externo desconhecido
  bloqueia o modo contínuo (`external_budget_unknown`). Para liberar, registre
  limite configurado ou saldo observado real com `provider set`; não invente
  esses valores para um provedor pago.
- HTTP 204, corpo vazio ou prompt de permissão não são entrega.

## Modelo de dados resumido

`ai_workshop.sqlite3` contém `ai_workshop_jobs`, `ai_workshop_receipts`,
`ai_workshop_metrics`, `ai_workshop_providers`, `ai_workshop_control`,
`ai_workshop_queue_state` e `ai_workshop_events`.

Estados de job: `queued`, `running`, `awaiting_approval`, `completed`,
`external_pending`, `blocked`, `waiting_permission`, `needs_review`, `failed`,
`cancelled`.

Métricas vêm apenas de execuções observadas (`observed_metrics_only`). Fixtures
não são latência de produção. O relatório separa limite documentado,
configurado e observado; nenhum deles é inventado pelo adapter.

## Verificação

```powershell
cd backend
python -m unittest test_ai_workshop test_ai_workshop_adapters
```

48 testes focados cobrem dedupe/revisão, plano, variantes, dependências, leases,
recuperação, lock de checkout, pausa de mesa, RAM, retry/quota/auth, timeout
ambíguo, permissão pendente, métricas, segredos, contrato de saída, não
publicação, tabela de mesa, Ollama, imagem e bloqueio de código.

Limites restantes: não há geração de imagem, aprovação/publicação, importação
massiva de PDF, ativação do worker nem prova de rede externa. Jobs de código
permanecem bloqueados até existir sandbox HTTP deny-all verificado.
