# Sprite Studio — primeira versão

## Investigação verificada

Leitura dos arquivos reais, sem instalar os aplicativos ou copiar seus algoritmos.
As referências são conceitos; seus contratos de pets não são regras do VTT.

| Referência e revisão consultada | Evidência no código | Aplicação independente |
|---|---|---|
| [LibreSprite](https://github.com/LibreSprite/LibreSprite/tree/fd0b7fdaf0f620a2510d90bda4221c3f7dc2e7b5) | `src/doc/sprite.h`: camadas, paletas, frames, duração e cor transparente; `cel.h`: imagem/posição por frame; `image_impl.h`: pixels tipados; `mask.h`: seleção | Atlas RGBA + retângulos de frames, sem importar seu modelo de documentos |
| Mesmo projeto | `src/app/ui/timeline.cpp`: seleção de camadas/frames e controles de onion skin; `src/render/render.cpp`: composição, mistura/paleta e onion skin | Reprodução com relógio compartilhado; camadas/onion skin ficam para evolução |
| Mesmo projeto | `src/app/tools/ink.h` e `controller.h`: pintura por scanlines e controle de entrada; `src/app/file/png_format.cpp`: PNG, paleta e alpha | Edição inicial de recorte/alinhamento, não uma cópia do editor de pintura |
| [Hatch Pet](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/hatch-pet) | `SKILL.md`: referência canônica, geração por estado e QA; `extract_strip_frames.py`: chroma, componentes conexos, slots estáveis e ajuste à célula; `compose_atlas.py`: composição RGBA | Separar produção de arte, preparação de atlas e reprodução |
| Mesmo pacote | `validate_atlas.py`: alpha, dimensões, células vazias/resíduo RGB; `render_animation_previews.py`: prévias animadas por duração; `qa-rubric.md`: poses, alinhamento e consistência | Validação estrutural no backend + inspeção visual; PNGs externos importáveis |

O contrato Hatch é específico de pets (`192×208` por célula e estados próprios).
Ele **não é uma API pública de geração de imagens**, nem um motor de VTT. Não
adotamos suas dimensões/estados obrigatórios, geradores, empacotamento ou scripts.

### Licenças e dependências

- [LibreSprite LICENSE](https://github.com/LibreSprite/LibreSprite/blob/fd0b7fdaf0f620a2510d90bda4221c3f7dc2e7b5/LICENSE.txt): GPL-2.0. As ferramentas/UI consultadas têm cabeçalhos GPL; `src/doc/LICENSE.txt` e `src/render/LICENSE.txt` são MIT. Não presumimos uma licença única para todos os componentes.
- [Hatch Pet LICENSE](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/hatch-pet/LICENSE.txt): Apache-2.0.
- Nenhum código desses projetos foi incorporado. Não adicionamos SDL, C++, WASM, processamento por componentes conexos ou dependência de serviços de pets. Implementação original em React/Canvas, FastAPI/SQLite e Pillow **já existente**.

## Integração com o Companion

`SessionWorkspace.tsx` renderiza imagem de fundo, grid/fog/áreas e pins. Cada pin
continua sendo um `session_workspace_tokens`, com posição de combate em
`session_workspace_entity_positions`. `spatial_grid.move_entity` e as rotas
nativas continuam validando movimento, permissões, versões e orçamento.
O combate/iniciativa continua em `combat_effects`, fichas em `character_play`,
realtime no observador de `session_ledger`. Nada disso foi duplicado.

Os mapas incluem ilustrações de cidade/exploração e arenas; não há perspectiva
isométrica universal declarada. `up/down/left/right` são direções da superfície
do mapa. Ausência de uma direção usa `idle`, sem inventar vista lateral/espelhada.

## Responsabilidades e persistência

- `backend/app/sprite_studio.py`: biblioteca, validação, associação, exportação e rotas.
- `frontend/src/components/SpriteStudio.tsx`: importação/recortes, seleção ordenada de quadros, duplicação, alinhamento, escala, estados, FPS/loop, prévia e vínculo.
- `frontend/src/spriteAnimation.ts`: seleção temporal de frames, direções, cache limitado e relógio compartilhado.
- `frontend/src/components/AnimatedSprite.tsx`: apresentação, fallback e interpolação visual de movimento **já confirmado**.
- `spriteApi.ts`: transporte autenticado; utiliza a autenticação existente.

Tabelas aditivas no SQLite atual: `sprite_assets` (PNG e metadados juntos),
`sprite_bindings` (referência a personagem ou pin existente) e `sprite_commands`
(recibos persistentes para retry). Não há nova entidade de combate. Vínculo de
personagem acompanha seus pins em outros mapas; um vínculo específico de pin
tem precedência. Desvincular restaura imediatamente o visual estático.

Salvar/substituir preserva o ID e exige a versão esperada. O novo PNG precisa
comportar todos os recortes, ou nada é salvo. Imagem e JSON são transacionais.
Assets privados não são enviados aos jogadores: apenas pins já filtrados por
visibilidade/fog recebem o descritor visual; download exige autenticação e
vínculo em pin visível no mapa público atual. A biblioteca/editor/exportação são
exclusivos do Mestre. Alterações geram ledger privado e o realtime nativo avisa
os clientes para relerem o estado público filtrado.

### Formato v1

```json
{
  "schema_version": 1,
  "canvas_width": 128,
  "canvas_height": 168,
  "pivot": [0.5, 0.5],
  "scale": 1,
  "frames": [{"x": 0, "y": 0, "w": 128, "h": 168,
              "offset_x": 0, "offset_y": 0, "scale": 1}],
  "animations": {
    "idle": {"frames": [0], "fps": 4, "loop": true, "direction": "down"}
  }
}
```

`durations_ms`, opcional na animação, substitui FPS por durações individuais.
O pivô normalizado é relativo ao canvas visual e cada recorte; offsets usam
pixels desse canvas. `scale` não aumenta footprint, alcance ou colisão.
`idle`, quatro caminhadas, `attack`, `cast`, `hit`, `death` e novos nomes são
aceitos. Só uma animação é obrigatória; fallback: estado → idle → primeiro estado.

Limites: PNG único (APNG rejeitado), 8 MB, lado até 4096 px, 8 megapixels,
256 quadros e 32 animações. PNG é decodificado/regravado em RGBA, sem carregar
metadados externos. Exportação ZIP contém `sheet.png` e `sprite.json`.

## Uso: Dorn no mapa

1. Mestre → **Mapas → Sprite Studio → Exemplo de Dorn**.
2. O exemplo já tem idle e walk_down. Para importar outro PNG, escolha arquivo,
   informe largura/altura e **Separar quadros**. Clique nos números na ordem
   desejada e use a seleção na animação escolhida. Ajuste FPS/loop e veja a prévia.
3. **Salvar sprite**, escolher Dorn em **Associar sprite**, **Associar**.
4. No mapa, Dorn reproduz idle. Arraste como antes; somente a confirmação
   nativa dispara caminhada/interpolação por 600 ms e retorno a idle.
5. Recarregar mantém associação. **Usar token estático** desfaz o vínculo.

Arte original encontrada: `zz_media/characters/unidade.png`, referenciada na
nota de Dorn. Não alteramos a nota nem a imagem. O exemplo em
`frontend/public/companion-assets/sprites/` é arte de teste derivada por
`imagegen` embutido, preservando pedra/bronze/runas/núcleo azul. O atlas foi
recortado, reduzido com escala comum e alinhado pela base. Não são poses CSS.
Somente a caminhada frontal possui arte; demais direções caem em idle.

## Fronteira para geração assistida

O MVP importa resultados externos em PNG; nenhum provedor é chamado pelo
editor. A integração futura pode usar a oficina existente com um briefing
versionado contendo `reference_assets`, `requested_states`, `frame_size`,
`directions`, `source_hash` e `style`. O resultado deve retornar PNG + metadados
v1, passar pela mesma validação e revisão antes de associar. Não executar texto
do modelo ou dar aprovação automática. Não existe promessa de API ChatGPT/Hatch.

## Evolução, sem implementação neste corte

Pintura/borracha, paletas editáveis, camadas, onion skin, seleção livre por
arrasto, timeline com drag, importação de projeto JSON, GIF/APNG exportável,
vistas adicionais e gatilhos de ataque/cast/hit/death. O modelo aceita os estados,
mas este corte conecta automaticamente **idle e caminhada**. A interpolação
liga os pontos confirmados; não reproduz cada célula de trajetos longos.
Biblioteca compartilhada entre campanhas e exportação para o jogo digital são
futuras; sem acoplamento ao Godot neste corte.

## Validação

- Backend global: **1721 executados**, sem erros de execução, um skip. A primeira rodada encontrou uma única falha: a asserção do schema MCP ainda listava os lotes anteriores. A lista foi atualizada para incluir Sprite Studio; reexecução de **35 testes** de sprites/lotes passou. Não houve uma segunda rodada global após essa atualização do teste.
- Backend específico: **7/7** casos de sprites, incluindo PNG inválido, limites, recortes, referência ausente, alpha, concorrência de edição, privacidade, retry, ledger, associação/exportação e ausência de mutação das fichas.
- Frontend global: **486/486**. Após acrescentar a limitação do cache por pixels decodificados, os **7 testes de animação/cache** passaram novamente. Cache: até 24 entradas e aproximadamente 32 MB de pixels armazenados; imagens ainda em uso por renderizadores têm seu próprio tempo de vida.
- Typecheck e build finais passaram. O Vite mantém o aviso de chunks grandes do aplicativo; não foi criada dependência pesada.
- Ensaio nativo isolado `omni-sprite-studio-v4`: quatro ataques API **PASS**, `report.ui_smoke.status=PASS`. PNG por seletor de arquivo, inválido rejeitado, recorte/sequência/FPS, associação, animação, caminhada confirmada/idle, reload, token estático, falha de download e desktop/mobile/zoom foram exercitados. Capturas foram abertas e aceitas explicitamente; isso não certifica toda a ficha ou redes móveis externas.
- Reinício real do processo da fixture: **PASS**, mantendo imagem, associação e célula de Dorn. Não foi apenas uma recarga da página.
- O MCP padrão atingiu o limite de 100 trabalhos históricos. Nada foi excluído nem o limite aumentado: o ensaio utilizou o mesmo executor nativo via CLI, com fixture TEMP e trava de memória. O Chrome existente foi usado headless com perfil descartável, sem instalar navegador adicional.
- Ativação: backend operacional religado, `/health` e `/gm/sprites` **200**, HTTPS público **200**. Backup em `C:\Users\delib\OmnisveraBackups\sprite-studio-20261029-212619`. Hashes de `character_states`, `player_inventory`, `combat_effect_clock`, `session_workspace_state` e arquivo de autenticação foram preservados.

As associações de teste ficaram somente na fixture. Na mesa, o Mestre pode
carregar o exemplo pronto e associá-lo, sem precisar configurar seus frames.

MCP: `ui_suite: "sprite_studio"`, `ui:true`, quatro atores. Evidências desta
execução e aceitação visual estão em
`C:\Users\delib\.codex\visualizations\2026\08\21\01a0264b-3fde-70c2-96f4-88b90861f3ea\sprite-studio`.

## Arquivos deste corte

- Backend: `app/sprite_studio.py`, `test_sprite_studio.py`; integração mínima em `app/main.py` e `app/session_workspace.py`.
- Ensaio: `scripts/run_sheet_test.py`, `scripts/companion_test_mcp.py`, `test_sheet_runner_batches.py`.
- Frontend: `src/spriteAnimation.ts`, `src/spriteApi.ts`, `src/components/{SpriteStudio,AnimatedSprite}.tsx`, `src/components/spriteStudio.css`; extensão de `src/api.ts` e do renderizador em `src/pages/SessionWorkspace.tsx`.
- Testes: `frontend/tests/sprite-animation.test.cjs`, `sprite-studio-smoke.cjs`.
- Arte: `frontend/public/companion-assets/sprites/{dorn-demo-v1.png,dorn-front-demo-v1.png,dorn-demo-v1.json,README.md}`.
- Documentação: este documento, `AI_TEST_TOOLS.md`, `CURRENT_COMPANION_CODE.md`.

Worktree misto anterior preservado. Sem staging, commit, push ou merge.
