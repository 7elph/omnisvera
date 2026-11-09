# Dorn: apoio dos pés, deslocamento e imagens — 06/11/2026

## Correções

- A folha original de movimento tem cinco faixas de desenho com espaçamentos
  diferentes. Dividir a altura por cinco incluía parte da direção seguinte
  nos quadros à esquerda e cortava a cabeça dos quadros à direita. Os limites
  agora vêm das faixas alfa reais.
- Cada quadro recebeu um pivô nas solas opacas. A altura física do corpo,
  excluindo a aura ciano, define uma escala constante por animação. Guarda e
  Relâmpago preservam a altura de Dorn; os efeitos ainda podem ultrapassá-la.
  Os três PNGs originais permanecem intactos, com SHA-256 verificado.
- O deslocamento visual percorre a rota confirmada pelo servidor, com 0,5 s
  por metro e interpolação linear em cada célula. A distância do clique não
  aumenta a velocidade. Atualizações repetidas não reiniciam o passo.
  Reconexão limpa a rota visual anterior. As regras continuam no backend.
- O carregador de mídia aceita as referências relativas, wiki-links,
  espaços e acentos já usados pelo Companion 2.0. Preserva autenticação por
  cabeçalho, rejeição de caminhos externos/traversal e limites de cache.
  Decodifica PNG/JPEG/WebP/SVG. Falhas tentam a próxima imagem e uma resposta
  antiga não pode substituir a imagem de uma vinculação mais recente.
- Inventário e equipamentos usam imagem própria, cover, ícone do catálogo
  existente e, por último, inventário genérico. O mapeamento de 80 ícones é
  extraído do TypeScript atual por `node tools/sync_icon_catalog.cjs`.
- Ficha projeta equipamentos e recursos autorizados. Guarda/Relâmpago usam
  suas imagens cadastradas, em vez de miniaturas do sprite de Dorn.

## Verificações

- RED observado nos testes de recorte esquerdo, velocidade constante e
  referências de mídia. Depois da correção: contratos nativos de movimento,
  mídia/UI e carregamento da cena PASS; persistência de idle após Guarda,
  conjuração e movimento PASS.
- Python `tests/test_foundation.py`: 8 testes PASS, incluindo hashes/alfa dos
  originais, recortes e proteção/autorização do proxy.
- Ensaio Web `tests/run_browser.py --suite playable`: base sintética TEMP,
  quatro atores, movimento Mestre/jogador, Guarda, Relâmpago com dano real no
  servidor de ensaio, item com imagem ausente e fallback, mapas/pins/sessões
  e proteção dos dados privados. Desktop 1440×900 e touch 844×390.
- Backend: 2.155 testes em 1.020,849 s, OK, um skip. Avisos existentes de
  depreciação e conexões SQLite não fechadas em testes permanecem no log.
- TypeScript e build React PASS; compilação em TEMP, sem substituir o legado.
- Exportação Godot Web Compatibility sem threads PASS.
- Ensaio final: `%TEMP%/omni-companion3-vg_tw8aa`, incluindo captura durante
  caminhada à esquerda. Capturas de movimento, escala das ações, inventário
  e ficha mobile inspecionadas explicitamente.
- Ativação: apenas `build/web/index.html` e `index.pck`, com cópias anteriores
  em TEMP. Backend 8787 e proxy 8872 preservados, sem reinício. Conferência
  HTTPS pública 844×390 PASS, sem erros de script nem comandos mutáveis;
  imagens de Guarda/Relâmpago, retrato, item e mapas responderam HTTP 200.
- Consulta operacional somente de leitura: 56 itens nas quatro fichas;
  22 imagens próprias, 19 ícones específicos do catálogo e 15 genéricos.
  Os quatro retratos e as 43 imagens cadastradas em habilidades responderam
  HTTP 200. Dezesseis habilidades ainda não têm arte própria cadastrada.

Evidências: `%TEMP%/companion3-dorn-media-20261106` (logs, exportação, auditoria
de mídia e recibo da ativação). Os diretórios individuais do ensaio ficam
registrados em `browser.log`. A captura pública usa somente leituras e
heartbeat, sem movimentos, compras, combate ou edição de fichas reais.

## Arquivos

`scripts/dorn.gd`, `main.gd`, `media_cache.gd`, `panel_content.gd`,
`ui_style.gd`, novo `icon_catalog.gd`; `tools/import_dorn.py`, novo
`sync_icon_catalog.cjs`; `assets/sprites/dorn.json`, novo
`assets/ui/item-icons.json`; `export_presets.cfg`; testes
`test_foundation.py`, novo `dorn_motion_contract.gd`, `ui_contract_smoke.gd`,
`create_fixture.py`, `playable_browser.cjs`; README e este relatório.

## Uso e limites

Recarregar `/companion3/` para receber o novo pacote. Ficha → Guarda ou
Relâmpago usa a entidade existente; “Testar” continua sendo uma prévia local
quando não houver pin. Os ensaios mutáveis nunca usam o banco operacional.

A correção não gera artes ausentes nem conclui a migração de todas as ações
e interfaces do Companion 2.0. O mapa ilustrado flutuante e o piso isométrico
continuam superfícies distintas. O ensaio mobile é emulado no Chrome;
desempenho e conexão em aparelho físico/rede móvel continuam dependentes de
validação real. Sem alterações de regras, canon, saldos ou inventários reais;
sem commit, push ou reinício do backend/OpenCode neste lote.
