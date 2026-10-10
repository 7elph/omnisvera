# Grid espacial — primeiro corte

## Modelo e uso

O mapa existente continua sendo a entidade principal. `session_workspace_map_grids`
adiciona grid quadrado, colunas/linhas, metros por célula, origem X/Y em **percentuais
da superfície da imagem**, política de distância e versão. A imagem não cria regras.

`session_workspace_entity_positions` referencia `(map_id, token_id)` e armazena
`cell_x/cell_y` (índices a partir de zero), footprint e versão. O token nativo já
identifica personagem/NPC/invocação: não existe um segundo catálogo de entidades.
Footprint inicial 1×1. Sem colisões entre tokens neste corte; sobreposição é permitida.

Na Mesa/Mapas, o Mestre abre **Grid … / Configurar grid lógico** e ajusta dimensões,
escala e origem, fora de combate. No mapa, selecione uma entidade e arraste ou use
as setas de uma célula. **Ficha da entidade** oferece acesso sem depender de acertar
um pin pequeno no celular. Fora de combate, só o Mestre reposiciona; em combate,
só a entidade do turno se move (jogador controla apenas seu personagem/invocação).

## Pixel versus célula

O centro visual é `origem + (célula + footprint/2) × (100-origem)/dimensão`.
Resize/zoom muda a projeção, nunca a célula. O stage acompanha as proporções da
imagem, evitando letterbox entre imagem e overlays. Ordem: imagem → grid → fog → pins.
O fog continua independente, no formato nativo, com filtragem de privacidade existente.

Mapas sem grid conservam pins percentuais fora do combate. Configuração inicial
adapta percentuais para a célula mais próxima por contenção (floor + clamp), sem
apagar os percentuais originais. Depois de um movimento confirmado, latitude/longitude
viram projeção de compatibilidade, não autoridade. Pins de localização permanecem
anotações visuais. Inserção/transferência de pins combatentes cria posições via triggers;
retorno a um mapa conserva suas células anteriores. Nova escala não pode invalidar
footprints existentes nem ser alterada durante combate.

Os seis mapas S7 registrados recebem 32×24 e **1,5 m/célula**, seguindo os layouts
nativos já preparados; nenhum outro mapa é migrado automaticamente. Imagem, zonas
e fog não são substituídos. Grades pintadas na arte não são inferidas automaticamente:
calibre dimensões/origem se a arte não coincidir. Inicialização adia um mapa com combate
ativo em vez de modificar sua escala durante a mesa.

## Comandos, turnos e distância

`POST /workspace/maps/{map_id}/grid`: Mestre, configuração com expected_version.
`POST /workspace/maps/{map_id}/move`: token_id, request_id, mode, path de células,
expected_position_version, expected_grid_version e expected_combat_version.
`GET /workspace/maps/{map_id}/distance?token_a=…&token_b=…`: cells/meters, respeitando
visibilidade. Distância entre âncoras, não entre bordas de criaturas grandes.

COMBAT_MOVE valida mapa/controle/turno/HP, origem do caminho, passos adjacentes,
limites e metros disponíveis. Caminho simples no frontend; nenhum pathfinding.
GM_REPOSITION, fora de combate, pode atravessar qualquer distância sem gasto.
Versões rejeitam concorrência obsoleta. Retry com mesmo ID/payload devolve o mesmo
recibo; payload diferente com ID reutilizado é rejeitado. Falha de confirmação na UI
mantém um botão para reenviar **o mesmo** comando. Sem atualização visual definitiva
antes da resposta, e pointercancel não confirma movimento.

Deslocamento usa `definition.movement` efetivo da ficha (incluindo Velocidade).
NPC/invocação usa `sheet.movement`: se ausente, é necessário cadastrar no editor
nativo de NPC/pin; não há velocidade inventada nem herdada silenciosamente do invocador.
`encounter.movement` guarda turn_key, budget_m e spent_m, no combate existente.
Nova sequência de turno reinicia o gasto logicamente; iniciativa preserva o gasto.
Não consome ação principal. Ex.: Dorn com 9 m em mapa de 1,5 m dispõe de seis passos
ortogonais; outro mapa usa sua própria escala.

Não foi encontrada política de diagonal nos módulos/regras locais consultados.
**Provisória, não canon:** Chebyshev (máximo de dx/dy), diagonal custa uma célula.
Alternativa por mapa: Manhattan (dx+dy), diagonal custa duas. O caminho soma custos
de cada passo, evitando ignorar desvios. Alterar a política exige validação da mesa.

Posição, gasto, recibo e ledger são uma transação SQLite. Ledger alimenta o watcher
e websocket já existentes (`session_changed`, ledger_id). Caminhos de mapas privados,
pins ocultos ou que cruzem fog oculto são auditados só para o Mestre. A narrativa mostra
nome/deslocamento, não JSON. Orçamento de participante oculto não é exposto ao jogador.

## Extensões e exclusões

Serviço de validação recebe caminho e grid, sem obstáculos gravados na imagem.
Próximo corte pode adicionar MapWall com segmentos x1/y1/x2/y2 e flags separadas
blocks_movement/blocks_sight, consultados antes de persistir. Grid e walls complementares.
Ainda não há walls, portas, LOS, iluminação, terreno, cobertura, altura, oportunidades,
reações, interrupções, áreas/templates, visão individual ou pathfinding A*.

## Referências conceituais

Somente documentação/README; **nenhum código externo copiado**:

- [Foundry Scenes](https://foundryvtt.com/article/scenes/), [Tokens](https://foundryvtt.com/article/tokens/) e [Walls](https://foundryvtt.com/article/walls/): cena, escala e restrições separadas.
- [Owlbear Scene Grid](https://docs.owlbear.rodeo/extensions/apis/scene/grid/) e [alinhamento](https://docs.owlbear.rodeo/docs/aligning-a-map/): escala/origem independentes da arte.
- [MapTool README](https://github.com/RPTools/maptool): referência de VTT open-source (AGPL-3.0); sem reutilização de código/licenciamento derivado neste corte.

## Verificação reproduzível

Backend: `python -m unittest discover -s backend -p "test_*.py"`.
Frontend: `node --test tests/*.test.cjs`, `npx --no-install tsc --noEmit`, `npm run build`.
`test_spatial_grid.py` cobre serviço, autorização HTTP, persistência, turnos, ledger,
retry concorrente, distância, fog, adaptação S7, triggers e bloqueio do endpoint visual.

Smoke: preparar SQLite temporário com `backend/scripts/cf01_probe.py prepare`, servir
somente loopback 8871, executar `frontend/tests/spatial-grid-smoke.cjs` com Playwright.
Usa fichas copiadas e tokens de ensaio. A mídia do banco copiado não está no vault
temporário: o smoke substitui suas respostas por imagem funcional 4:3, sem gerar arte.
Dois browsers locais não comprovam mesa real em redes diferentes.

Validação deste corte: 468 testes backend, 211 frontend, typecheck e build passaram.
Checkpoint isolado também passou em 16 testes backend do grid, 7 frontend, typecheck
e build. Smoke HTTP/browser: seis mapas, três personagens + NPC, arrasto, reload,
realtime entre dois clientes locais, zoom/seleção/setas mobile e rejeição por orçamento.
Mobile é viewport touch emulada, não telefone físico. Build mantém aviso de chunks grandes.

Os seis grids operacionais foram configurados com backup SQLite e comparação dos
dados nativos preservados. O backend 8787 não foi reiniciado neste corte: carregar
as rotas novas exige reinício controlado do backend, preservando o banco existente.
