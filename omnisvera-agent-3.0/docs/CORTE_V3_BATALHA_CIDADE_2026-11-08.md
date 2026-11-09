# Corte 3.0 · batalha frente a frente, cidade clicável, loja ROM2 e HUD Diablo — 08/11/2026

Escopo aprovado por Thiago: (1) encontro por proximidade com modo automático liga/desliga,
(2) tela de batalha frente a frente com linha de frente e retaguarda, IA simples dos monstros
com opção de o Mestre assumir, (3) cidade de Nimalis com pontos clicáveis ligados à loja e ao
pouso, (4) HUD estilo Diablo. O backend continua autoritativo: turnos, alcance, deslocamento,
dados, dano, preços e recibos são decisões do servidor.

## O que mudou

| Área | Arquivos | Comportamento |
|---|---|---|
| Visual | scripts/gothic_theme.gd, scripts/hud_orbs.gd | Tema escuro/dourado; globo de PV (vermelho) e do primeiro recurso da ficha (azul), retrato e cinto com até 4 poções do inventário. Valores vêm da ficha autorizada. |
| Encontros | scripts/encounter_watch.gd, main.gd | Só no cliente do Mestre. Pin de criatura visível, com ataques, não invocada e não ligada a estabelecimento, a até N células (padrão 4) de um herói no grid de exploração. Modo manual: diálogo Batalhar / Agora não / Não é hostil. Modo automático: inicia direto. Configurações na gaveta Combate (raio, arena, formação por personagem, lista de "não hostis"). Salvas em user://companion_v3.cfg do navegador do Mestre. |
| Batalha | scripts/battle_overlay.gd (reescrito), scripts/battle_ai.gd | Heróis à esquerda, criaturas à direita. "Frente" = adjacente a um inimigo (alcance real do grid), "Retaguarda" = não adjacente. Avançar/Recuar usam COMBAT_MOVE. Ataque corpo a corpo da retaguarda avança primeiro e depois pede confirmação. Números de dano, investida, morte e transição de entrada. IA: pede ao servidor as propostas assistidas (GET /gm/combat/tokens/{id}/action-proposals), escolhe o alvo mais próximo com menos PV, resolve/confirma pelos contratos existentes; sem proposta, avança e tenta de novo; senão passa o turno. Desligar a chave "IA dos monstros" devolve o controle ao Mestre. |
| Backend | omnisvera-agent/backend/app/battle_mode.py, combat_effects.py, test_battle_formation.py | Novo campo opcional `formation` no `start` do modo batalha: células iniciais validadas no grid da arena, sem repetir célula, só participantes. Inválido → nada é iniciado (transação inteira). Sem `formation`, comportamento idêntico ao anterior. |
| Cidade | scripts/city_screen.gd, assets/city/nimalis.json | Tela da cidade do ROM2 (townmain + máscara de regiões). Pontos: Equipamentos de Thoradin (loja), O Frasco Afogado (poções), Conclave dos Errantes (guilda/pouso), Praça (mapa de Nimalis com todos os pins reais), Portões (sair). Abre sozinha para todos quando o mapa ativo é Nimalis; o Mestre tem "Levar o grupo à cidade" / "Sair para os Arredores" (PATCH /gm/workspace/maps/active, com confirmação). |
| Loja | scripts/merchant_screen.gd | Layout da loja do ROM2 (shopmain, shopframe, shopinv, shoptable, shopmenu). Ofertas, venda, serviços e barganha via /workspace/tokens/{pin}/commerce, /commerce/{id}/quotes e /commerce/quotes/{id}/confirm, sempre com confirmação. |
| Prévia/proxy | tools/serve_preview.py | Liberadas somente: propostas de criatura, ofertas/cotação/confirmação de comércio, PATCH do mapa ativo (corpo só com map_id). |
| Arte | rom2-lab/tools/extract_screens.py | Extrai, somente leitura, as telas de cidade/loja/pouso do graphics.res para assets/rom2_local/{town,shop,inn} com SHA-256 em screens_provenance.json. Arquivos locais, fora do Git. |

## Trocar sprites depois

Edite assets/city/nimalis.json: `background` (imagem da cidade), `mask` (PNG em tons de cinza;
cada cor é um ponto clicável), `hotspots[].mask` (valor da cor), `pin` (id do marcador real) e
`highlight` (imagem acesa ao passar o mouse; sem ela o brilho é gerado da própria máscara).
Imagens próprias (por exemplo geradas no Flux) substituem a arte do ROM2 sem mudar código.

## Validação

- Backend: 62 testes direcionados (battle_mode, battlefield_extensions, combat, spatial_grid,
  monster_proposals) + 3 novos de formação, em SQLite temporário.
- Ensaio nativo contra backend descartável (tests/v3_fixture_server.py, TEMP): proposta de
  encontro, início com formação aplicada (heróis 5/3, goblins 6), ataque de Dorn (d20 10, 3 de
  dano), turnos passando, IA do Goblin atacando sozinha, encerramento devolvendo a exploração,
  visita à cidade, viagem do grupo, loja do Thoradin com compra confirmada (bolsa 20 → 10 PO) e
  Conclave listando a hospedagem.
- Nenhum comando mutável foi enviado à campanha real.

## Limites conhecidos

- Magias na arena: só Guarda do Dorn. Relâmpago e as demais continuam pela ficha/mapa até o
  seletor genérico de ações.
- Iniciativa continua 0 para todos (heróis primeiro), como no corte anterior.
- "Hostil" é heurística (criatura com ataques e sem vínculo de estabelecimento). Use "Não é hostil"
  para NPCs como Klhauss/Iria.
- O backend em produção só aplica a `formation` depois de reiniciado; até lá a batalha abre com as
  posições antigas e o Avançar/Recuar resolve.
- Arte do ROM2 é da Nival: uso privado da mesa; para publicar, trocar pelos próprios sprites.
