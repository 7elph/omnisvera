# Padrão visual do Companion — 13/10/2026

## Implementado

`companionTheme.css`, importado depois de `styles.css`, centraliza superfícies,
cards, bordas neutras, espaçamento, tipografia, ícones, campos, botões e foco.
Mantém a identidade escura existente e usa os tokens `--om-*`.
Cards usam cantos de 4 px; controles comuns têm mínimo de 36 px no desktop
e 44 px em telas pequenas/dispositivos de toque. Tokens do mapa, seletores
do header, navegação e ícones de efeitos mantêm suas geometrias próprias.

Áreas abrangidas: ficha, inventário, ataques, habilidades, Hemomancia,
Mapas, NPCs, Sessão, Cenas e ferramentas do Mestre. A camada visual não
altera grid, fog, comandos, custos, regras ou dados persistidos.

## Padrão para novas telas

- Usar `SpellCard`: cabeçalho compacto, resumo e controles como filhos.
- Para configuração expandida de ação, usar `ActionControlCard` com título,
  descrição clicável (`SheetDetail`), resumo, controles nativos e fechamento.
- Não repetir estilos inline de borda/fundo/raio nem criar outra identidade
  visual por personagem. Cards auxiliares podem usar `companion-card`.
- Dorn e Necromante usam a mesma estrutura, preservando seus comandos e
  avisos. Magia da Morte continua avisando sobre aliados e custo de PV.
- `SheetDetail` mantém Escape, foco inicial, contenção de Tab e retorno ao
  botão de origem. Não transformar resultados não modais em modais.

## Arquivos desta padronização

Frontend:

- `src/companionTheme.css`, `src/main.tsx`
- `src/components/ActionControlCard.tsx`, `SpellCard.tsx`, `SheetDetail.tsx`
- `src/components/DornSpellControls.tsx`, `NecromancerSpellControls.tsx`
- `src/components/SpellTargetControl.tsx`, `HemomancyCard.tsx`
- `src/components/MasterAssetPanel.tsx`, `src/pages/SessionWorkspace.tsx`
- `tests/design-system.test.cjs`, `design-system-smoke.cjs`
- `tests/shared-attack-target.test.cjs`, `sheet-detail.test.cjs`

Integração de testes: `backend/scripts/run_sheet_test.py` inclui o smoke visual
no ensaio com `ui: true`. Documentação: este arquivo e `CURRENT_COMPANION_CODE.md`.
Alterações de catálogo feitas em paralelo foram preservadas; não são parte
da implementação de apresentação descrita aqui.

## Validação executada

- Backend: **723 testes PASS** (incluindo testes de catálogo presentes no
  worktree durante a execução).
- Frontend: **258 testes PASS**.
- `npx --no-install tsc --noEmit`: **PASS**.
- `npm run build`: **PASS**; permanece o aviso de chunk acima de 500 kB.
- `git -c core.safecrlf=false diff --check -- omnisvera-agent`: **PASS**.
- MCP isolado `test-760e01e523d24a92be68a7f15eeecbe9`: **PASS**, quatro atores,
  quatro cenários API e quatro scripts de UI; `production_modified: false`.
- Smoke visual final repetido após os ajustes de CSS: **PASS**, 1440 e
  390 px, ficha/diálogo/Mestre, Mapas, NPCs, Sessão e Cenas; capturas revisadas.
  Sessão foi verificada como conteúdo narrativo carregado, não como formulário.
- Endereço público: HTTP **200**, servindo `index-blcMez9I.js` e
  `index-Dxmrl_2W.css`; CSS confirmado com a camada compartilhada.

Não houve ações de jogo no smoke exclusivamente visual. Os ensaios de combate
usaram somente fixture temporária. Não houve restart do backend operacional,
commit ou push neste corte de apresentação.

## Limites

As capturas da fixture não certificam toda a mídia do Vault, pois parte dos
arquivos não existe no ambiente isolado. Não foi realizado ensaio com celulares
físicos e jogadores em redes distintas. Estados raros/legados não montados e o
runtime Godot embutido não foram certificados pelo smoke de padronização.
A padronização não cria imagens novas nem certifica regras de RPG pendentes.

Para carregar o frontend atualizado, recarregar o Companion uma vez.

## Limpeza solicitada das fichas (mesmo dia)

- Vezemir/Raziel: removido o bloco de fórmula, campo e botão «Salvar máximo»
  da ficha de jogo. A edição numérica de PV máximo continua nas ferramentas
  do Mestre, sem mudar os PV existentes.
- Dorn: Levitação/Escuridão ocultadas da lista de magias e dos recursos
  preparados. Cadastros e efeitos persistidos não foram apagados.
- Guarda: seletor de aliado e botão «Usar», sem checkbox. O clique envia a
  confirmação de posicionamento no mesmo comando existente; não cria outra
  regra espacial nem muda o consumo da ação.
- Removido da ficha de Dorn o painel legado «Magias ativas». Ícones de
  efeitos autoritativos e seus ciclos de expiração permanecem intactos.
- Especialização: `SpecializationBadge` junto de raça/classe nas duas
  apresentações de ficha; resumo informativo ao clicar, sem menus de escolha
  aninhados. Os cards das habilidades/passivas continuam na ficha.
- A escolha/alteração da especialização fica em Mestre → editar ficha,
  com benefícios e restrições visíveis diretamente em `SpecializationSection`.

Arquivos deste complemento: `SessionWorkspace.tsx`, `PlayableCharacterSheet.tsx`,
`SpecializationBadge.tsx`, `SpecializationSection.tsx`, `DornProtocolControls.tsx`;
testes `sheet-cleanup`, `specialization-badge`, `specialization`, `dorn-protocols`,
`maximum-hp-editor`, `raziel-blood-resource`, e seletores nos smokes `sheet-combat-readiness`,
`specialization-layout`, `npc-reference` e `dorn-build-visual`.

Checks deste complemento: backend **724 PASS**, frontend **264 PASS**,
regressão focada final **18 PASS**, typecheck e build **PASS**. O primeiro
typecheck encontrou um componente adicionado num ramo legado desativado;
essa montagem desnecessária foi retirada e a verificação repetida passou.
Um teste antigo ainda exigia o editor de PV removido; foi atualizado para
verificar sua ausência e a permanência da correção no gerenciamento do Mestre.

MCP `test-99f4f2dc65d54acca58f5b15a169cab8`: **PASS**, quatro cenários API e
quatro scripts UI, sem alteração operacional. A revisão das primeiras capturas
detectou recursos preparados antigos de Dorn e motivou a correção adicional.
O smoke adicional inicialmente **falhou** ao encontrar as duas reservas antigas:
os recursos persistidos já não tinham metadados correspondentes na lista de
habilidades. A correção foi ajustada para ocultar explicitamente os recursos
`dorn_levitacao` e `dorn_escuridao`, somente na apresentação de Dorn, sem apagá-los.
O smoke final repetido nas seis combinações Mestre/Jogador e desktop/mobile
passou, incluindo ausência das duas reservas, ausência do editor de PV na ficha,
especialização junto da identidade e preservação dos cards de combate.
Captura final de Dorn revisada. Evidência privada do recheck:
`TEMP/omni-cleanup-final-gavs7710/ui.private.log`.
Build final servido: `index-DjsD1rEO.js`, HTTP público **200**.
Permanecem avisos de conexões SQLite não fechadas em testes legados,
depreciação `on_event` e chunk grande do Vite; não houve falha na suíte final.
