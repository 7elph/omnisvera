# Progressão e build aprovado de DORN-7 — 2026-10-07

## A. Estado inicial e preservação

Branch: `devin/create-omnisvera-class-standard`.
HEAD: `8f6444c13cbb55603d9e97699d47b0cbd0ba2a4d`.
Working tree já continha alterações de produto, imagens/providers, UI e alterações externas de Vault/Obsidian/mídia. O corte acrescenta alterações sem limpar a árvore. Exclusões preexistentes de DornUnitIdentity e seu teste não foram revertidas. Não houve staging, commit, push, reinício operacional ou escrita no banco/Vault operacional.

## B–C. Causa e correção estrutural

O ajuste manual de definição persistia `level` sem passar pelo cálculo de progressão. O mecanismo antigo de confirmação era separado, limitado por perfil e rolava PV ao confirmar. O ajuste manual agora passa por `level_recalculation.recalculate` na transação da definição: recalcula BA/JP, recursos mágicos e desbloqueios existentes no contrato; preserva offsets manuais e não recarrega recursos gastos. `progression_contract` permite tabelas aprovadas de outras classes sem ramificação por personagem.

Não foram inventadas tabelas: Guerreiro e Mago têm suporte aprovado até nível 4; Hemomante até nível 2. Classe/nível desconhecido recusa a alteração inteira. Redução abaixo da âncora sem histórico suficiente também recusa. Histórico existente de PV deste mecanismo é preservado e reutilizado ao subir novamente; rolagens antigas sem evidência suficiente não são inferidas.

## D. PV pendente

Nível → valores determinísticos → `dice_roll_requests` persistida → seção `PV · ROLAGEM PENDENTE` → controlador aciona `Rolar PV` → rolagem existente no backend → incremento registrado/aplicado na conclusão transacional. A UI não envia um número de dado arbitrário. Pendência é owner-only ou GM para controlados pelo Mestre. Usa chave estável, trava de double-click, histórico e recuperação de replay sem rerrolar/conceder duas vezes. Aumento de máximo não cura.

## E–F. Dorn aprovado

Aplicação explícita pelo Mestre, não no startup/leitura: botão `Aplicar ficha aprovada de Dorn · nível 3 / PV 20`, endpoint GM `/gm/characters/dorn7/approved-build`. A conciliação recusa combate/efeitos/ataques pendentes ou estado inicial ambíguo. Preserva ferimentos, XP, anotações, imagens e gastos sobreviventes; não modifica catálogo compartilhado com outro dono. Não foi aplicada à campanha real nesta tarefa.

- Unidade DORN-7, Constructo Arcano, Mago 3, movimento 9 m, máximo 20 PV; âncora aprovada, sem pendência para chegar a 20.
- FOR14/+2, DES8/-1, CON16/+3, INT16/+3, SAB12/+1, CAR6/-2.
- BA +1, JP14, CA11; apresentação: Base10 · DES-1 · Escritas Rúnicas+2.
- Malha Rúnica integrada: corpo a corpo +3, 1d6+2, foco/conduíte; não armadura.
- Adaga: corpo a corpo +3/1d4+2; arremesso +0/1d4 sem FOR. Precisa equipar a adaga no slot correspondente. Não foi inventado alcance numérico ausente no contrato de arremesso existente.
- Mísseis Mágicos C1, Levitação C2, Escuridão C2, Relâmpago C3. Quatro usos independentes 1/1, consumo0/1 e descanso1/1. Não há slots compartilhados RAW para este build.
- Cajado, Detectar Magia, Escudo Arcano e Recalibração removidos do build atual. O JSON histórico de Mago2 foi preservado como arquivo histórico; o carregador atual não o usa.

Mísseis reutiliza a resolução digital existente. Levitação, Escuridão e Relâmpago têm consumo/restauração operacional, mas a resolução completa de efeito/área/duração/dano permanece assistida pelo Mestre. Nenhum parâmetro de magia foi inventado.

## G–I. Constructo, Reparo e cura

As regras são determinadas por categorias semânticas explícitas do efeito: `physical_transformation`, `natural_disease`, `common_poison`, `magical_sleep`, `charm`, `mind_control`, `conventional_magical_healing`. Não se infere imunidade a partir de qualquer magia/poison genérico.

- Forma Imutável, doença natural e veneno comum: efeito categorizado rejeitado antes de aplicar.
- Mente Artificial: +4 JP somente nas três categorias aprovadas; JP comum não recebe bônus.
- Cura convencional categorizada: rejeitada no backend da ação/efeito com razão clara; Reparo e recuperação específica de constructos não são bloqueados.
- Natureza registrada; o produto não possui simulação de respiração/alimentação para automatizar algo adicional.
- Reparo: GM-only, Kit de Reparo no inventário com quantidade positiva, backend rola1d4, aplica com teto, registra ledger e responde idempotentemente. Kit é requisito permanente, não consumido: não havia consumo aprovado.
- Timing exatamente como a poção de HP existente: atualmente `use_item` não reserva ação de combate. Reparo também não introduz um novo custo. Isso não redefine a economia de poções.

Fontes não categorizadas continuam não identificáveis automaticamente; não alegamos que todo texto livre de magia é classificado pelo sistema.

## J. Protocolos e UI

Guarda, Vanguarda e Diagnóstico reutilizam `DornProtocolControls` e comandos/efeitos existentes, exclusivos do Mestre. Agora são expostos diretamente na ficha, não duplicados no agrupamento genérico de técnicas. Guarda continua exigindo turno/ação, aliado vivo e confirmação de posição; uma interposição antes da rolagem, expiração no início do turno seguinte. Vanguarda é estado sem bônus. Diagnóstico rola INT real, consome ação em combate e não cria lore. Traços/sistemas/componentes/efeitos têm seções recolhíveis com dados existentes, sem inventar estados de memória/comunicação/núcleo.

## K. Arquivos deste corte

Backend:
- Novos: `app/level_recalculation.py`, `app/construct_rules.py`, `app/data/dorn7_mage3.json`.
- Alterados: `app/character_play.py` (recalcular definição e dados derivados), `app/dice_rolls.py` (conclusão de PV, JP condicional e arremesso), `app/level_advancement.py` (bloqueio do fluxo antigo durante pendência), `app/dorn_mage.py` (conciliação explícita), `app/combat_effects.py` (validar efeitos/cura), `app/combat.py` (dano do slot arremessado), `app/player_inventory.py` (slots aprovados), `app/schemas.py` (metadados semânticos e arremesso), `app/main.py` (integração e rotas GM).
- Testes novos: `test_level_recalculation.py`, `test_dorn_construct.py`.
- Testes/fixture ajustados: `test_character_progression.py`, `test_dorn_mage.py`, `test_dorn_protocols.py`, `test_session6_acceptance.py`, `scripts/session6_acceptance.py`.

Frontend:
- Novos: `src/components/PendingLevelRolls.tsx`, `src/components/DornConstructDetails.tsx`, `tests/pending-level-rolls.test.cjs`, `tests/dorn-build-visual.cjs`.
- Alterados: `src/api.ts`, `src/components/CharacterLevel.tsx`, `src/pages/SessionWorkspace.tsx`, `src/styles.css`, `tests/level-advancement.test.cjs`.
- Este relatório. Arquivos compartilhados já tinham diffs anteriores; a lista não reivindica autoria de todo seu diff.

## L. Checks reais finais

- `.venv-observer/Scripts/python.exe -m unittest discover -s backend -p "test_*.py"`: **361/361 PASS**, 84,522s. ResourceWarnings de conexões SQLite em testes existentes, sem falha.
- `node --test tests/*.test.cjs` em frontend: **142 total,141 PASS,1 FAIL,0 skips**.
- Falha preexistente, observada antes de editar: `shared-attack-target.test.cjs:33`, regex exige grid antigo de Mísseis. Não foi alterada nem ocultada para declarar verde.
- `npx --no-install tsc --noEmit`: PASS.
- `npm run build -- --outDir C:/Users/delib/AppData/Local/Temp/companion-progression-ffc46d09e8554c1798d4f82a15ba046e/frontend-final`: PASS; aviso de chunks>500kB.
- `git diff --check -- .` na pasta Companion: PASS. Não é declaração de limpeza da worktree nem de whitespace externo ao Companion.

## M. QA real

Componentes React hidratados com CSS real e API fixture: mobile390×844 e desktop1440×900; expandir/recolher, Vanguarda, Diagnóstico, pendênciaPV, Guarda desabilitada sem combate, sem pageerror/overflow. Screenshots em `C:/Users/delib/AppData/Local/Temp/dorn-build-qa-n9SU86/`.

App completo em localhost8893, build isolado, SQLite/Vault temporários, tokens públicos sintéticos: ficha com ataques, quatro magias, protocolos, CA, inventário; Vanguarda ativada/desativada; Diagnóstico real retornou INT9/dificuldade12/inconclusivo; subida3→4 gerou pendência com máximo20; RolarPV aplicou +7 (d4+CON3), deixando20/27 sem cura e removendo a pendência. Reload manteve o estado. Nenhuma progressão real de Dorn foi feita. Desktop scrollWidth1440/viewport1440; mobile scrollWidth380/viewport390.

Limites: imagens do fixture não existem no Vault vazio; não é defeito novo de assets. O servidor de ensaio foi iniciado antes do último ajuste de nome/metadados, então ainda mostrou o título fixture `Dorn 7`; o nome definitivo está coberto pelo teste backend do build. Guarda/interposição e combate foram regredidos em testes backend existentes, mas não foi repetida toda interposição multicliente visual neste corte. Não há alegação de aceitação humana em redes distintas.

## N. Pendências comprovadas

1. Uma falha frontend preexistente de contrato CSS impede declarar suíte integralmente verde.
2. Três magias ainda não têm resolução digital completa; consumo e descanso funcionam.
3. Tabelas futuras fora dos níveis aprovados continuam bloqueadas, não inventadas.
4. Aplicação da ficha aprovada no banco real/reinício e aceitação operacional continuam não executados; revisão primeiro.

Sem commit, push ou publicação. Sem alterações de Vault/canon além da especificação de dados aprovada dentro do Companion. Sem novos mapas, grid, loot, morte ou imunidades.
