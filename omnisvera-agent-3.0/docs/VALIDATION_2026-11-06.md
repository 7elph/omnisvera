# Companion 3.0 — diagnóstico e validação

## Estado recebido

Branch devin/create-omnisvera-class-standard.
HEAD a395934b791e1974886c5ff3364b602608dc86e5.
Checkout misto, com mudanças anteriores no Companion e no Vault, além do
projeto irmão omnisvera-agent-3.0 ainda não rastreado. O HEAD foi preservado.
Autoria individual das alterações locais não pode ser deduzida apenas pelo diff.

Encontrados os catálogos relatados, com 854 magias, 47 habilidades, 326 itens
de fonte e 255 monstros. Permanecem quatro magias com descrição vazia.
O catálogo normalizado atual contém 338 itens, incluindo entradas e variantes
já existentes antes deste corte. Conteúdo e regras não foram ampliados.

O projeto Godot recebido tinha seis scripts, uma cena, um HTML, configuração
sem seções válidas e um ícone contendo texto base64. A pasta assets estava
vazia. Havia scripts usados como textura, recursos de animação inválidos,
tipos ausentes, métodos de sinal incorretos, ausência de autenticação e URLs
/api/v1 incompatíveis com o backend real. O primeiro import do motor reproduziu
erro no PNG e falha de parsing em APIClient.

O projeto anterior OmnisveraGame foi localizado e sua configuração inspecionada.
O novo corte utiliza o projeto 3.0 recebido e suas responsabilidades originais.
Conectores Godot estavam desativados. CLI foi suficiente para validar.

## Implementação executada

Cena principal main.tscn executável em Godot 4.7.1 Compatibility.
Mapa isométrico procedural, projeção do grid autorizado, câmera, zoom, pan,
sprite animado, seleção e HUD nativo. Os painéis sobrepostos mantêm a cena e
a câmera. Ficha, ataques, habilidades, inventário, combate e registro podem
ser consultados. Execução de combate pelo Godot permanece no próximo corte.

As três imagens fornecidas em Desktop/Nova pasta foram copiadas intactas.
Manifesto versionado com SHA-256 e retângulos por alpha organiza 56 quadros
em idle, quatro caminhadas, guarda e conjuração. Somente Dorn tem sprite
animado. Outros participantes usam marcadores e iniciais como fallback visual.

A conexão usa o papel confirmado pelo servidor. A prévia desconectada permite
caminhada visual identificada. Conectado, o sprite interpola somente posições
recebidas do workspace. O renderizador não calcula dano, recursos ou turnos.

## Contratos integrados

| Contrato | Uso |
|---|---|
| GET /health | Autenticação, papel e identidade |
| GET /characters?read_only=true | Lista autorizada |
| GET /characters/{id}?read_only=true | Ficha, atributos, ataques e inventário |
| GET /workspace | Mapa, grid, tokens filtrados e presença |
| GET /workspace/ledger?limit=80 | Registro existente |
| GET /combat/effects | Consulta do combate |
| POST /workspace/heartbeat | Presença nativa |
| POST /workspace/messages | Mensagem no registro nativo |

Cliente HTTP serializado, deduplicação de leituras, timeout, cancelamento por
mudança de credencial e descarte de respostas de outra ficha. Escritas de
mensagem não são repetidas automaticamente após resposta incerta.

Shell Web consome o fragmento e o remove da barra. Token apenas em memória,
sem credencial de servidor incluída no export. O proxy local força leituras
de ficha não mutáveis e limita as escritas a presença e mensagem.

## Checks e resultados

| Verificação | Resultado |
|---|---|
| Godot import e parsing | PASS em 4.7.1 |
| Execução nativa headless | PASS, COMPANION3_NATIVE_SMOKE_PASS |
| Projeção célula ↔ posição, recursos e painéis | PASS no ensaio nativo |
| Testes de assets e proxy | 5/5 |
| Exportação Web Compatibility sem threads | PASS |
| Chrome desktop 1440×900 | PASS |
| Chrome touch emulado 390×844 | PASS |
| Dois clientes e backend FastAPI/SQLite sintético | PASS |
| Privacidade de ficha, NPC e ledger | PASS no escopo testado |
| Atualização autorizada de posição | PASS |
| Ficha refletindo PV 27 → 24 | PASS |
| Mensagem enviada pelo Godot | Uma entrega no ledger |
| Erros de script no navegador final | Zero |
| Suíte completa backend | 2.153 executados, 3 falhas de expectativa de contagem, 1 ignorado |
| Módulos backend afetados após correção das expectativas | 22/22 |
| Frontend legado, antes da manutenção | 539/541 |
| Frontend legado, após manutenção pontual | 542/542 |
| TypeScript legado | PASS |
| Build legado, saída separada em TEMP | PASS, aviso de chunks grandes |

As três expectativas backend usavam 336 e foram atualizadas para os 338 itens
já cadastrados, com verificação explícita das duas variantes de Bola de Cristal.
Os módulos afetados foram repetidos após a correção. A suíte completa não foi
repetida depois dessas mudanças exclusivamente em testes. O caso ignorado exige
criação de symlink indisponível neste Windows.

No legado, foi corrigido o bloqueio ao parar Tambores/Botas quando o consumível
do turno já foi usado. Um teste adicional garante que isso não libera outro
item. A expectativa do rótulo “Editar criatura” foi alinhada à UI existente.
Nenhum novo sistema de habilidades foi acrescentado ao React.

Os números históricos 665 e 42 não equivalem à suíte completa atual. O resultado
de 2.153 veio de descoberta completa de test_*.py em ambiente descartável.

## Evidências

Pasta de visualizações desta conversa, em
C:/Users/delib/.codex/visualizations/2026/08/21/01a0264b-3fde-70c2-96f4-88b90861f3ea.

- companion3-initial contém a cópia dos arquivos recebidos antes das alterações.
- companion3-browser-report.json registra o ensaio Web final.
- companion3-desktop.png e companion3-mobile.png foram inspecionados visualmente.
- companion3-native.log e companion3-export.log registram execução e export.
- foundation-companion3-backend.json e foundation-companion3-baseline-fixed.json.
- companion3-legacy-tests-final.log, companion3-legacy-tsc-final.log,
  companion3-legacy-build-final.log.

O ensaio Web final usou somente
C:/Users/delib/AppData/Local/Temp/omni-companion3-q89tvyrz.
Backend, prévia de QA e navegadores desse ensaio foram encerrados pelo runner.

## Arquivos deste corte

No projeto 3.0 foram corrigidos project.godot, scenes/main.tscn, index.html,
README.md e os seis scripts existentes. Foram acrescentados export_presets.cfg,
start_preview.ps1, .gitignore, os três PNGs originais e dorn.json, oito SVGs de
navegação, tools/import_dorn.py, tools/serve_preview.py,
tests/create_fixture.py, tests/run_browser.py, tests/browser_smoke.cjs e
tests/test_foundation.py. Sidecars de importação/UID foram produzidos pelo Godot.

No Companion legado, somente a manutenção descrita acima em
frontend/src/pages/SessionWorkspace.tsx,
frontend/tests/combat-controls.test.cjs,
frontend/tests/combat-integrity.test.cjs,
backend/test_catalog_readiness.py,
backend/test_hp_potion_pipeline.py,
e a referência em docs/CURRENT_COMPANION_CODE.md.
As alterações anteriores desses arquivos foram preservadas.

## Executar e inspecionar

Ver README.md e start_preview.ps1. Prévia local em http://127.0.0.1:8872/.
Para inspeção desconectada, use “Explorar prévia local”, clique no piso para
caminhar e use arraste, WASD e os controles de zoom.
Para fichas da campanha, é necessário o backend habitual em execução e o token
do usuário. O papel vem do servidor.

Na checagem operacional deste corte, 8787 e 8788 estavam sem resposta.
A prova de integração usa o backend nativo com fichas sintéticas.
Não foi acionado startup ou migração do banco operacional.

## Pendências e próximo corte

O piso é uma superfície de validação. Falta composição com tiles e cenário.
As artes de campanha existentes preservam sua perspectiva original. Não foram
reinterpretadas automaticamente como terrenos isométricos.

Faltam comandos autoritativos de movimento emitidos pelo Godot, seleção/execução
de ataques e magias, efeitos de combate, ferramentas do Mestre, retratos dos
outros personagens, WebSocket nativo e otimização da entrega remota.
O build bruto ocupa aproximadamente 43,8 MB. A renderização inicial limita o piso a
96×96 células. Interpolação usa o destino confirmado, sem reconstruir o path.

Próximo corte vertical recomendado é mover Dorn pelo próprio cliente com
request_id e versões do grid/posição/combate, validar orçamento no backend e
executar um ataque básico com confirmação e ledger. Depois, expandir os
mesmos contratos para outros atores e habilidades.

Os testes locais não certificam desempenho em celular físico ou uma mesa em
redes distintas. Não houve commit, push, merge ou substituição do publicado.

## Referências técnicas consultadas

- [Exportação Web oficial](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html)
- [HTTPRequest oficial](https://docs.godotengine.org/en/stable/classes/class_httprequest.html)
- [Release oficial 4.7.1](https://github.com/godotengine/godot/releases/tag/4.7.1-stable)
