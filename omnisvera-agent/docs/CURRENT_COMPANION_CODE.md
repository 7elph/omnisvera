# Companion atual — guia de código para revisão

## Localizar a versão correta

Repositório: `7elph/omnisvera`.
Branch publicada: `devin/create-omnisvera-class-standard`.
Diretório do aplicativo: `omnisvera-agent/`.

Não presuma que `main` contém a versão operacional mais recente. Confirme
branch e SHA antes de analisar, e use os arquivos reais como autoridade.
O repositório contém o código, não o banco operacional ou os tokens da mesa.
Publicar código não concede acesso ao Companion autenticado em execução.

Último corte de passivas/turnos: `PASSIVES_SUMMON_TURNS_2026-10-21.md` registra
a correção dos turnos invisíveis de clones, checks concluídos e limites de
aceitação visual/ativação. Não confundir código em disco com runtime publicado.

## Pontos de entrada

Mercado: `ECONOMY_COMPLETION.md` descreve o registro unificado, recompra com
preço local, serviços, recibos auditáveis e a manutenção idempotente aprovada
para Thoradin/Conclave e os 18 PO de Raziel. Não chamar manutenção em GET/startup.
`MARKET_FOLLOWUP_2026-10-30.md` cobre ofertas individuais, serviços por contratos
revisados e o perfil editável de Klhauss com usos de magias no runtime nativo.

| Área | Arquivos principais |
| --- | --- |
| Backend/API e autorização | `backend/app/main.py`, `backend/app/config.py` |
| Fichas, recursos e ações | `backend/app/character_play.py` |
| Progressão | `backend/app/level_advancement.py`, `backend/app/level_routes.py` |
| Ataques e confirmação | `backend/app/combat.py` |
| Resumo pós-ataque e detalhes opcionais no registro | `frontend/src/attackOutcome.ts`, `components/AttackOutcome.tsx`, `pages/SessionWorkspace.tsx`; limites em `docs/ATTACK_OUTCOME_2026-10-15.md` |
| Turnos, efeitos e orçamento de ações | `backend/app/combat_effects.py` |
| Baforadas e componentes de passivas dos monstros | `backend/app/monster_runtime.py`, `monster_passives.py`, `monster_action_specs.py`; limites em `docs/MONSTER_PASSIVES_2026-10-25.md` |
| Equipamentos/repertórios de encontro editáveis | `backend/app/monster_encounters.py`, `data/monster_encounter_defaults.json`, `monster_catalog.py`; carregamento no formulário em `SessionWorkspace.tsx`; fonte SRD preservada. Escopo e contratos especiais em `docs/MONSTER_ENCOUNTER_DEFAULTS_2026-10-27.md` |
| Dano tipado e condições de acerto | `backend/app/damage_profiles.py`, `monster_riders.py`, `monster_conditions.py`; integração nativa e limites em `docs/MONSTER_RIDERS_2026-10-25.md` |
| Olhar/gás e venenos complexos | `backend/app/monster_exposures.py`, `monster_poison_specs.py`, `monster_poison_runtime.py`; fontes, regras aprovadas e limites em `docs/MONSTER_EXPOSURES_AND_POISON.md` |
| DORN-7 | `backend/app/dorn_protocols.py`, `frontend/src/components/DornConstructDetails.tsx` |
| Ciclo de efeitos e dissipação de áreas | `backend/app/spell_effect_runtime.py`, `dorn_spell_pack.py`, `necromancer_spells.py`; `frontend/src/dispelTargetSelection.ts`, `DispelEffectOptions.tsx`; `docs/ACTIVE_SPELL_EFFECTS_2026-10-27.md` |
| Magias de Necromante | `backend/app/necromancer_spells.py`, `frontend/src/components/NecromancerSpellControls.tsx` |
| Clonagem/Magia da Morte e pacote aprovado de Dorn | `backend/app/morthak_high_spells.py`, `backend/app/dorn_spell_pack.py`, manutenção explícita `backend/app/approved_spell_pack.py`; uso em `docs/APPROVED_SKILLS_2026-10-13.md` |
| Frenesi/Provocação e corte mínimo de Necromante | `backend/app/vezemir_skills.py`; limites e provas em `docs/APPROVED_SKILLS_2026-10-13.md` |
| PV e especializações | `backend/app/level_recalculation.py`, `frontend/src/components/PendingLevelRolls.tsx`, `frontend/src/components/SpecializationSection.tsx` |
| Raziel | `backend/app/vampire_powers.py`, `backend/app/data/raziel_vampire_powers.json` |
| Poderes de sangue aprovados / Caixão | `backend/app/main.py` (techniques), `backend/app/character_play.py` (`rest_in_coffin`), `backend/app/data/session_abilities.json`; fechamento em `docs/ACTION_COMPLETION_2026-10-12.md` |
| Invocações | `backend/app/summons.py`, `frontend/src/components/SummonControls.tsx` |
| Sessão, mapa e pins | `backend/app/session_workspace.py`, `frontend/src/pages/SessionWorkspace.tsx` |
| Sprite Studio e pins animados | `backend/app/sprite_studio.py`, `frontend/src/spriteAnimation.ts`, `spriteApi.ts`, `components/SpriteStudio.tsx`, `AnimatedSprite.tsx`; importação/vínculos visuais, limites e fontes em `docs/SPRITE_STUDIO.md` |
| Cenas: sequência, cards de contexto e mapa compacto | `frontend/src/components/ScenePreparationGallery.tsx`, `scenePreparation.ts`, `components/scenePreparation.css`; escopo em `docs/SCENE_CONTEXT_LAYOUT_2026-10-28.md` |
| Grid lógico e movimento | `backend/app/spatial_grid.py`, `backend/app/spatial_routes.py`, `frontend/src/spatialGrid.ts`; uso em `docs/SPATIAL_GRID_FIRST_CUT.md` |
| Clique no card, alcance e seleção múltipla | `backend/app/action_range.py`, `backend/app/dorn_spells.py`, `frontend/src/components/TargetingOverlay.tsx`, `cardActivation.ts`, `gridTargetSelection.ts`; regras e provas em `docs/RANGE_MULTI_TARGET_2026-10-14.md` |
| Contratos aditivos: dez ações aprovadas das quatro fichas | `backend/app/action_contract.py`, `morthak_action_contracts.py`, `raziel_action_contracts.py`, `action_components.py`, `action_library.native_action_contract`, definições em `data/dorn7_mage3.json` e `data/session_abilities.json`; `docs/SHARED_ACTION_COMPONENTS_2026-10-16.md`. Não é migração integral. |
| Ledger e realtime | `backend/app/session_ledger.py`, `backend/app/session_realtime.py` |
| Retry de magias/ações genéricas | `backend/app/spell_command_receipts.py`, `spell_engine.py`, `frontend/src/commandRetry.ts`; recibos transacionais nas duas rotas GM, limites em `docs/GENERIC_ACTION_RETRY_2026-10-28.md` |
| Recuperação no reload e catálogo de cura | `frontend/src/commandRetry.ts`, `api.commandRecoveryOptions`; `backend/app/catalog_spell_contracts.py`, `data/catalog_spell_contracts.json`; escopo e lote MCP `catalog` em `docs/RECOVERY_DORN_CATALOG_2026-10-28.md` |
| Loot | `backend/app/loot.py` |
| NPCs/locais: ofertas, barganha e serviços pelo pin | `backend/app/map_commerce.py`, `commerce_routes.py`, `merchant.py`, `frontend/src/components/MapCommerce.tsx`; uso e limites em `docs/MAP_COMMERCE_2026-10-15.md` |
| Anel Rúnico / consumo diário | `backend/app/combat_consumables.py`, `backend/test_runic_ring.py`; correção ativada e pendências em `docs/RUNIC_RING_AND_SESSION7_CLOSURE_2026-10-12.md` |
| Cliente HTTP e contratos TS | `frontend/src/api.ts` |
| Visual e responsividade | `frontend/src/styles.css`, camada final compartilhada `frontend/src/companionTheme.css`; padrão e validação em `docs/FRONTEND_STANDARD_2026-10-13.md` |
| Ficha compacta, equipamento e zoom mobile | `components/SheetSection.tsx`, `components/EquipmentLoadout.tsx`, `components/CurrencyCounters.tsx`, `pages/SessionWorkspace.tsx`; corte e limites em `docs/COMPACT_SHEET_AND_MAP_2026-10-15.md` |
| Inicialização | `start_companion.ps1`, `start_backend.ps1` |
| Índice para propostas/testes por IA | `docs/AI_COMPONENT_MAP.json`, `docs/AI_COMPANION_FOUNDATION.md`; índice de código verificado, não um formato paralelo de campanha |
| Teste isolado por ficha | `test_sheet.ps1`, `backend/scripts/run_sheet_test.py`, `backend/scripts/sheet_rehearsal.py`, `backend/scripts/all_actions_simulation.py`; uso e limites em `docs/SHEET_TEST_RUNNER.md` |
| Certificação por ação das quatro fichas | `backend/scripts/sheet_rehearsal.py`, campo `certification_ready` no MCP e `report.certification.gaps`; contrato em `docs/SHEET_CERTIFICATION_2026-10-15.md` |
| Matriz de Vezemir/Morthak/Dorn e correções de alcance/retry | `docs/THREE_SHEETS_AUDIT_2026-10-15.md`; regressões em `test_dorn_spell_map_scope.py`, `test_necromancer_grid_authority.py`, `test_vezemir_buff_concurrency.py` |
| Ferramentas para outras IAs | `backend/scripts/companion_test_mcp.py`, `backend/scripts/agent_test_jobs.py`, `opencode.json`; contrato em `docs/AI_TEST_TOOLS.md` |
| Integração e disponibilidade das ações na Cola do Mestre | `backend/app/native_action_manifest.py`, `sheet_action_inventory.py`; `frontend/src/actionReference.ts`, `components/CharacterActionReference.tsx`; leitura da ficha com `read_only=true`, escopo em `docs/ACTION_READINESS_2026-10-28.md` |
| Aceitação visual da ficha | `frontend/tests/sheet-combat-readiness-smoke.cjs`; MCP `companion_test_start` com `ui: true` usa somente fixture isolada; evidências em `docs/SHEET_COMBAT_READINESS_2026-10-12.md` |
| Mantenedor manual | `scripts/companion_maintainer.py`, `.autonomy/` (estado histórico, não prova de execução atual) |

O frontend usa React/Vite e o backend FastAPI/SQLite. Testes estão em
`backend/test_*.py` e `frontend/tests/*.test.cjs`.

## Contratos que devem ser preservados

- Backend é autoridade de estado, permissões, recursos e resultados.
- Controle Mestre/Jogador e visibilidade de dados privados não podem regredir.
- Confirmações devem preservar os contratos existentes de idempotência.
- DORN-7 continua controlado pelo Mestre; Guarda, Vanguarda e Diagnóstico
  não concedem aumentos permanentes de atributos, PV ou economia de ações.
- Invocações usam a infraestrutura de combate existente, com controle pelo
  proprietário e ações no card/pin correspondente.
- Descrições de habilidades são acessíveis sem inflar os cards compactos.
- No mobile, a imagem inteira define a superfície do mapa e seus overlays.
- Não modificar Vault/canon, mídias, modelos ou Godot por consequência de
  uma tarefa restrita ao Companion.

## Verificação local

Na pasta `omnisvera-agent` e com dependências disponíveis:

```powershell
python -m unittest discover -s backend -p "test_*.py"
cd frontend
node --test tests/*.test.cjs
npx --no-install tsc --noEmit
npm run build
```

Na raiz Git: `git diff --check`.
Dependência indisponível significa INCONCLUSIVE, nunca PASS.
Teste com dados descartáveis; não usar credenciais ou banco real para QA.
Suíte verde não equivale a mesa multicliente em redes distintas comprovada.

## Pedir ajuda ao ChatGPT

Informe repositório, branch e SHA, e peça que a análise comece por este guia
e `AGENTS.md`, seguida dos componentes e testes da área solicitada.
O ChatGPT precisa de acesso GitHub autorizado ou dos arquivos fornecidos;
este documento não configura nem amplia permissões de contas.
Não compartilhar tokens da mesa para obter uma análise de código.

## Fundação de ações e laboratório (16/10/2026)

Os módulos de contrato e `action_components.py` atendem dez ações aprovadas
(cinco de Dorn, dois buffs de Vezemir, Clonagem/Magia da Morte de Morthak e
Sangue Defensivo de Raziel), delegando aos comandos nativos. Não há executor universal
de texto nem habilitação automática de catálogos. `native_action_manifest.py`
inventaria as quatro fichas efetivas e tokens; fonte/automação/disponibilidade
e certificação são conceitos separados.
`sheet_action_inventory.py` mantém o legado auditável e identifica a superfície
atual (`visible_on_sheet`), incluindo nove comandos únicos de Hemomancia e cinco
passivas. Custos são estimativas de leitura, nunca autorização. Estado das quatro
fichas, checks e UI ainda inconclusiva em `FOUR_SHEETS_STATUS_2026-10-19.md`.

Cenas administrativo inclui `SceneLabPanel`: propostas privadas versionadas,
histórico, revisão manual e vínculo a relatórios MCP locais verificados.
`scene_lab_store.py` foi delegado ao OpenCode; rotas e UI integradas pelo Codex.
Aprovação não executa, publica nem altera o jogo. A evidência anexada refere-se
ao código existente, não à execução do JSON proposto. `catalog_provenance.py`
acrescenta quatro referências verificadas ao catálogo existente, sem substituir
regras OD1/campanha por OD2. Consulte `SEVEN_STEPS_PROGRESS_2026-10-16.md`
para checks, ativação e lacunas; fonte nova em disco não prova runtime atualizado.

Oficina (20/10): `SceneWorkshopPanel` e `ai_workshop_routes.py` projetam a fila
privada em Cenas, com contadores e prévias de rascunhos, sem executar/publicar.
Worker e provedores não são ativados ao abrir o painel. Estado e limites em
`STAGED_WORKSHOP_RECOVERY_2026-10-20.md`; a geração real ainda é pendente.

## Galeria de preparações em Cenas (22/10)

`ScenePreparationGallery.tsx` e `scenePreparation.ts` fornecem galeria e
visualizador privado sobre cenas, mapas e pins existentes. Cenas não monta
o workspace vivo ao lado; ele continua em Mapas/Mesa. Editor, oficina e laboratório
nativos são preservados. Escopo e checks em `SCENE_PREPARATION_GALLERY_2026-10-22.md`.

Fechamento para sexta (22/10): lote MCP explícito `ui_suite: "friday"`, capas e
retratos na mídia da fixture, diagnóstico de falta de RAM e capa ilustrada do
escritório em `FRIDAY_READINESS_2026-10-22.md`. Resultado de admissão sem RAM
não é execução de combate, screenshot revisada ou certificação da mesa.

## Hemomancia de Raziel

Hemomancia aprovada de Raziel (17/10): `app/hemomancy.py` fornece as cinco armas,
skills e passivas; compõe o ataque/confirm nativo, não outro motor. A ficha recebe
`definition.hemomancy` e usa `HemomancyCard`/`hemomancySelection` com alvo no grid.
`razielSheetAbilities` projeta dez ativas em Habilidades e cinco passivas em
Poderes vampíricos; Hemomancia mantém apenas as armas. Organização e limites em
`RAZIEL_SHEET_SECTIONS_2026-10-18.md`.
Marca Rubra voltou a Habilidades com contador da Reserva de Sangue e comando
transacional nativo: `RUBRA_MARK_2026-10-18.md`.
Revisão v2 (18/10): Estocada acrescenta 1d4, separado dos dados das passivas;
alcance, custos, ataque básico e demais armas preservados.
Regras e limites em `RAZIEL_HEMOMANCY_APPROVED.md`. O lote visual `hemomancy` inclui
`hemomancy-weapons-smoke.cjs`; código/build em disco não comprova ativação.

Ensaio focal `vampiric` (20/10): dois scripts fixos
`raziel-vampiric-smoke.cjs` / `raziel-vampiric-second-smoke.cjs` para Regeneração,
Mordida, Caixão e Forma da Noite, pelo MCP/fixture existentes. Contrato em
`AI_TEST_TOOLS.md`; resultados e recorte visual do seletor em
`VAMPIRIC_UI_CHECK_2026-10-20.md`. Não certifica todos os animais/redes reais.

Necromancia (20/10): lote focal `necromancy` em três scripts nativos para seis
ações de Morthak; contrato em `AI_TEST_TOOLS.md`, evidência e limites em
`NECROMANCY_UI_CHECK_2026-10-20.md`. `_token_record` distingue dispensa de morte
para não recriar cadáver de invocação dispensada; código em disco não prova
ativação operacional.
O card de esqueleto permite ao dono recuperar o controle após usar a ação;
isso consulta/reutiliza a invocação existente, não concede nova ação. O backend
continua validando turno, uso diário e limite de uma invocação ao criar outra.

Descanso geral (20/10): lote focal `rest` no MCP/executor existente, somente
TEMP, com quatro fichas e UI; escopo/resultados em `REST_UI_CHECK_2026-10-20.md`.
O disclosure Assets IA de `SessionWorkspace` monta seu painel apenas quando
aberto, evitando polling/referências enquanto fechado. Sem alteração de regras.

## Controle local de recursos

Combate aprovado em 24/10: `critical_rules.py` compõe críticos/falha crítica
no fluxo nativo; `hemomancy.py` v3 aplica custos unitários e reserva máxima 20.
`MapSpellEffects` renderiza Reflexos/Teia como projeções, sem criar combatentes.
Regras, arquivos e evidências: `RAZIEL_COMBAT_FIX_2026-10-24.md`.

O corte posterior de 24/10 usa Hemomancia v4 e reserva máxima **10**;
regras e ativação em `COMBAT_PIPELINE_2026-10-24.md`.
`monster_rules.py` acrescenta à rota de ações do bestiário um `rulebook`
com todos os textos, cláusulas, parâmetros, fonte e revisão dos 255 monstros.
O compêndio usa cards recolhidos; classificação não significa execução.
`monster_action_specs.py` detalha 15 habilidades de baforada em 14 criaturas,
sem interpretar dados de chance/duração como dano. O executor genérico usa
o fluxo nativo de PV e rejeita ficha/pin duplicados. Escopo e limitações em
`MONSTER_RULEBOOK_2026-10-24.md`.

Recursos locais (21/10): `scripts/memory_guard.py` fornece trava comum entre
ensaios de fichas e `ai_workshop.tick`. `run_sheet_test.py` contém suas próprias
árvores de fixture/navegador em Job Objects Windows e libera cada etapa ao sair,
sem encerrar aplicativos por nome. Gate privado precede a execução do driver;
workers Python entram no grupo antes da aplicação. Detalhes e limites em
`MEMORY_GUARD.md`; código em disco não prova ativação no backend operacional.

## Exclusões deliberadas

Tokens, `.env`, SQLite operacional, logs, backups, anexos, relatórios locais
de execução da autonomia e dependências instaladas não pertencem à publicação.
O Vault e a mídia externos ao Companion continuam fora deste corte.
