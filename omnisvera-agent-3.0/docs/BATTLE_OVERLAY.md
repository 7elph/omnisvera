# Arena sobreposta — primeiro combate Dorn × Goblin

## Fluxo implementado

No Godot: Combate → escolher mapa disponível → preparar grade quando ausente → marcar participantes → adicionar Goblin do bestiário, se necessário → marcar Goblin → Iniciar batalha. A adição e a preparação são comandos explícitos do Mestre; apenas abrir a gaveta não altera fichas ou inicia um encontro.

O modo de batalha do backend existente registra a origem e leva os participantes à arena. A janela é uma camada sobre a exploração. Minimizar mantém o combate ativo; reabrir pela gaveta Combate. Movimentação e ataque usam posição, versão do grid, orçamento e turno do servidor. O atacante é o participante do turno atual; jogadores não ganham controle do Goblin. Seu turno é operado pelo Mestre neste corte, sem IA autônoma.

Atacar arma a seleção de alvo; clicar no alvo abre confirmação. Após confirmar o alvo, resolve e confirma o resultado no servidor automaticamente, sem uma segunda etapa de confirmação do dano. O resultado resumido aparece na arena e o backend mantém o ledger. Atalhos desktop: A para selecionar ataque; espaço para passar turno. Rodinha amplia a arena, botão direito/meio arrasta. Toque seleciona células/alvos no celular.

O mapa da arena usa a imagem autorizada do catálogo, com projeção de células sobre a imagem e posições separadas por mapa. Não foi reinterpretado como tiles ROM2; o mundo ROM2 de exploração continua por baixo. Escala gráfica e limites do mapa não substituem células de 1 m e movimento autorizado.

Ao encerrar pelo Mestre, o backend restaura o mapa e as posições de exploração, preservando consequências nos PV e recursos. O cliente reabre a exploração. Uma resolução arena-attack pendente pode ser retomada após reload apenas se seu combat_turn corresponder exatamente ao encontro/turno atual. Outros ataques pendentes não são confirmados automaticamente.

## Arte

Dorn reutiliza idle e caminhadas. Como não há spritesheet específica de ataque básico neste corte, usa um pequeno movimento visual da pose existente; isso não é apresentado como novos quadros gerados. Goblin usa frames extraídos do arquivo original ROM2, com proveniência no manifesto local e FPS 10 de apresentação (timing original ainda não certificado). Ataque e morte do Goblin usam frames existentes. Outros personagens/criaturas não recebem o sprite de Dorn como substituto.

## Arquivos

- scripts/battle_overlay.gd: janela, mapa, sprites, alvos, resultado, minimizar, zoom e pan.
- scripts/arena_projection.gd: projeção visual de células na arena.
- scripts/main.gd: preparação, transporte de comandos, lifecycle da arena, erro visível e retomada do ataque pendente.
- scripts/dorn.gd: manter o último quadro de morte quando a animação existe.
- tools/serve_preview.py: somente rotas existentes de combate, confirmação, catálogo e configuração de grade adicionadas à lista explícita.
- assets/rom2_local/goblin.json e goblin.png: arte local ignorada pelo Git.
- tests/battle_overlay.gd, arena_browser.cjs e run_browser.py: testes nativos e ensaio isolado.

Nenhuma mudança no código backend ou React. Suas suítes completas não foram repetidas; foram rodados os checks direcionados do backend já existente.

## Evidência

- 14 testes de test_battle_mode e test_battlefield_extensions PASS, SQLite temporário.
- 9 testes de fundação Python PASS, incluindo proteção do proxy.
- COMPANION3_BATTLE_OVERLAY_PASS: abertura, atores, preservação da câmera de exploração, minimizar sem encerrar, permissão, encerramento e filtro de ataque pendente por turno.
- COMPANION3_GM_SESSION_CONTROLS_PASS e COMPANION3_DORN_MOTION_PASS.
- Ensaios Web intermediários PASS: TEMP/omni-companion3-iemg8lj0 e jo7tuvw5, com mover/atacar Dorn, atacar Goblin, negar controle ao jogador e restaurar a posição original. A captura mobile do segundo usa Morthak fora do encontro e, corretamente, não mostra a arena; não certifica arena mobile. Ensaio final usa Mestre mobile e inclui reload de golpe pendente; resultado final abaixo.

Todos os comandos mutáveis de ensaio usam banco e Vault sintéticos. Nenhum combate de teste foi iniciado na campanha real. No Goblin sintético foram usados 100 PV para permitir testar os dois turnos; a criação real usa os PV do bestiário, sem essa alteração de ensaio.

## Limites

- Primeiro corte Dorn/Goblin; seleção genérica de participantes existe, mas as demais aparências e ações não foram integradas nesta janela.
- Guarda, Relâmpago e outras magias não ganharam controles na arena neste corte; continuam na fila.
- IA autônoma, vitória automática, recompensas/loot visuais e todos os estados de animação ainda pendentes.
- Fonte de dados continua o Companion/Old Dragon. Nenhuma fórmula ROM2 foi introduzida no combate da campanha.
- Rede local e emulação mobile não equivalem a validação de mesa em redes distintas/celular físico.
- Não houve commit ou push.
