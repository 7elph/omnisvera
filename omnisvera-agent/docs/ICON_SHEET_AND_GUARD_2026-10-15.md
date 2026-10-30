# Ficha por ícones e Guarda — 15/10/2026

## Corte

- Nível: seta e engrenagem lado a lado; continuam restritas ao Mestre.
- Anotações: folha no cabeçalho de atributos, com JP/dados; editor nativo no diálogo.
- Inventário: seis colunas, somente ícone/quantidade. Equipar/guardar apenas no
  diálogo do item, também aberto pelos equipamentos. Mantidos os comandos
  idempotentes, slots persistidos, erro/retry e borda dos itens equipados.
- Equipamentos: ícones horizontais por slot, sem minicard preto ou nome visível.
  O nome e a descrição permanecem acessíveis ao clicar. Fallback do catálogo
  existente cobre Kit básico e armadura de couro; nenhuma mídia criada.
- Magias/habilidades: regra extensa só nos detalhes; cards mostram nome, ícone,
  uso real disponível e marcador Passiva. Nenhuma regra/custo removido do backend.
- Raziel mantém ataques nativos; Hemomancia separada, recolhida, seletores em linha.
- Guarda: seleciona aliado adjacente pelo pipeline de grid atual e confirmação.
  O próximo ataque contra o aliado é redirecionado automaticamente para Dorn,
  com CA/PV dele, consumindo a interposição. Sem checkbox de opt-out. Expira no
  início do próximo turno de Dorn, como antes; sem alterar ações/turnos.
  Retry reutiliza o recibo mesmo após consumir Guarda. Ataque direto não pode
  ignorar proteção ativa. Sem grid, o card não inventa alcance/posição.

## Arquivos

Frontend: `CharacterLevel.tsx`, `CharacterNotes.tsx`, `InventoryItemIcon.tsx`,
`EquipmentLoadout.tsx`, `HemomancyCard.tsx`, `DornProtocolControls.tsx`,
`MonsterAttackPanel.tsx`, `SessionWorkspace.tsx`, `companionTheme.css`.
Backend: `dorn_protocols.py`, `combat.py`, `main.py`.
Testes: `backend/test_dorn_protocols.py`; frontend `icon-sheet`, `inventory-icon`,
`dorn-protocols`, `combat-controls`, `morthak-combat-availability`, `session6-rewards`,
`compact-sheet-smoke`, `grid-action-flow-smoke`, `vezemir-inventory-smoke`,
`design-system-smoke`.

## Evidência e ativação

Frontend: 295 testes PASS, typecheck e build PASS. Backend: primeira rodada
completa 804 PASS; 17 testes específicos de Guarda PASS após fixar a seleção
ao pin exato do mapa de combate (personagens podem ter pins em vários mapas).
Rodada completa final: **805 backend PASS**, **295 frontend PASS**; typecheck
e build PASS. Inclui teste RED/GREEN de Guarda com alvo obrigatório (Provocação):
a intenção do inimigo é validada antes da interposição, sem bloquear o golpe
por o receptor final ser Dorn.

Primeiro MCP `test-39006d313e694bec90c51ece9087960c`: quatro ataques API e
dois scripts visuais PASS; terceiro FAIL por desalinhamento dos seletores de
Hemomancia. Capturas também mostraram que a cascata geral ainda desenhava
fundo nos botões de item. Ambos corrigidos com regras locais de layout; ensaio
agora exige fundo transparente e três seletores alinhados.
Segundo MCP `test-8b6940b65fb0496180a55f072867fc8f` ainda encontrou a regra antiga
de coluna única. Corrigida a cascata local (colunas, order e span dos labels).
Ensaio direto com a mesma fixture descartável passou nas quatro fichas, incluindo
Guarda pelo pin, redirecionamento real, retry e PV do aliado preservados.
O teste nativo de inventário passou com Mestre desktop e jogador mobile:
equipar/guardar no diálogo, reload, sem alterar PV/quantidade/cargas.

MCP `test-e6e70f573c3746af8c6b06eac0d7e8d5`: cinco scripts visuais PASS,
incluindo o corte compacto e Guarda; design-system FAIL porque o driver ainda
contava minicards de inventário como cards grandes. Adaptado para validar os
cards de ação; inventário tem agora asserções próprias de seis colunas/ícones.

Ensaio final MCP `test-530ee293880443ed92ab0d23d7dee3cf`: **COMPLETED/PASS**,
`report.ui_smoke.status=PASS`, **9/9 roteiros visuais PASS**, com os quatro atores.
Os replays iniciais também passaram nos quatro ataques de API. O corte compacto
executou Guarda de verdade via card → pin → confirmação, ataque automático do
inimigo contra o aliado, redirecionamento para Dorn e retry sem nova rolagem.

Aceitação visual explícita: inspecionadas capturas em
`%TEMP%/omni-compact-sheet-vhHRsI`, incluindo identidade do Mestre (seta/engrenagem),
JP/dados/anotações, inventário de seis colunas, cards de Morthak, equipamento de
Raziel e seletores horizontais. Equipamentos também conferidos no desktop.
Kit básico e couro carregam imagens do catálogo, sem caixas pretas de botão.
Alguns ícones antigos de magia não são copiados pela fixture; imagem de Lâmina
de Sangue foi confirmada HTTP 200 no operacional autenticado, não é mídia ausente.
Não é certificação completa das fichas: `physical_actions=false`; celular físico
e redes distintas não foram ensaiados neste corte.

## Operacional

Backup privado `backend/data/backups/pre-icon-guard-20261015-103246`, SQLite
consistente, tokens e configuração preservados. Backend oficial reiniciado de
PID 123788 para 147352; túnel preservado. Nove tabelas duráveis comparadas iguais
antes da limpeza. Encerrados somente os dois efeitos antigos de Dorn por
`dorn_spell_end`, com IDs e versionamento nativos. Depois da limpeza: nenhum
efeito/condição de Dorn; fichas, níveis, PV, inventários, sessões, pins e grids
continuam iguais ao backup. Não foi concedido descanso nem feita recarga.

Health autenticado e frontend local/público: HTTP 200; bundle `index-D63tharW.js`,
CSS `index-JAwKXvau.css`. Nenhum ataque de QA foi enviado ao operacional.
Leitura inicial encontrou somente Reflexos e Força Arcana antigos em Dorn,
com duração narrativa, sem mapa. Não foi concedido descanso para limpá-los.

Limites: emulação de celular não certifica aparelho físico/redes diferentes;
Guarda conserva uma interposição, não é provocação em área ou proteção infinita.
Sem staging, commit ou push; demais mudanças do worktree preservadas.
