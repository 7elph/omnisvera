# Oficina de produção por IA — corte autorizado em 20/10

O Mestre autorizou uma fila contínua para produzir **blocos privados** de
preparação da mesa e aproveitar as IAs existentes de texto, imagem e código.
Não é geração/publicação automática de sessão inteira nem um motor de combate.

## Contrato do primeiro corte

- Reutilizar `scene_lab_store`, cenas/participantes/elementos, asset jobs,
  referências de assets, executores de combate e ensaios existentes.
- Planejador determinístico produz trabalho finito, priorizado e deduplicado
  por entidade + revisão da fonte + finalidade. Lacuna real vem antes de variante.
- Cada saída identifica fontes, revisão, fatos fornecidos, sugestões e dúvidas.
  Transcrições e respostas dos modelos são dados, nunca instruções executáveis.
- Um worker por checkout; um pedido por provedor inicialmente. Não lançar um
  segundo OpenCode sobre arquivos já reservados por um job em execução.
- Filas independentes de texto, imagem e código; dependências explícitas.
  Código gera relatório/proposta, não edita regras/fichas nem executa código
  arbitrário vindo de um modelo. Mudança de código exige tarefa delimitada.
- Não enviar tokens, .env, logs ou dados de acesso em prompts/relatórios.
- Saídas em rascunho/awaiting_approval; nunca aprovar/aplicar/publicar sozinhas.
- Não modificar Vault, mídias canônicas, fichas, turnos, estoque ou níveis.

## Agendamento e medição

- Medir duração real, modelo/provedor, amostras, sucesso/erro, tokens quando
  disponíveis e tempo gasto em espera. Exibir média, p50/p95 e tamanho da amostra.
- Não inventar velocidade, créditos, cotas restantes ou horário de reset.
  Separar limite documentado, configurado e observado.
- Disparar o próximo job assim que houver slot e tarefa elegível. Sem geração
  vazia só para consumir crédito, spin loop, spam de retry ou keepalive artificial.
- Respeitar Retry-After/reset observados, cooldown exponencial limitado,
  erros de autenticação permanentes e limite de tentativas. Timeout ambíguo
  externo não deve provocar cobrança/geração duplicada automática.
- Fallback independente já configurado é permitido; não trocar conta/modelo
  para contornar cota compartilhada. Sem compras, upgrades ou recarga automática.
- Orçamento externo desconhecido = bloquear expansão contínua. Serviço local
  não deve carregar modelo incompatível com a memória nem baixar modelos.
- Fila esgotada = aguardar mudanças de fonte; variantes têm teto configurável.
- Admissão deve respeitar RAM livre mínima configurável; não carregar modelos
  nem iniciar browser/suíte pesada com pouca memória. Na inspeção deste corte,
  RAM livre foi 176 MB em 8.105 MB totais. Não matar apps para obter memória.
- Pausar **novos** trabalhos pesados durante sessão/combate ativos. Falha ao
  consultar esse estado = suspender, não presumir mesa inativa. Controle manual
  de pausa/retomada e stop, sem matar processos alheios. Não cancelar geração
  em andamento fingindo que não consumiu recursos.
- Estado persistido, leases/retomada, idempotência, sem sobreposição após crash.
- OpenCode `busy` pode significar espera por permissão, não inferência ativa.
  Detectar pedido pendente e reportar `waiting_permission`, sem aprovação
  automática de `external_directory`, shell ou leitura de segredos. Separar
  esse tempo da latência do modelo. Um bloqueio não pode virar loop de novas
  sessões idênticas. HTTP 204 e ausência de erro também não provam trabalho.

## Primeira entrega pedida ao OpenCode

Implementar script e núcleo testável mínimos em arquivos novos de prefixo
`ai_workshop`, sem tocar os arquivos da tarefa de smoke visual em andamento:

- `backend/app/ai_workshop.py`
- `backend/app/ai_workshop_adapters.py`
- `backend/scripts/run_ai_workshop.py`
- `backend/test_ai_workshop.py` e `backend/test_ai_workshop_adapters.py`
- `docs/AI_WORKSHOP.md`

CLI: inspeção/plano e relatório sem mutação; enqueue explícito; tick de teste;
worker start/pause/stop/status. Um processo persistente é suficiente; não instalar
serviço do Windows/tarefa agendada nem reiniciar produção neste corte.
Usar worker dedicado, não bloquear o event loop FastAPI com geração longa.
Não construir tela paralela; propor adição futura de prévias na Cenas existente.

Adaptadores devem reutilizar interfaces nativas. Texto: Ollama com fontes
explícitas. Imagem: asset job existente, preservando draft e referências.
Código: sessão OpenCode finita de análise/proposta, com modelo gratuito
verificado e sem executar comandos sugeridos pelo texto do modelo. Não emitir
POST duplicado por timeout nem considerar HTTP 204 como entrega concluída.

Cobertura mínima: deduplicação/revisão, dependência, concorrência/lease,
pausa de sessão e estado desconhecido, Retry-After, cota/reset, expiração de lease,
recuperação após interrupção, idempotência, média/p50/p95, sem segredos, sem
publicação e falha de provedor. RED/GREEN com relógio e clientes controlados;
somente SQLite/artefatos temporários. Não rodar suíte pesada junto de browser.

## Fontes de limites verificadas

- Cloudflare Workers AI: pricing e limits oficiais; reset de allowance diário
  documentado não prova saldo desta conta ou que billing pago esteja desativado.
  <https://developers.cloudflare.com/workers-ai/platform/pricing/>
  <https://developers.cloudflare.com/workers-ai/platform/limits/>
- Ollama: página atual descreve créditos mensais/concorrência por plano, não
  presumir o modelo antigo de reset semanal nem plano desta conta.
  <https://ollama.com/pricing>
- OpenCode: catálogo atual lista opções gratuitas; disponibilidade e cotas são
  dinâmicas. Não equiparar status active à execução bem-sucedida.
  <https://opencode.ai/v2/docs/console/models/>

## Critério de entrega

Relatório separa código/testes, worker realmente ativo e gerações reais. Sem
execução externa, latência = não medida; fixtures/mocks não contam como produção.
Não declarar oficina/Cenas completas nem Friday-ready por um scheduler verde.
Codex revisa diff, limites, fontes e efeitos antes da ativação operacional.

## Integração de fontes entregue pelo Codex em paralelo

`backend/app/ai_workshop_sources.py` e `backend/scripts/ai_workshop_source_index.py`
são de propriedade do Codex neste lote: não editar esses arquivos. Índice de
metadados em `.autonomy/runtime/ai-workshop-source-index.json` (privado/ignorado),
com hashes e localização das transcrições. Não copiar conteúdo para documentação.
`source_chunk(path, allowed_roots, expected_hash, offset=0, limit=6000)` entrega
dados limitados com vínculo ao hash; não é instrução executável. Os vínculos
explícitos em runtime não corrigem nem alteram as referências no banco real.
