# Oficina privada: execução e revisão

A sessão 8 voltou a `planned`. Os 674 eventos observados antes desta sessão
eram ensaios técnicos de habilidades, inclusive poderes experimentais de Raziel.
Não constituem uma transcrição canônica. A fila de texto atual usa transcrições
das sessões 1–7. Nenhuma ficha foi restaurada ou modificada por esta transição.

## Produção

`start_ai_workshop.ps1 -Action start` inicia o worker nativo em segundo plano.
`status`, `pause` e `stop` consultam/controlam somente a oficina. A configuração
explícita fica em `.autonomy/runtime/ai-workshop-automation.json`, apontada por
`AI_WORKSHOP_CONFIG_FILE`. Sem ela, a automação nova fica desativada.

Um trabalho por vez: trava do checkout e slot compartilhado de memória/ensaios.
Novos trabalhos aguardam pelo menos 1024 MB disponíveis e mesa inativa. Um
pedido externo já enviado pode terminar se a sessão começar durante a resposta;
seu resultado permanece privado. Não são encerrados aplicativos para obter RAM.

Limites administrativos: texto 12, imagem 2 e análise de código 6 tentativas
por dia UTC. São tetos locais; não representam franquias ou resets conhecidos
dos provedores. Erros ambíguos não são repetidos automaticamente. Quota e
autenticação seguem o bloqueio/cooldown nativo, sem contratar serviços.

Texto usa Ollama `gpt-oss:120b-cloud` e recebe uma projeção mínima do grupo atual.
Imagem reutiliza o pipeline privado Cloudflare FLUX 2 Klein 9B e seus critérios
existentes de fallback. Análise usa somente modelo com custo zero verificado no
catálogo OpenCode, sessão com todas as permissões negadas e ferramentas
desativadas. Não aplica código nem executa sugestões. O limite gratuito do
OpenCode impediu concluir a delegação nesta execução; testes com mocks não
comprovam disponibilidade real do provedor.

## Revisão em Cenas

Somente o Mestre vê a oficina. Prévia de imagem autenticada usa header, Blob
temporário e limpeza ao fechar. Rascunhos de imagem continuam pelo fluxo nativo
de aprovação de assets, sem publicação automática.

Importar texto/análise exige escolher uma cena e confirmar o hash e a revisão.
O resultado são elementos nativos ocultos, privados do Mestre. Textos longos
são divididos em partes de até 2000 caracteres com marcadores de continuação;
o texto completo é preservado. O limite global de JSON da oficina continua em
50000 caracteres. Retry recupera partes já escritas sem duplicar nem mudar
o destino. Nenhuma cena é ativada ou publicada pela importação.

Checagens de qualidade são conservadoras: não certificam lore. Rascunhos com
nomes incertos usados como fatos ficam `needs_review`. A imagem piloto do
Górgon foi gerada, mas apresentou anatomia inadequada e permanece para revisão.
Nada disso foi aprovado automaticamente.

## Validação

Regressões em `test_workshop_execution`, `test_workshop_review`,
`test_workshop_code_client`, `test_ai_workshop_routes` e
`test_fixture_environment`. Ensaios CF-01 recebem banco separado da oficina e
configuração desativada em TEMP. `scene-workshop-smoke.cjs` verifica revisão
nativa em desktop/mobile, três jogadores sem acesso e quatro fichas preservadas.
Aceitação visual deve ser registrada após inspecionar as capturas. Isso não
certifica uma mesa com redes diferentes nem toda a campanha.

## Resultado observado

- Backend ativado com backup em `OmnisveraBackups/workshop-activation-20261026-064040`.
  Comparação de 21 tabelas: estado de jogo preservado; apenas timestamps dos
  mapas oficiais foram atualizados pelo startup. Tokens preservados.
- HTTPS público 200; acessos de Morthak, Vezemir e Raziel responderam como jogador.
- Worker ativo, mesa inativa, mínimo de 1024 MB; última leitura 1961 MB livres.
  Nove blocos adicionais processados, alcançando as 12 tentativas de texto de hoje.
  Quatro rascunhos aguardam aprovação; demais resultados problemáticos estão separados.
- Suíte backend: 1495 testes, OK, 1 ignorado. Regressões posteriores de assets
  e oficina: 41 e 69 testes OK; cliente OpenCode final: 4 OK.
  Frontend: 420 testes OK; regressões da oficina: 11 OK; typecheck e build OK.
- Navegador CF-01: PASS após corrigir a coluna estreita dos cards. Capturas
  desktop 1440 e mobile 390 inspecionadas e aceitas para a oficina.
  Evidência: `%TEMP%/omni-workshop-ui-a5qkmubl/workshop-report.json`.
- OpenCode: catálogo gratuito e permissões negadas verificados ao vivo;
  tentativa de análise sem resposta conclusiva ficou `needs_review`, sem retry
  automático. Não há uma análise entregue nem prova de disponibilidade contínua.
- Uma imagem real foi gerada; revisão visual reprovou a anatomia do Górgon.
  Mantida privada. O prompt agora também inclui ataques e traços do catálogo.
- Sem staging, commit ou push. Não certifica mesa externa ou toda a campanha.

Arquivos deste corte: `backend/app/ai_workshop*`, `workshop_execution.py`,
`workshop_review.py`, `workshop_code_client.py`, `asset_api.py`,
`asset_context.py`, `prompt_builder.py`; `backend/scripts/run_ai_workshop.py`
e `cf01_probe.py`; testes correspondentes; `frontend/src/api.ts`,
`sceneWorkshop.ts`, `components/SceneWorkshopPanel.tsx`, `companionTheme.css`;
testes da oficina e `start_ai_workshop.ps1`. Alterações anteriores misturadas
na worktree foram preservadas.

## Revisão das ressalvas e do texto repetido

O texto repetido da captura era conteúdo sintético da fixture visual: duas
frases repetidas 75 vezes para forçar uma importação longa. Isso não era saída
real do modelo nem foi importado na campanha operacional. Os 14 rascunhos reais
inspecionados não continham essa repetição. A fixture passou a usar parágrafos
fictícios variados e o texto sintético é identificado como teste.

`quality_notes` agora detecta conteúdo repetido dominante, preserva o original
para auditoria e o mantém `needs_review`; o Mestre vê o aviso e a importação
fica bloqueada. Refrões curtos comuns não são tratados como repetição abusiva.

O cliente OpenCode passou a despachar de forma assíncrona e observar apenas a
sessão criada por ele, com prazo total, ferramentas desativadas e permissões
negadas. HTTP 204 só confirma o envio. Cota, ferramenta indevida, permissão
pendente, erro do modelo e resposta inconclusiva possuem tratamentos separados.
Teste real novo: `opencode_free_limit` confirmado em aproximadamente cinco
segundos. O serviço está saudável; isso não libera a franquia gratuita. O
intervalo local de nova tentativa não é um horário de renovação informado
pelo provedor. A tentativa antiga ambígua permanece separada e não foi repetida.

A página oficial https://olddragon.com.br/monstros/gorgon descreve um touro com
carapaça metálica. O catálogo local omitia essa descrição. O campo foi adicionado
somente ao Górgon, mantendo a atribuição/licença do catálogo, e agora chega ao
prompt. A direção visual em inglês reforça anatomia quadrúpede antes do estilo;
isso é direção artística, não uma mudança nas regras. A primeira regeneração
continuou bípede e foi mantida para revisão; não foi publicada.

Uma única correção manual adicional, fora da produção contínua, tentou usar a
anatomia quadrúpede explícita em inglês no início do prompt. A geração falhou
no Cloudflare com HTTP 500/código 3043 e no fallback ZeroGPU com RuntimeError.
A causa não foi confirmada como quota de imagens. A direção visual corrigida
está implementada, mas ainda não há imagem nova aprovada. Nenhuma arte anterior
foi substituída. O limite automático de duas tentativas diárias foi preservado.

Validação deste segundo corte: 1502 testes backend OK (1 ignorado), 421 testes
frontend OK, typecheck e build OK. Arquivos adicionais: descrição/direção visual
do Górgon em `backend/app/data/old_dragon_srd_monsters.json`, detector em
`workshop_execution.py`, cliente assíncrono em `workshop_code_client.py`,
contexto/prompt de assets, aviso de repetição em `SceneWorkshopPanel.tsx` e
regressões correspondentes. Não há aprovação ou publicação de conteúdo real.
