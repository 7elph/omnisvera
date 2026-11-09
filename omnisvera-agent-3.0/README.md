# Omnisvera Companion 3.0

Cliente Godot 4.7.1, Compatibility, com exportação Web sem threads.
A cena principal é o aplicativo. O backend FastAPI continua autoritativo.

## Versão no GitHub

Use o backend da pasta irmã `omnisvera-agent/` no mesmo checkout. Os cortes
mais recentes incluem arena isométrica, ações e iniciativa, dados e pedidos
de rolagem, espólio, comércio, Biblioteca do Mestre e preparação de sessões.
O Estúdio de preparação salva rascunhos antes de o Mestre aplicar o conteúdo.
A geração depende de provedores configurados no servidor. Ao solicitar a
geração, o resumo cadastrado no Estúdio entra no contexto enviado ao modelo.

O repositório inclui as artes do Companion. O cenário e os sprites extraídos
do Rage of Mages II ficam em `assets/rom2_local/` na instalação local. Sem
esses arquivos, a prévia usa o piso do Godot, os tokens disponíveis e a arte
original da cidade. Abra `project.godot` no Godot para executar a prévia
nativa ou instale os templates Web da mesma versão para usar o lançador.

## Executar no Windows

Com o backend habitual funcionando em 8787, execute nesta pasta.

~~~powershell
.\start_preview.ps1
~~~

Abra http://127.0.0.1:8872/ e informe seu acesso habitual.
O endereço é uma prévia local. O Companion publicado continua separado.
O botão “Explorar prévia local” permite ver a arte e a câmera sem conectar.

O lançador aceita outro executável, porta e backend local.

~~~powershell
.\start_preview.ps1 -GodotExecutable 'C:\caminho\Godot_console.exe' -Port 8872
.\start_preview.ps1 -SkipBuild
~~~

Godot portátil validado neste computador em
%LOCALAPPDATA%\Omnisvera\tools\Godot-4.7.1.
Os templates correspondentes já estavam instalados em
%APPDATA%\Godot\export_templates\4.7.1.stable.
Instalações anteriores foram preservadas. MCP Godot está desativado na
configuração atual. Esta versão utiliza CLI e recursos nativos.

## Primeiro corte de 06/11 — registro histórico

- Piso isométrico procedural de validação, projeção de células do backend,
  zoom, pan por arraste, câmera WASD e controles touch.
- Dorn com as três folhas originais entregues em 06/11, intactas.
  56 quadros organizados em idle, quatro caminhadas, guarda e conjuração.
- Interpolação visual de posições confirmadas pelo backend.
- Ficha nativa, consultas de ataques, habilidades, inventário, combate e registro.
- Navegação por oito ícones, painéis temporários e seleção de personagem.
- Presença baseada no heartbeat nativo. Retratos ainda usam iniciais como
  fallback, com a arte de Dorn já disponível.
- Mensagens pelo endpoint existente e histórico legível do ledger.
- Carregamento, erros, rejeição de credenciais e proteção contra respostas antigas.
- Exportação Web executada e testada em 1440×900 e 390×844.

Ataques e magias exibidos são consultas. Os comandos de combate, o arraste
autoritativo e as ferramentas de edição serão conectados no próximo corte.
Guarda e conjuração têm quadros preparados, sem disparo por regras conectado.

A prévia desconectada deixa Dorn caminhar visualmente. A conexão muda esse
comportamento. No modo conectado, a posição vem exclusivamente do backend.
As ilustrações atuais da campanha não foram convertidas em mapas isométricos.
A projeção das células preserva seus dados lógicos.

## Autenticação e transporte

O cliente usa X-Omnisvera-Token. Na Web, o backend tem a mesma origem,
por meio de tools/serve_preview.py. A prévia usa somente o backend local
explicitamente configurado. Tokens podem entrar pelo campo ou fragmento
#token=..., removido imediatamente da barra. Não há token de servidor
incluído no export. O fragmento não é salvo automaticamente.

O proxy encaminha uma lista explícita de leituras e comandos. Consultas de
fichas forçam `read_only=true`. Decisões Mestre/Jogador vêm de `/health`, e
a visibilidade vem das respostas autorizadas do backend.

## Estrutura

| Arquivo | Responsabilidade |
|---|---|
| scenes/main.tscn | Cena persistente com mapa, Dorn, câmera e CanvasLayer |
| scripts/main.gd | HUD, seleção, painéis e coordenação das leituras |
| scripts/grid_map.gd | Projeção isométrica e desenho do grid |
| scripts/dorn.gd | SpriteFrames e interpolação de posições |
| scripts/api_client.gd | HTTP serializado, timeout e isolamento por credencial |
| scripts/navigation_panel.gd | Ícones flutuantes |
| scripts/hud_player.gd | Participantes e presença |
| assets/sprites/dorn.json | Recortes, estados, FPS e hashes dos originais |
| tools/import_dorn.py | Importação intacta e extração de retângulos pelo alpha |
| tools/serve_preview.py | HTTP estático e proxy limitado |
| export_presets.cfg, index.html | Export Web e shell de carregamento |

## Testar

Use o Python já disponível no Companion, com Pillow para validar os assets.

~~~powershell
..\omnisvera-agent\.venv-observer\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
& "$env:LOCALAPPDATA\Omnisvera\tools\Godot-4.7.1\Godot_v4.7.1-stable_win64_console.exe" --headless --path . --quit-after 120 -- --smoke-test
..\omnisvera-agent\.venv-observer\Scripts\python.exe tests\run_browser.py
~~~

O ensaio Web cria um banco e um Vault sintéticos em TEMP, inicia backend 8891
e prévia 8892, usa Chrome instalado e encerra seus próprios processos.
Exige uma exportação atualizada e Playwright disponível no runtime de QA.
O relatório, logs e capturas ficam no diretório TEMP informado ao terminar.

## Limites registrados no primeiro corte

- Piso visual de validação, ainda sem composição de cenários e obstáculos.
- Renderização inicial de até 96×96 células.
- Somente Dorn tem sprite animado neste corte. Outras entidades têm marcadores.
- Caminhada recebida é interpolada pelo destino, sem reprodução integral do path.
- Execução de ataques/magias e comandos de movimento ainda pertencem ao legado.
- Export Web bruto com aproximadamente 43 MB. Compressão de entrega será necessária
  antes de publicação remota.
- Ensaio local em duas identidades, com emulação mobile. Mesa em redes distintas
  e desempenho em celular físico continuam sem comprovação.

As evidências e a situação da suíte anterior estão em
docs/VALIDATION_2026-11-06.md.

## Celular na horizontal

A Web usa layout horizontal. Em celular na vertical, uma camada pede para girar
o aparelho. “Tela cheia horizontal” solicita fullscreen e bloqueio landscape
mediante toque; navegadores sem essa API continuam com rotação física.
O HUD se ajusta à altura disponível, e girar não reinicia a cena nem a câmera.

Validação de 06/11: quatro testes de orientação em Node, cinco testes Python,
smoke nativo em 844×390, 740×360 e 640×320, exportação Web e ensaio Chrome
isolado completos PASS. Capturas e relatório em TEMP/omni-companion3-o6mp94rm.
O navegador emulado testou vertical → horizontal → vertical → horizontal,
reabertura da ficha, identidade, privacidade e dados descartáveis.
Bloqueio físico de orientação em aparelho real ainda depende do navegador.

Arquivos deste ajuste: index.html, project.godot, scripts/main.gd,
scripts/navigation_panel.gd, tests/orientation.test.cjs,
tests/browser_smoke.cjs, tests/run_browser.py e este README.
Backend e frontend React não foram alterados nem reiniciados neste ajuste;
as suítes desses módulos não foram repetidas.

## Gavetas e biblioteca conectada

A prévia pública em https://desktop-p30ui0j.taildecf09.ts.net/companion3/
agora usa gavetas à esquerda, presença real, imagens autenticadas, inventário
visual, mapas/pins existentes e o histórico autorizado das sessões.
Entrega, arquivos, evidências e limites em docs/UI_DRAWERS_2026-11-06.md.

## Corte jogável de Dorn

Fichas acessíveis mesmo offline, personagem controlado separado da presença,
PNG maior/centralizado, idle persistente, clique para mover com confirmação
do servidor e Guarda/Relâmpago reais. Uso e limites em
docs/PLAYABLE_CUT_2026-11-06.md. Ensaio: tests/run_browser.py --suite playable.

Ajustes de recorte/pivô, movimento constante por metro, escala das ações e
imagens do inventário: docs/DORN_MOTION_MEDIA_2026-11-06.md.

Morthak agora usa a folha enviada (idle + quatro caminhadas) no próprio token
e na prévia da ficha. Uso, arquivos e limites em docs/MORTHAK_SPRITE_2026-11-06.md.
Ensaio isolado: `tests/run_browser.py --suite morthak`.

Recuperação do login de Morthak e preparação do mapa público Earthropo:
docs/MORTHAK_LOGIN_RECOVERY_2026-11-06.md.
