# Primeiro corte de comandos jogáveis — 06/11/2026

## Interface

As fichas não dependem mais da presença online: o seletor usa os personagens
que o backend autoriza consultar. Inventário e estado privados continuam
filtrados pelo servidor. A faixa superior distingue pessoas online (verde)
do personagem selecionado/controlado (azul quando não está online).

Dorn não desaparece quando o mapa recebido não contém seu pin. Nesse caso o
Mestre mantém uma **prévia local**, identificada no sprite e nos comandos.
O botão “Colocar este personagem no mapa” usa o cadastro nativo somente quando o
Mestre o aciona. O sistema não cria pins nem altera fichas automaticamente.

Os ícones Wenrexa já existentes no outro projeto foram copiados intactos;
proveniência em assets/ui/ASSET_SOURCES.md. Área de toque de 56 × 54 px, imagem
de 44px, sem fundo. A navegação fica no meio à esquerda; em telas baixas usa
duas colunas para manter o tamanho de toque. Nome do mapa discreto no topo.

## Movimento

Clique/tocar numa entidade a seleciona; clicar numa célula vazia envia um
caminho de células adjacentes ao endpoint espacial existente. Personagens sem
sprites continuam com representação estática; Dorn usa os quatro ciclos de
caminhada fornecidos. A representação só se move após confirmação do servidor.

EXPLORATION_MOVE amplia o mesmo motor espacial, fora de combate. Valida dono
ou invocador, visibilidade, grid, versão da posição, incapacidade, imobilização
e passos adjacentes. Não altera o relógio nem o orçamento dos turnos. Durante
combate o cliente usa COMBAT_MOVE, preservando turno, custo e todas as regras.
O Mestre também fica sujeito a essas regras ao usar o clique de jogador.
GM_REPOSITION administrativo anterior foi preservado.

O comando recebe um request_id aleatório e estável durante retry. Enquanto a
confirmação está pendente, outra intenção não é enviada. Falha de rede permite
repetir o mesmo comando; conflito do servidor exige nova leitura.

O mapa ilustrado agora é uma imagem sobre o mundo, sem um painel preto ao
redor. Mantém proporção, fog e pins, e permite pan/zoom local. Esse visualizador
flutuante continua separado dos comandos no piso isométrico.

## Dorn

A ficha tem Guarda e Relâmpago visíveis no início da gaveta. Guarda utiliza
/gm/combat/effects, ação dorn_guard: exige o combate/turno/uso nativos.
Relâmpago consulta /gm/actions/describe, usa revisão/alcance do contrato,
seleciona até três pins no grid e confirma a resolução nativa. Clique novamente
num pin selecionado para concluir antes de três alvos. Custos, JP, divisão do
dano e resultado continuam sendo decisões do backend.

As animações guard/cast começam após uma resposta de sucesso e voltam ao idle.
As prévias visuais separadas não enviam comandos nem consomem recursos. Se Dorn
não estiver posicionado, os botões são identificados como testes locais.

O painel de combate permite ao Mestre iniciar/encerrar um combate com os pins
visíveis do mapa, e passar o turno pelo contrato existente. Pins ocultos não
são incluídos automaticamente nessa seleção.

## Verificação e limites

- Testes espaciais: 18 PASS, incluindo novos RED/GREEN de exploração, propriedade,
  adjacência, replay e bloqueio durante combate.
- Smoke Godot e contrato de UI: PASS.
- Teste temporal Dorn: PASS. Cinco snapshots sem pin não ocultaram o idle;
  Guarda, cast e caminhada retornaram ao idle.
- Ensaio nativo FastAPI/SQLite descartável + Chrome: PASS em
  TEMP/omni-companion3-4pyqs4r5. Executou cliques de movimento Mestre/jogador,
  Guarda real, passagem de turnos e Relâmpago real com dano. Verificou também
  mapas, pins, sessões e a filtragem de informações privadas.
- TypeScript e build React passaram; saída em TEMP, sem substituir o legado.
- Backend completo: 2.155 testes, OK, um skip de privilégio de symlink Windows.
- Ativação com backup SQLite/token no launcher preservado, sem instalação,
  rotação de acessos ou substituição do frontend legado. Reiniciados somente
  backend 8787 e prévia 8872. Recibos em TEMP/companion3-playable-20261106 e
  .observer-runtime/companion3-playable-20261106-receipt.json.
- O verificador bruto sinalizou três updated_at de mapas oficiais alterados
  pelo registro normal no startup (Earthropo, Nimalia e Nimalis). A comparação
  por campo preservou nomes/imagens/visibilidade e confirmou os dados de jogo.
- Conferência pública horizontal 844×390: PASS, sem erros de script e sem
  comandos mutáveis. Capturas public-dorn-sheet.png e public-floating-map.png
  em TEMP/companion3-playable-20261106. Vinte e uma tabelas protegidas mantiveram
  seus campos de jogo; tokens preservados. Corrigido também o seletor que
  voltava à primeira opção enquanto mostrava a ficha de Dorn após polling.

Este corte conecta movimento e os dois comandos de Dorn descritos acima.
Os demais ataques/habilidades ainda precisam de ligação nativa no cliente
Godot. A seleção de alvos e os movimentos no mapa ilustrado flutuante continuam
como próximo corte; os comandos atuais usam o piso isométrico.

Não é uma certificação de desempenho em celular físico ou mesa em redes
distintas. Testes mutáveis usaram somente dados descartáveis. Não houve commit
ou push, mudança de canon ou migração de fichas reais.

## Arquivos do corte

Backend: app/spatial_grid.py, app/spatial_routes.py e test_spatial_grid.py.
Godot: scripts/main.gd, dorn.gd, navigation_panel.gd, hud_player.gd,
panel_content.gd, grid_map.gd, api_client.gd, game_commands.gd, map_viewer.gd;
assets/ui/*.png e ASSET_SOURCES.md; tools/serve_preview.py;
tests/ui_contract_smoke.gd, dorn_persistence.gd, playable_browser.cjs,
create_fixture.py, run_browser.py, browser_smoke.cjs; README e este relatório.
