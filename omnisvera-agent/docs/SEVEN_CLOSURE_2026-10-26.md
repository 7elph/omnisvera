# Sete frentes — entrega verificada em 27/10/2026

Elenco: **Vezemir, Raziel, Dorn e Morthak**. Dorn continua controlado pelo
Mestre. As sete frentes **não estão integralmente concluídas**. Esta entrega
foi testada e ativada, mas não certifica todo o catálogo nem uma mesa externa.

## Situação de cada frente

| Frente | Entregue e observado | Limite que permanece |
|---|---|---|
| 1. Confiabilidade | Backend/site público respondem; JS e imagens têm MIME correto. Ensaios nativos em SQLite TEMP, quatro atores e UI. | Celular físico, redes distintas e duração de uma mesa real: **INCONCLUSIVE**. |
| 2. Fichas e combate | Corrigido erro 500 de monstro autoral com `source` textual. Removido card duplicado de Guarda que gastava recurso sem aplicar proteção. Ensaios de ações clássicas, passivas, invocações e descanso aprovados. | Os lotes têm escopo específico; não certificam todas as combinações ou botões das quatro fichas. |
| 3. Bestiário | 198 descrições públicas acrescentadas; 199/255 possuem descrição. Recuperados 14 bônus explicitamente presentes na fonte. Agora 329/365 ataques têm configuração completa. | **36 ataques incompletos**, **16 conjuradores sem repertório explícito**, 56 sem descrição pública recuperada e 107 sem ilustração vinculada. Nenhuma regra inventada para preencher esses vazios. |
| 4. Magias | Dados de duração, quantidade, imagens e atributos deixaram de virar dano por inferência. Escala por nível/alcance exige texto explícito e nível real do conjurador. Bola de Fogo usa uma rolagem compartilhada, com JP individual. | Das 854 entradas, **376 são manuais**. As 478 com handler genérico não têm necessariamente custo, duração, área e todos os efeitos automatizados. A contagem manual aumentou ao retirar automações falsas. |
| 5. Itens e comércio | Corda corrigida para 1 PO conforme descrição; nomes/pesos de kits normalizados sem mudar IDs. Parágrafos/tabelas são referências, não mercadorias vendáveis. Compra em Thoradin validada na cópia isolada. | 326 registros incluem 207 itens concretos e 119 referências. Zero lacunas objetivas nos concretos segundo o auditor atual não certifica todo efeito mágico, estoque, serviço ou imagem. Carteiras/estoque operacional não foram reescritos. |
| 6. Sessão 8 e mídia | Seis blocos privados como rascunhos com os quatro atores. Morthak disponível nos cinco mapas preparados. Dez retratos de NPCs e uma arte de Górgon revisados/vinculados; 19 NPCs têm retrato cadastrado. | Blocos opcionais não são acontecimentos canônicos. O encontro preparado não substitui cobertura de monstros aleatórios. Nenhuma sessão/combate iniciada. |
| 7. Automação das IAs | Worker nativo ativo, uma carga pesada por vez, mínimo de 1024 MB livres e pausa durante sessão/combate. Texto/código usam Ollama Cloud; houve geração real FLUX. OpenCode e conector de testes online. | Dois modelos gratuitos recusaram por cota em 26/10. Código em nuvem é análise textual, sem executar sugestões. Limites locais não garantem cota externa. Rascunhos exigem revisão. |

## Checks e ensaios

- Backend: **1.520 testes, OK; 1 ignorado**. Log:
  `%TEMP%/omni-seven-closure-backend-authorized.log`.
- Frontend: **422/422 aprovados**. Log:
  `%TEMP%/omni-seven-closure-frontend-authorized.log`.
- `npx --no-install tsc --noEmit`: PASS. `npm run build`: PASS.
  Permanece aviso de bundle principal acima de 500 kB.
- `git diff --check`: PASS. Worktree misto preservado; sem staging, commit ou push.

O primeiro lote teve 91 cenários API sem falha; os seguintes repetiram casos
selecionados e UI, sem alegar certificação completa. Evidências nativas em
`%TEMP%/omnisvera-ai-tests-ec76133d3556/<run-id>/evidence/`:

| Evidência | Run ID | Resultado e escopo |
|---|---|---|
| Cenas, Thoradin, ações clássicas | `test-c5dc2f7327214cfd8ed79f22c23fa508` | Quatro scripts iniciais PASS. O job inteiro falhou depois em seletor antigo do smoke de passivas; não contar como PASS global. |
| Passivas de Hemomancia | `test-362a778d721a4c54b6ca073e71ebe30f` | PASS: crítico do Arco, Carrasco condicionado aos PV, Exposto, combo e Revanche. |
| Turnos de invocações | `test-9fe538fc0a2d43bf8b4b3001f461112c` | PASS: esqueleto, reanimado e clones; turno próprio, privacidade, dispensa, morte, expiração e reload. |
| Descanso e mapa | `test-dccdae29e1da4d0c87afb045a874301e` | PASS: quatro fichas, PV/status/contadores, persistência, zoom horizontal e drag. Estoque consumível e efeito de NPC alheio preservados. |

Capturas desktop e viewport 390 px de passivas, invocações, descanso e mapa
foram inspecionadas pelo agente. São evidências de navegador local, não teste
em aparelho físico. Alguns d20 são entradas controladas no transporte.

## Ativação e preservação

Backend reiniciado com backup em
`C:/Users/delib/OmnisveraBackups/workshop-activation-20261027-002320`.
Recibo: `.autonomy/runtime/workshop-activation-20261026.json`.
Comparação de 21 tabelas confirmou preservação de fichas, inventários,
carteiras, posições, fog, sessão e combate; somente metadados `updated_at` dos
mapas mudaram durante a ativação. Hash dos tokens preservado.

Preparação anterior à ativação usou APIs nativas com backups separados:
retratos de NPCs, elenco privado e visibilidade de quatro pins existentes;
um pin nativo de Morthak foi acrescentado em Nimalis. Não houve alteração das
fichas reais, recompensa, movimento de pins existentes ou troca do mapa ativo.
Sessão 8 permanece planejada; nenhum combate está ativo.

Às 00:49 de 27/10 (São Paulo), o domínio público retornou HTTP 200 para HTML,
JavaScript e amostras de retratos/Górgon. OpenCode retornou 200 com
`companion-tests: connected`. Verificação desta máquina, não de outra rede.
O mapa ativo existente `map:c7c287b2b7bb4e3b` foi preservado.

## Automação e revisão

Configuração local: texto 12, imagem 2, código 12 tentativas por dia; intervalo
ocioso de 30 s. São tetos locais, sem promessa de cota externa ou RAM sempre
livre. O worker usa a trava compartilhada dos ensaios; não abre modelo local.

- 107 lacunas de arte enfileiradas; último recibo: 105 na fila, uma falha e um
  rascunho gerado. Enfileirar não significa gerar ou aprovar.
- O dragão dourado FLUX (`asset_job_id=66`, workshop 288) apresentou anatomia
  humanoide inadequada. Foi **ignorado pela API nativa**, preservando original
  e imagem atual. A oficina ainda mostra o job 288 aguardando revisão:
  sincronizar essa projeção continua pendente.
- Proposta de código 285 rejeitada: confundia trecho truncado com erro
  sintático e fazia alegações sem evidência. Nenhuma sugestão executada.
- Texto/código permanecem privados; não há importação automática em cena.
  Outros rascunhos continuam com revisão pendente.
- Górgon e dez retratos vinculados: **OpenAI imagegen**, não FLUX. Prompts,
  originais e atribuição em `GENERATED_ART_2026-10-26.md` e no manifesto de retratos.

## Arquivos deste corte

Fontes principais: `backend/app/monster_runtime.py`, `spell_engine.py`,
`item_catalog.py`, `merchant.py`, `catalog_readiness.py`, `monster_catalog.py`,
`workshop_execution.py`, `workshop_code_client.py`, `ai_workshop.py`,
`ai_workshop_adapters.py`, `ai_workshop_routes.py`; catálogos de monstros/itens
e manifesto de arte. Frontend: `SessionWorkspace.tsx`, `SceneWorkshopPanel.tsx`,
`MerchantPanel.tsx`, `MapCommerce.tsx`, `api.ts`, `sceneWorkshop.ts`.

Regressões/smokes: `backend/test_seven_closure.py`, `test_monster_actions.py`,
testes de magias, `frontend/tests/{dorn-protocols,sheet-cleanup}.test.cjs`,
`three-sheet-actions-smoke.cjs`, `today-encounter-probe.cjs`,
`hemomancy-passives-smoke.cjs`, `summon-turns-smoke.cjs`.
Scripts de fonte: `backend/scripts/enrich_monster_descriptions.py` e
`repair_monster_attack_bonuses.py`. Documentos de preparação, 11 imagens e
manifesto preservam a origem. Outras alterações do worktree são anteriores
ou de terceiros e não foram incorporadas a commit por este corte.

Inventário: `.autonomy/runtime/seven-closure-catalog-readiness.json`.
Recibo final: `.autonomy/runtime/seven-closure-final-20261027.json`.

Próxima frente concreta: completar mecanismos reutilizáveis por família de
efeito e resolver lacunas de fonte/configuração antes de liberar cada grupo;
validar a mesa externa separadamente. Não preencher dano, repertório ou regra
ausentes por suposição silenciosa.
