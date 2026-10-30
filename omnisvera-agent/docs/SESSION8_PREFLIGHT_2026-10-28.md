# Sessão 8 — fechamento operacional de 28/10

Não confundir verificações locais/públicas deste computador com aceitação no
celular dos jogadores. O Mestre relatou timeouts e imagens incompletas no
4G/5G; ainda falta confirmar a recuperação no dispositivo depois da publicação.
O prazo solicitado de 40 minutos terminou às 23:03, sem essa confirmação.

## Publicação e estado real

- Companion e OpenCode 1.18.32 responderam ao preflight.
- Quatro fichas no nível 5: Vezemir 47/47, Raziel 37/37, Morthak 13/13,
  Dorn 35/35; nenhuma condição ativa na consulta.
- Seis preparações privadas disponíveis; 36 imagens dessas preparações
  responderam 200 pelo endereço público.
- As 71 referências diretas de imagem encontradas nas quatro fichas têm
  arquivo local. Isso não prova transferência no celular nem todos os fallbacks.
- Thoradin: 37 ofertas revisadas, 37 aptas, nenhuma bloqueada. Não foram
  inventados serviços nem alterados estoque ou preços neste corte.
- Correção de instruções privadas antigas para incluir Morthak: elementos
  49–54, 56 e 59. Visibilidade, pins e fichas preservados; backup separado.
- Backend ativado com backup `recovery-dorn-catalog-20261028-234614`:
  25 tabelas protegidas e tokens preservados. Somente timestamps de mapas
  variaram. O frontend de prévias menores está registrado no recibo de publicação.

## Correções de carregamento e combate

- Leituras de ficha e resumo usam projeção sem manutenção/escrita, com prazo
  limitado. Dados têm prioridade; imagens fora da tela carregam depois.
- Recuperação confirmada remove somente o aviso antigo de carregamento da
  ficha/lista. Rejeições de ações continuam visíveis.
- Validação de alcance procura o pin no mapa atual, evitando selecionar um
  pin antigo de outro mapa.
- Cadastros preparados com `sheet.source` textual causavam erro 500 ao abrir
  ações e resolver ataques. A origem textual é preservada e não tratada como
  objeto do bestiário. Regressão cobre cadastro, biblioteca e resolução.
- Medição pública após as correções: personagens 0,55 s; mesa 0,05 s;
  lista de mapas 0,02 s; registro 0,40 s. São medições deste computador.
- Verificação posterior contornou o MagicDNS local e usou os dois IPs públicos
  do Funnel com TLS/SNI originais: personagens e mesa responderam 200 em
  2,74–3,15 s. Isso ainda não reproduz a conexão do aparelho do Mestre.
- O Mestre confirmou que os avisos persistiam após as primeiras publicações.
  Foi encontrada carga de 40.872.811 bytes nas 71 imagens diretas das fichas.
  Prévias de ícone somaram 266.660 bytes (−99,35%), sem alterar originais.
  Ícones usam 128 px, arte do equipamento 768 px; diálogos e mapas mantêm os
  originais. Cache derivado limitado em TEMP, sempre atrás da autenticação.

## Sete frentes e limites

| Frente | Entrega deste corte | Limite |
| --- | --- | --- |
| Recuperação de comandos | Mesmo ID nativo após reload; seletores por aba; correção da corrida de carregamento | Não é outbox universal; alvo removido exige nova escolha |
| Ícones de Dorn | Fixture e referências compartilhadas verificadas nos cenários | Sem certificação de todas as imagens no celular |
| Catálogo | Remover Paralisia individual, além das três curas já automatizadas | 4 contratos automatizados, 83 parciais, 763 assistidos, 4 bloqueados |
| Monstros | Febre de Esgoto e veneno de cabelo da Medusa nos gatilhos explícitos | Reinfecção, casos cumulativos e dados ausentes continuam assistidos |
| Comércio | Mesma validação de oferta no cadastro, cotação e confirmação | Não automatiza todos os serviços ou a economia da campanha |
| Oficina de IA | Projeção de revisão respeita arquivo/proveniência; worker nativo iniciado com guardas | Nenhuma imagem nova certificada; rascunho não vira publicação automática |
| Preparações | Revisão de 17 rascunhos da sessão 7 e elenco corrigido | Não equivale a revisar integralmente as sete transcrições |

## Evidência de testes

- Backend completo: 1690 testes; um erro de mock antigo corrigido depois e
  um skip por permissão de symlink. Rechecks focados passaram; não houve uma
  segunda execução completa verde. Lote de combate legado: 47/47; biblioteca
  de ações/recuperação e origem legada: 15/15.
- Frontend completo anterior às últimas correções de carregamento: 465/465.
  Último lote de timeout/recuperação/leitura: 20/20. Typecheck e build passaram.
- Ensaio nativo `test-4b270d17fbe24dc7b318242fa953ba99`: 89 cenários PASS e
  2 bloqueios esperados; interface FAIL no ataque do inimigo preparado.
  Após correção, `test-e76b36c73f114bd780d4841e53b266be`: quatro cenários de
  identidade/ataque e sete scripts de UI PASS, sem alterar produção. Cenas,
  combate preparado, compras/saldo, ações, passivas, invocações e descanso.
  Este lote precede a última otimização de imagens; não certifica todo catálogo.
- Prévia autenticada e cache: backend 5/5; componentes/URLs de imagem:
  frontend 19/19; novo typecheck/build concluídos antes da publicação.
- As capturas de Cenas em 1440/390 px foram inspecionadas: cards, biblioteca,
  mapa sob demanda e imagens legíveis, sem mapa expandindo toda a página.
- As seis capturas de identidade de ficha do lote `catalog` (diretório TEMP
  `omnisvera-sheet-readiness-aPqnOn`) incluem os quatro atores, Mestre e
  Jogador, 1440/390/360 px. Foram inspecionados Vezemir, Raziel, Dorn e Morthak;
  isso não transforma a falha posterior do catálogo nesse lote em PASS.
- Sem staging, commit ou push; checkout misto preservado. Não foram alteradas
  fichas reais para ensaio. Nenhuma aceitação multirrede pode ser inferida.

## Arquivos principais do corte

Backend: `action_library.py`, `schemas.py`, `main.py`, `action_range.py`,
`combat.py`, `catalog_spell_contracts.py`, `data/catalog_spell_contracts.json`,
`spell_engine.py`, `monster_riders.py`, `monster_conditions.py`,
`monster_poison_specs.py`, `monster_poison_runtime.py`, `item_catalog.py`,
`catalog_readiness.py`, `map_commerce.py`, `merchant.py`,
`ai_workshop_routes.py`, `workshop_asset_reviews.py` e testes relacionados.
O corte de carregamento também adiciona `image_previews.py` e seu teste.

Frontend: `api.ts`, `selectionRecovery.ts`, `readJson.ts`, `spellOutcome.ts`,
`attackOutcome.ts`, `components/ActionCard.tsx`, `CompendiumPanel.tsx`,
`MonsterAttackPanel.tsx`, `InventoryItemIcon.tsx`, `SheetDetail.tsx`,
`EquipmentLoadout.tsx`, `pages/SessionWorkspace.tsx` e testes relacionados.

Documentos específicos: `WORKSHOP_ASSET_REVIEW_PROJECTION_2026-10-28.md`,
`MONSTER_DISEASE_HAIR_2026-10-28.md`, `ITEM_OFFER_READINESS_2026-10-28.md`,
`SCENE_CONTENT_REVIEW_2026-10-28.md` e `preparation/TODAY_GM_PLAYBOOK.md`.
