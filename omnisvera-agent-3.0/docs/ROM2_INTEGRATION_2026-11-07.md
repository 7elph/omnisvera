# ROM2 no Companion 3.0 — 07/11/2026

## Entrega ativada

Terreno local convertido (80 x 80 células) renderizado como apresentação principal do Godot, preservando tiles, relevo e colocações gráficas do catálogo. A projeção é a nativa de 32 pixels com deslocamento vertical por altura, não uma conversão artificial para losangos 2:1.

Dorn e Morthak reutilizam os sprites existentes e a transformação do grid. Movimentação conectada continua usando os comandos autorizados do backend; nenhuma posição operacional foi migrada. A câmera fica limitada ao terreno. O HUD mantém apenas Arredores de Nimalis no canto superior esquerdo, remove controles de zoom/foco do registro e legenda de Dorn, filtra retratos pela presença real e adiciona o ícone do editor para o Mestre.

Editor inicial: seleção de tile, pintura, desfazer (64 alterações), salvar/reabrir rascunho local. Rascunho não é publicação compartilhada da campanha. Na Web, a persistência depende do armazenamento local do navegador.

## Arquivos

- scripts/main.gd, grid_map.gd, dorn.gd, hud_player.gd, navigation_panel.gd
- scripts/rom2_terrain.gd
- assets/ui/editor.svg
- export_presets.cfg e .gitignore
- tests/rom2_scene.gd, rom2_browser.cjs, run_browser.py, ui_contract_smoke.gd
- assets/rom2_local/: recursos locais selecionados, excluídos do Git.

## Evidências

- Godot nativo: ROM2_COMPANION_SCENE_PASS (coordenadas, destino de movimento, pintura/desfazer e entrada inválida).
- Godot: COMPANION3_UI_CONTRACT_PASS e COMPANION3_DORN_MOTION_PASS.
- Python: 9 testes de test_foundation.py passaram.
- Exportação Web concluída.
- Ensaio isolado: TEMP/omni-companion3-qazkgdri/rom2-report.json — PASS. Chrome desktop e mobile horizontal, leituras autorizadas de Dorn, gavetas de ficha/editor, movimento point-and-click aceito (HTTP 200), sem erros de script. Capturas inspecionadas visualmente. Não equivale a teste num celular físico em outra rede.
- Publicação: /companion3/ e /companion3/index.pck HTTP 200; SHA-256 do PCK público idêntico à exportação.
- Backend e servidor Web estavam parados. Inicializados em loopback 8787/8872, sem instalação de dependências ou mudança nos tokens.
- Backup: %LOCALAPPDATA%/Omnisvera/backups/rom2-web-20261107-155907/ (SQLite e Web anterior).
- Comparação de 12 tabelas de character/inventory/stock/ledger/token/spatial: nenhuma alteração após startup. Nenhum comando mutável enviado à campanha real.
- React e código backend não alterados neste corte; suas suítes completas não foram repetidas.

## Limites explícitos

- Esta apresentação ROM2 ainda não é um novo mapa persistido no catálogo operacional. O grid e os limites de movimento continuam os do mapa autorizado pelo backend, que pode ser menor que 80 x 80. Trocar de mapa não converte sua geometria/cenário automaticamente.
- Objetos são desenhados, mas sua colisão, navegação e oclusão com personagens não foram convertidas para regras do Companion. Luz e sombras originais não foram reconstruídas.
- Unidades, scripts e regras ROM2 não foram importados.
- Edição de objetos, sincronização e publicação de mapas editados pendentes.
- Retratos usam presença vinculada a character_id. Presença genérica de Mestre não é inventada como presença de Dorn; representação do personagem sob controle do Mestre ainda requer um contrato explícito de presença/controle.
- Fonte decorativa de ROM2 não foi extraída; usa tipografia atual do HUD.
- Sem commit ou push. Assets originais do pen drive não foram modificados.

## Continuação — movimento no cenário inteiro

Ativado cenário próprio Arredores de Nimalis, id map:fdba4a6d68c94b66, grid autoritativo 80×80 e células de 1 m. Dorn, Morthak, Vezemir e Raziel estão vinculados pelas identidades existentes. A limitação anterior de 30×30 vinha do mapa operacional que estava sob o cenário visual. Esse limite foi resolvido para o novo cenário, sem redimensionar os mapas anteriores. A ressalva anterior sobre ausência de cadastro operacional não se aplica mais a Arredores de Nimalis.

Removido o texto de conexão bem-sucedida. Mensagens necessárias de erro/ação ficam junto ao registro à direita, sem aviso no canto inferior esquerdo.

Correção adicional: seleção de células usa a interseção exata com as arestas do terreno. O teste de 6.400 centros falhava em uma célula com o cálculo iterativo antigo; passou com zero falhas após a correção.

Validação: ui_contract_smoke e dorn_motion_contract PASS; rom2_full_grid PASS (6.400 células); ensaio Web isolado PASS em TEMP/omni-companion3-umphc99p. O ensaio cadastra um cenário descartável completo e clica além da coluna 70, validando HTTP 200 e token de Dorn no comando. Desktop e mobile horizontal capturados e inspecionados. Nenhum movimento de teste enviado aos personagens reais.

Arquivos adicionais: tools/prepare_rom2_map.py (usa contratos autenticados existentes, recusa combate ativo, reutiliza cenário por título e preserva pins existentes), tests/export_rom2_preview.gd, tests/rom2_full_grid.gd; ajustes em tests/run_browser.py, rom2_browser.cjs, scripts/main.gd e rom2_terrain.gd.

Backup antes da ativação: %LOCALAPPDATA%/Omnisvera/backups/rom2-full-map-20261107-161435/. Comparação das 17 tabelas de personagens, inventário e comércio: nenhuma alteração. Cadastro de mapa/pins e sua auditoria foram alterações intencionais. Backend não reiniciado neste ajuste; exportação Web substituída após validação. Sem commit/push.

Colisão de objetos, navegação por obstáculos, sombras/oclusão e editor compartilhado continuam pendentes. O movimento em combate continua obedecendo aos custos e turnos do backend.
