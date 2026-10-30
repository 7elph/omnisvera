# Contrato para agentes: testar o Companion sem usar a mesa real

Esta ferramenta é para **outras IAs**, não uma tarefa operacional para o usuário.
Use o MCP local `companion-tests`. Não peça ao Mestre para executar comandos,
copiar tokens ou interpretar JSON. O agente inicia, acompanha e explica o resultado.

## Ferramentas disponíveis

O lote `inventory_summons` também roda `economy-market-smoke.cjs` (compra,
venda, barganha, serviços, recibos, reload e dois clientes). Para esse cenário,
forneça uma cópia TEMP com Thoradin/Conclave configurados, HP a 5 PO e pó no
estoque do Conclave; não aplique preparação de fixture ao banco operacional.
Aceite as capturas explicitamente antes de certificar a interface.

O mesmo lote inclui `market-followup-smoke.cjs`: oferta individual, preservação
de cargas/ferrugem, cura paga e armas/magias de Klhauss. O preparador
`backend/scripts/market_followup_fixture.py` adiciona o objeto de ensaio e os
serviços somente em `TEMP/.../simulation.sqlite3`; recusa o banco operacional.
Conclave/Klhauss precisam existir na cópia. Dependência ausente é INCONCLUSIVE.

| Ferramenta | Entrada | Saída |
|---|---|---|
| `companion_test_capabilities` | nenhuma | atores, limites, resultados possíveis, política de isolamento |
| `companion_test_start` | request_id, actors, scenarios opcional | run_id e estado; início assíncrono |
| `companion_test_status` | run_id | estado, verdict e report estruturado quando concluído |

`actors`: `raziel`, `morthak`, `vezemir`, `dorn7`. Sem `scenarios`, executa os
adaptadores existentes desses personagens. Para repetição seletiva, use IDs
exatos de `report.scenarios[].scenario_id` da execução anterior. Não invente IDs.
O host pode prefixar os nomes com `companion-tests`; use os nomes efetivamente
descobertos no cliente. Disponibilidade local não significa ferramenta já
instalada em todo chat/conector remoto.

### Lotes limitados e resultados parciais (16/10)

`ui_suite: "sprite_studio"` exige quatro atores e `ui:true`. Executa somente
`sprite-studio-smoke.cjs`: importação/recortes/sequência, vínculo visual de Dorn,
idle/caminhada após movimento nativo confirmado, reload, visual jogador mobile,
fallback estático e privacidade do editor. Usa Nimalis copiada para TEMP. Não
certifica combate integral, novos ângulos de arte ou redes móveis externas.

`ui_suite: "catalog"` exige quatro atores e `ui:true`: roda a identidade das
quatro fichas e `catalog-recovery-smoke.cjs`. Verifica cura normal por toque,
confirmação perdida após commit, reload/replay sem nova cura, três fórmulas e
ícones Relâmpago/Adaga de Dorn, em 1440/390 px. Todo preparo ocorre na fixture
TEMP. Não certifica custos/repertórios, reversos ou todo o catálogo. Consultar
`RECOVERY_DORN_CATALOG_2026-10-28.md`; inspecionar as capturas explicitamente.

`ui_suite: "active_spells"` exige quatro atores e `ui:true`; executa somente
`active-spell-effects-smoke.cjs`, com 300 s por script e teto de 20 minutos.
Valida Dissipar por pin/área, escolhas dentro da confirmação, cancelamento,
resultado nativo, custo/retry/ledger/reload, em 1440/390 px. API de Velocidade,
regeneração e Mísseis tem cobertura distinta das identidades visuais das quatro
fichas. Inspecionar capturas; não certifica todas as magias ou mesa externa.
Escopo: `ACTIVE_SPELL_EFFECTS_2026-10-27.md`.

`ui_suite: "monster_defaults"` exige quatro atores e `ui:true`; executa apenas
`monster-defaults-smoke.cjs`. Cobre equipamentos/repertórios de encontro por
HTTP nativo, ataques de condição sem dano fictício e identidade/controles de
PV nas quatro fichas em 1440/390 px. Mantém o teto por script e o isolamento
TEMP; usa d20 físico controlado nas chamadas de ataque. Inclui os módulos
`monster-specials-scenarios.cjs` e `monster-specials-visual.cjs`: Esfera, Flagelo,
Ferrugem e Enxame por comandos nativos, com modais em 1440/390 px. Inspecionar
as capturas explicitamente. Metadados ausentes de Ferrugem, expulsão de
morcegos, divisão de projéteis e preparação diária continuam assistidos.
Escopo: `MONSTER_ENCOUNTER_DEFAULTS_2026-10-27.md`.

`ui_suite: "oct24"` exige os quatro atores e `ui:true`. Executa dois scripts
fixos: `table-balance-oct24-smoke.cjs` e `monster-exposure-poison-smoke.cjs`.
O segundo cobre olhar com confirmação explícita, cancelamento/retry, gás com
JP/imunidade individuais, carga após sete ataques e venenos no relógio nativo,
em desktop e 390 px. Toda preparação ocorre na fixture TEMP de 8871; não nas
fichas reais. Conserva 300 s por script, teto de 20 minutos e admissão de 1024 MB.
O d20 físico de ataque é controlado no transporte (15); não comprova digitação
do dado na interface. Aceitação visual exige inspeção das capturas pelo agente.
Escopo e limites: `MONSTER_EXPOSURES_AND_POISON.md`.

`ui_suite` é opcional e participa da idempotência. Padrão `full` preserva os 12
scripts existentes. `combat`, somente com os quatro atores e `ui: true`, executa
`sheet-combat-readiness` e o smoke estendido `three-sheet-actions` em dois scripts
fixos: a primeira metade cobre Vezemir/Morthak e a segunda cobre Dorn, com dez
ativações no total, incluindo Reflexos; Raziel é regressão de layout. O split não
aumenta o orçamento de 300 s por script nem o teto de 20 minutos do ensaio.
O lote explícito `ui_suite: "hemomancy"` executa somente `hemomancy-weapons`, com
os quatro atores obrigatórios: dois scripts fixos de três casos, seis ativações de Raziel nas cinco
armas aprovadas, cancelamento, confirmação nativa, custo/reload e duas páginas
locais, em larguras desktop/celular. Isso não certifica mesa externa nem poderes
vampíricos restantes. Full preserva os 12 scripts anteriores; combat mantém os
mesmos dez casos, agora em dois scripts. O teto
continua em 20 minutos; selecionar cenários API pelos IDs observados se necessário.
Não executa biblioteca/loja/mapas nesse lote e não certifica essas áreas.
O lote explícito `ui_suite: "vampiric"` também exige os quatro atores e `ui:true`.
Usa dois scripts fixos: `raziel-vampiric-smoke` (Regeneração em desktop/Mestre
e Mordida em 390 px/jogador) e `raziel-vampiric-second-smoke` (Caixão em
390 px/jogador e Forma da Noite em desktop/Mestre). Exercita cards atuais,
alvo no grid, confirmação automática, custo/recarga, reload e retorno da forma
animal ao perder PV; não usa os controles legados de `raziel-ready-smoke`.
Cada script conserva 300 s e o job 20 minutos. UI coverage só é atribuída
às ações concluídas. Todos os scripts/lotes anteriores permanecem inalterados.
Não certifica todos os animais, passivas, mídias ou redes reais. A fixture copia
somente as três imagens de animais auditadas, não a pasta inteira de uploads.
O lote explícito `ui_suite: "necromancy"` exige os quatro atores e `ui:true`.
São três scripts fixos: Toque Sombrio/Aterrorizar, esqueleto/Animar Mortos e
Clonagem/Magia da Morte. Usam os cards atuais e os comandos nativos: cadáver no
grid, coexistência, reutilização/dispensa sem reembolso, ticks/expiração, custo,
retry e reload. Clonagem prepara um fragmento do catálogo somente na fixture,
explicitamente registrado; isso não reabastece nem certifica o inventário real.
Mantém 300 s por script e 20 minutos por job; não usa o smoke antigo que exigia
preparação manual de magia. Recibo PASS requer execução, e aceitação visual
continua dependendo da inspeção das capturas. Não certifica todas as ações.
O lote focal `ui_suite: "rest"` exige os quatro atores e `ui:true`. Executa
somente `map-toolbar-rest-smoke` e `four-sheet-rest-smoke`, preservando os 12
scripts do lote full. O segundo usa o botão nativo Descanso geral e observa
PV, condições, contadores e área Status nas quatro fichas, com reload e
larguras 1440/390; estoques consumíveis e efeitos de NPC alheio não devem ser
restaurados/removidos por consequência. Preparação somente na fixture TEMP.
Mantém 300 s por script e 20 minutos por job. Código do smoke não constitui
evidência de execução; conferir relatório terminal e capturas. Não certifica
mesa multirrede nem uma ficha inteira.
`lightning` também exige os quatro atores e `ui:true`: readiness + fluxo nativo
de Relâmpago (1/3 alvos, cancelamento, mobile, revisão/mapa e segunda página local).
Não substitui o lote full nem certifica combate completo; contrato do piloto em
`ACTION_CONTRACT_PILOT_2026-10-16.md`.
Escolher cenários de API pelos IDs exatos do relatório anterior mantém o lote
dentro dos mesmos 20 minutos, sem aumentar o teto ou omitir checks silenciosamente.

`status.progress` informa fase, cenário/script atual, quantidade e tempo.
Ao terminar cada script, há checkpoint privado do relatório e sua duração.
Um timeout para apenas a árvore criada pelo runner. Em ERROR/CANCELLED/INTERRUPTED,
`partial_report` pode recuperar cenários/checkpoints válidos já concluídos,
incluindo IDs para nova seleção; não substitui `report` conclusivo e nunca torna
`certification_ready` verdadeiro. FAILs presentes continuam visíveis.
Ausência de checkpoint válido não vira evidência. Recibo terminal antigo não é
reativado nem reclassificado porque o código do conector foi atualizado.

Se o host mantém o MCP antigo em memória, precisa recarregar somente o conector
para enxergar o novo campo; isso não exige reiniciar o backend operacional.
Não interromper outro job nem remover lock para forçar acesso.

O lote `ui_suite: "inventory_summons"`, com os quatro atores e `ui: true`, testa
compra/uso da poção comum de HP, agregação dos frascos legados e manuais, retry,
reload e substituição confirmada de esqueleto oculto em outro mapa. Só usa a
fixture TEMP. O veredito visual depende de revisar suas capturas.

`ui_suite: "item_families"` é o lote focado de armas/munição, armadura/escudo
e consumível declarativo: compra pela UI, equipar, consequência defensiva,
uso em Recursos, disparo/consumo idempotente e persistência após reload.
Ele também integra `inventory_summons`. A nota sintética é criada na cópia
TEMP antes de iniciar o servidor para não depender de invalidação externa
do cache de notas. Não escreve no Vault ou banco operacional.

Lotes focados adicionais: `ui_suite: "passives"` exercita os gatilhos das cinco
passivas hemomânticas; `ui_suite: "summon_turns"` cobre ataques, permissões e
ciclo dos turnos das invocações. Ambos exigem os quatro atores e `ui: true`,
usam somente scripts fixos e não ampliam o lote `full` nem seus limites de tempo.

`ui_suite: "friday"` exige os quatro atores e `ui:true`. Executa, em sequência,
prévia privada das seis preparações (1440/390 px), compra da mochila de 5 PP
na loja real de Thoradin **copiada na fixture**, dez ações das fichas em duas
metades, passivas hemomânticas, turnos das invocações e descanso geral.
Valida cancelamento, moedas preservadas, retry, estoque em uma segunda página
local e reload. Não substitui redes externas nem aceitação das screenshots.
Não altera `full` (12 scripts), a margem de 1024 MB, os 300 s por script ou o
teto de 20 minutos por job. Usa o mesmo banco TEMP e os comandos nativos.
Ausência de estoque/capa/preparação na fixture não autoriza mutação operacional.
Um script ainda não executado não é prova visual: conferir o relatório e suas
capturas antes de declarar PASS. Dados físicos controlados no transporte de um
ensaio devem ser declarados; não comprovam a entrada desses dados pela interface.
O executor lê o recibo JSON terminal em uma ou várias linhas. Ausência explícita
de componente pode retornar `INCONCLUSIVE` com código 2; código 2 sozinho não
oculta falha de asserção. Saída não zero nunca fornece PASS/cobertura e FAIL
declarado interrompe o lote mesmo se um script sair com zero por engano.

`ui: true` adiciona aceitação no frontend compilado, na mesma fixture privada:
layout das fichas em desktop/celular, PV pendentes sem sobreposição e benefícios
de especialização visíveis. Com os quatro atores, também executa o smoke nativo
`compact-sheet`: grupos recolhidos, ícones na área de Status, JP/dados compactos,
inventário/equipamentos e carteira somente leitura para jogadores. O smoke
de mapa também testa que ampliar no celular não aumenta o viewport nem bloqueia
a navegação. Estes checks não certificam ofertas comerciais ainda não cadastradas.
O smoke `map-commerce` usa Nimalis e os pins copiados da campanha para exercitar
vínculo NPC/local, compra, venda, barganha, serviços, retry e atualização de uma
segunda janela. Cadastros e transações de ensaio ficam somente na fixture.
O smoke `shop-header-library` confere as 37 imagens reais do estoque de Thoradin,
quantidade explícita, header com nível ao lado da barra de vida e consolidação
de NPCs sem apagar instâncias distintas; desktop e 390 px, sem compras reais.
O smoke `three-sheet-actions` executa Força Arcana de Vezemir, Aterrorizar de
Morthak e Força Arcana de Dorn pela ficha, com consequência/custo/reload.
Tem dez casos no modo estendido isolado; a bateria MCP full padrão usa três para
respeitar seu limite total. Matriz e evidências: `THREE_SHEETS_AUDIT_2026-10-15.md`.
O ensaio também cobre clique no card → pin → Sim/Não → aplicação digital automática (`grid-action-flow`),
com alcance, seleção múltipla, cancelamento e resposta atrasada (`range-multitarget`),
além dos ensaios específicos de magias/cards. O smoke `map-toolbar-rest` verifica
zoom horizontal, ausência de setas/seletor de movimento, drag de pins por mouse/toque
e descanso geral dos quatro atores com limpeza
de efeitos persistida após reload, na fixture. Os adaptadores de API mantêm cobertura
do modo físico legado; esse modo não certifica sozinho a seleção nova pelo mapa.
Exige build atualizado, Node, Playwright e Edge. Confira `report.ui_smoke`;
PASS de API sem esse campo não certifica interface. Falha visual gera FAIL;
dependência ausente/timeout gera INCONCLUSIVE, nunca PASS. Não prova celular
físico/redes diferentes nem certifica toda mídia; a fixture tem vault isolado.

## Exemplo de chamada de ferramenta (não é comando para o Mestre)

Complemento focal de 23/10: o smoke fixo de preparações também executa
`today-encounter-probe.cjs`, somente na mesma fixture TEMP/8871. Usa os quatro
inimigos PREP da Âncora e Vezemir/Raziel/Dorn, coordenadas de entrada declaradas,
movimento nativo, ataques básicos digitais via API, confirmação/retry e três
contextos de navegador observando realtime/reload. A iniciativa é declarada;
não é teste de rolagem da iniciativa, clique nos cards ou balanceamento estatístico.
Não atribui cobertura UI às ações executadas pela API. Um inimigo derrotado antes
de atacar não ganha evidência de execução do seu ataque. Mantém 300 s por script.
Mídia final é recapturada no mesmo visualizador; revisar as imagens continua
obrigatório. Se o armazenamento MCP atingir 100 recibos, não apagar histórico
nem aumentar o limite: o executor nativo `run_sheet_test.py` continua disponível,
com fixture/travas/limites existentes, mas seu recibo avulso não vira evidência
MCP anexável ao laboratório nem certificação de mesa externa.

```json
{
  "request_id": "audit-raziel-morthak-001",
  "actors": ["vezemir", "morthak", "raziel", "dorn7"],
  "ui": true
}
```

1. Descubra capacidades; inicie com um request_id único e guarde run_id.
2. Consulte status, espaçando consultas enquanto estiver RUNNING.
3. Resposta perdida: repita start com o MESMO identificador e parâmetros.
   Recebe o mesmo job, inclusive após reconectar o servidor. Mudar parâmetros
   com esse ID é conflito; após corrigir código use um NOVO request_id.
4. Leia verdict, scenario_counts, cenários, checks e entradas da ficha.
5. Entregue um resumo claro: o que funcionou, o que falhou e o que segue manual.

## Não confundir os resultados

- `COMPLETED/PASS`: cenários selecionados passaram; não significa ficha inteira automática.
- `COMPLETED/FAIL`: o ensaio concluiu e encontrou falha; não é erro de conexão/MCP.
- `ERROR/INCONCLUSIVE`: problema do launcher/fixture/relatório/timeout; não afirmar regra quebrada.
- `CANCELLED` ou `INTERRUPTED`: não existe certificação dessa tentativa.
- `EXPECTED_BLOCK`: rejeição prevista, não ação executada com sucesso.
- `PENDING`, `ASSISTED`, `RULE_BLOCKED`, `UNAVAILABLE`: não chamar de automático.

### Certificação por ação

`verdict: PASS` significa que os cenários selecionados passaram. O campo separado
`certification_ready` só fica verdadeiro com evidências por ação das quatro fichas,
incluindo UI. Consulte `report.certification.characters` e `report.certification.gaps`.
Cada lacuna contém ator, chave estável da ação e `missing_checks`:
`execution`, `persistence`, `idempotency`, `cost`, `range`, `expiration`, `ui`.
Custos e expiração são exigidos conforme o contrato de teste da ação.

Consulta de alcance não certifica execução; mutações de preparação da fixture
também não. Layout renderizado ou card aberto/cancelado não certifica o uso.
Os scripts visuais retornam `action_coverage` somente para ações efetivamente
concluídas. Essa evidência de UI não pode declarar custos backend como comprovados.
Falha de cenário/UI impede certificação, mesmo com outros cenários verdes.

Fingerprints identificam a ficha/inventário/nível ensaiados, sem publicar as notas
privadas. Mudança na ficha exige novo ensaio; recibo antigo não certifica dados novos.
Itens, recursos e passivas continuam inventariados; `ASSISTED` é a classificação
conservadora do ensaio, não prova de que uma passiva do produto seja manual.
Regras bloqueadas ou componentes ausentes não são corrigidos silenciosamente.
O teste de Clonagem usa o componente persistido: sem fragmento, registra a rejeição.
O ensaio visual pode preparar um componente explicitamente apenas na fixture;
isso não torna o inventário operacional pronto.

O JSON e Markdown privados do mesmo ensaio incluem as lacunas. Outra IA deve
trabalhar a partir delas, sem criar um executor paralelo nem editar regras da mesa.

Relatório continua listando todas as entradas da ficha selecionada, mesmo num
teste seletivo; só os cenários realmente executados atribuem cobertura.
Não apagar FAIL porque outra ação teve PASS. Diferencie defeito de cadastro,
defeito de implementação e defeito do próprio ensaio. O Anel Rúnico foi um
exemplo real de inconsistência: cura diária declarada, mas consumo `none`.
Esse defeito foi corrigido por manutenção explicitamente autorizada, com
regressão do ciclo de carga/descanso e smoke MCP nativo. Evidência atual e
limites: `RUNIC_RING_AND_SESSION7_CLOSURE_2026-10-12.md`. Relatórios antigos
continuam mostrando o FAIL histórico; não confundir com uma nova execução.

## Segurança e limites

Somente stdio local; sem porta MCP pública, sem autenticação de jogador e sem
ampliar a superfície da API operacional. O host do agente tem acesso privado
a estes resultados. Não fornecer o serviço/relatórios aos jogadores.

O adapter só chama o executor já existente, com cópia SQLite/vault no TEMP e
credenciais CF-01. Não aceita script, código, SQL, URL, token, source_db ou
regra de RPG enviados pelo modelo. Logs/snapshots completos ficam privados no
TEMP; a resposta MCP é o relatório compacto. Nunca incluir tokens, bancos,
logs ou evidências em commits/prompts públicos.

Um servidor/job ativo por checkout (lease de arquivo liberada pelo SO), até
100 recibos guardados e 20 minutos por ensaio. BUSY não autoriza matar outro
processo. Timeout/desconexão encerra apenas a árvore de processo criada pelo
adapter. Não limpa histórico/material automaticamente. Recibos sobrevivem à
reconexão; RUNNING abandonado vira INTERRUPTED, não PASS nem nova execução.
Encerramento abrupto do SO pode deixar uma fixture finita até ela terminar;
não matar processos desconhecidos para liberar sua porta.

Ferramentas não aprovam alterações mecânicas ou publicação: editar valores
da campanha, entregar itens, reiniciar produção, fazer commit/push ou enviar
mensagem a outra tarefa exige autorização correspondente. Uma falha de teste
não amplia essa autoridade.

## Integração existente

Lote focal de 24/10: `ui_suite=oct24`, com os quatro atores e `ui: true`,
executa somente `table-balance-oct24-smoke.cjs` na fixture nativa. Confere
Ceifa/Carrasco a 25%, custo/reserva, sangramento pré-turno/retry e apresentação
de Reflexos/Teia. Não concede cobertura às demais ações. Dado físico 15
controlado no transporte é declarado; revisar capturas antes de aceitar UI.

`opencode.json` já registra `companion-tests` e este guia. O projeto usa o SDK
MCP **1.30.0**, já fixado em `backend/requirements-observer.txt`; não instala
SDK de versão diferente nem depende de LLM específico.

Para outro host MCP local, o agente/integrador deve registrar:

```json
{
  "command": "C:/Users/delib/Desktop/OMNISVERA/omnisvera-agent/.venv-observer/Scripts/python.exe",
  "args": ["C:/Users/delib/Desktop/OMNISVERA/omnisvera-agent/backend/scripts/companion_test_mcp.py"]
}
```

Isso não instala automaticamente um conector remoto no ChatGPT nem muda a
configuração global de Codex/outros clientes. Sessões OpenCode já abertas
podem precisar recarregar sua configuração; não interromper conversa ativa.

Referências de transporte/configuração: [OpenCode MCP local](https://opencode.ai/docs/mcp-servers/)
e [SDK MCP Python](https://github.com/modelcontextprotocol/python-sdk).
Código instalado é a referência de compatibilidade usada neste corte.

## Extensões posteriores

Controle de recursos (21/10): o executor compartilha uma trava de trabalho
pesado com a oficina de IA. `resource_busy` não inicia fixture, backup ou
adaptador nem consome tentativa de proposta. No Windows, fixture e cada script
visual têm grupos de processos próprios, encerrados ao sair/falhar; o driver
só recebe o sinal para executar depois de entrar no grupo. O stdin usado para
isso é privado, nunca o pipe de protocolo do MCP. A margem de 1024 MB e os
timeouts existentes não foram reduzidos. Ver `MEMORY_GUARD.md`.

O serviço não gera código de teste arbitrário por interpretação de ficha.
Novos cenários exigem adaptador seguro no executor nativo, teste de regressão
e regra aprovada. O MCP continua restrito aos ensaios isolados; não executa
JSON de propostas. Cenas agora possui laboratório privado de revisão via
rotas GM (aba administrativa), sem substituir cenas reais nem publicar conteúdo.
Usar `AI_COMPONENT_MAP.json` para localizar handlers, contratos e componentes;
não criar motor de regras ou mapas paralelo.

## Contratos, inventário de ações e propostas (16/10/2026)

- Contratos aprovados: cinco magias de Dorn (Relâmpago, Reflexos, Força Arcana,
  Teia, Dissipar Magia), Força Arcana/Velocidade de Vezemir, Clonagem/Magia da
  Morte de Morthak e Sangue Defensivo de Raziel. Dez ações delegam aos handlers
  e recibos existentes; não é migração integral. Ver
  `SHARED_ACTION_COMPONENTS_2026-10-16.md` e `RESUME_COMPANION_2026-10-16.md`.
- `GET /gm/actions/manifest/{character_id}` inventaria a ficha **efetiva**;
  `GET /gm/workspace/tokens/{token_id}/action-manifest` reutiliza o token nativo.
  Binding é localização do executor, não certificação de toda a habilidade.
  `visible_on_sheet=false` preserva comandos legados fora dos cards atuais;
  não apagar sua evidência nem tratar essa marca como autorização. A auditoria
  agora inclui os nove comandos únicos das cinco armas de Raziel e suas cinco
  passivas. Estimativa de custo usa a arma ativa na leitura; o handler continua
  autoridade. Ver `FOUR_SHEETS_STATUS_2026-10-19.md` para execução e lacunas.
- `GET /gm/compendium/provenance` expõe o primeiro lote de quatro fontes
  verificadas. Não confundir fonte conferida com regra da campanha aprovada.
- Laboratório: `GET/POST /gm/scenes/{scene_id}/lab/proposals`,
  `GET/PUT /gm/scene-lab/proposals/{id}` e `POST .../{id}/evidence|decision`.
  Usar autenticação GM pelo cliente já autorizado; não copiar tokens para
  propostas, prompts, logs ou commits. O conector de testes não fornece tokens.
- Criar proposta privada é diferente de executar/publicar. Edição gera nova
  revisão e invalida evidência/aprovação corrente. `expected_version` protege
  concorrência; em retry manter corpo e `request_id` originais.
- Para vincular evidência, enviar somente `run_id`, `expected_version` e
  `request_id`. O servidor lê um relatório MCP terminal do próprio checkout;
  não aceita um `PASS` informado pelo cliente. A evidência cobre o **código
  existente**, não significa que o JSON da proposta foi executado.
- Aprovar é revisão manual, nunca concessão de poderes, publicação ou ativação.
  O fluxo de execução arbitrária de propostas e a importação/revisão de todo o
  acervo PDF continuam fora da entrega; importar novos lotes com fonte/página.
- A fixture de UI recebe apenas cópias limitadas das imagens referenciadas,
  preservando caminhos e fonte. Consultar `ui_smoke.media_fixture`: mídia
  faltante/limites não são aceitação visual; revisar screenshots explicitamente.
