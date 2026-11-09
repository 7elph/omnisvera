# Gavetas, presença, mapas e sessões — 06/11/2026

## Entrega

- Navegação à esquerda com imagens transparentes de 34 px e área de toque de
  48 × 46 px. TextureButton evita molduras do tema. A coluna permite rolagem
  nas telas em que os oito comandos do Mestre não cabem.
- Gavetas ancoradas em x=76, junto à navegação, sem reconstruir mapa ou câmera.
- Registro lateral removido: um ícone transparente permanece acima da mensagem.
- O título permanente do mapa/conexão foi retirado. Erros de conexão continuam
  tendo feedback visível.
- Presença usa somente online=true do snapshot nativo. Personagens offline
  saem dos retratos e do seletor de ficha. O Mestre tem identidade própria;
  o sprite de Dorn nunca substitui um retrato de jogador.
- Ficha usa retrato, identidade, atributos, defesas e campos narrativos
  autorizados da definição. Ataques/habilidades possuem cards com imagens e
  detalhes; inventário usa ícones/quantidades e contorno nos equipados.
- Mapas consulta /workspace/maps e /workspace?map_id=…; cada mapa abre uma
  janela com imagem real e pins clicáveis. Coordenadas continuam percentuais;
  não houve conversão da perspectiva da imagem nem mudança do grid lógico.
- Jogadores recebem apenas mapas/pins autorizados e fog de exploração/batalha.
  Suas miniaturas de biblioteca usam um ícone de mapa para não revelar áreas
  encobertas antes de consultar o fog correspondente. Mestre vê miniaturas.
- Sessões consulta /sessions e /sessions/{id}: capas, resumo/crônica pública,
  participantes, locais e acontecimentos. Notas privadas são exclusivas do
  Mestre e continuam dependendo da filtragem nativa do servidor.

## Mídia e contratos

MediaCache usa /media/…?preview_size=128|768 com token somente no cabeçalho.
Cache limitado a 48 entradas, respostas a 5 MB e imagens decodificadas a
1024 × 1024. Uma requisição de mídia por vez, weakrefs para destinos fechados,
cancelamento/limpeza por troca de credencial e rejeição de hosts externos,
travessia e URLs com token. O mapa selecionado tem prioridade sobre a galeria
e utiliza sua miniatura enquanto a imagem maior chega. Pins aguardam imagem.

O proxy local foi ampliado somente para essas leituras autorizadas. Nenhuma
rota de regra, custo, dano, compra, venda ou movimento foi criada/liberada.

## Arquivos

- scripts/main.gd: coordenação, presença, gavetas e detalhes.
- scripts/navigation_panel.gd, hud_player.gd: ícones e lista online.
- scripts/ui_style.gd: controles visuais comuns.
- scripts/panel_content.gd: projeções de fichas, itens e sessões.
- scripts/map_viewer.gd: mapa, fog e pins com detalhes.
- scripts/media_cache.gd: carregamento autenticado e limitado.
- assets/ui/close.svg, sessions.svg: ícones transparentes.
- tools/serve_preview.py: proxy limitado com leituras de mapas/sessões/mídia.
- tests/test_foundation.py, ui_contract_smoke.gd, create_fixture.py,
  browser_smoke.cjs: regressões, fixture e ensaio nativo/Web.
- README.md e este relatório.

## Verificação

- Node orientação: 4/4 PASS.
- Python assets/proxy: 7/7 PASS, incluindo autenticação e rejeição de travessia.
- Godot smoke nativo: PASS, incluindo layouts horizontais pequenos.
- Godot contrato UI: PASS para presença, ausência de Dorn fictício, ícones,
  tamanho de toque, caminhos de mídia, prioridade do mapa, miniatura provisória
  e isolamento do cache entre credenciais.
- Exportação Compatibility/Web sem threads: PASS.
- Ensaio FastAPI/SQLite descartável + Chrome, Mestre e jogador: PASS, sem
  erros de script. Exercitou ficha, câmera, mensagem, atualização confirmada,
  rotação, mapa/pins/fog e sessão, com dados privados excluídos do jogador.
- Capturas revisadas em TEMP/omni-companion3-6nprxf9m. A alteração posterior
  de navegação para TextureButton e a prioridade de mídia tiveram smoke nativo
  próprio e conferência no endereço público, sem comandos de jogo.
- Evidência pública em TEMP/companion3-drawers-20261106; somente consultas e
  heartbeat normal. Imagens reais, mapas e sessão 7 retornaram HTTP 200.

## Limites

O mapa desta janela é um visualizador: movimentação e combate ainda devem ser
executados no Companion operacional. Cards de ação abrem dados/detalhes;
este lote não promete execução de ataques, magias, equipar ou consumir pelo
Godot. O painel do Mestre fornece acesso aos controles atuais da mesa.

As imagens devem existir no cadastro para substituir o ícone de fallback.
Grandes coleções/arquivos são carregados progressivamente. Aparelho físico e
mesa em redes distintas não foram certificados pelo ensaio emulado.

Backend 8787, OpenCode, fichas, regras, economia e Vault não foram modificados
por esta tarefa. Somente o servidor da prévia 8872 foi recarregado. Os módulos
Python/React operacionais não tiveram alterações nem novas suítes completas.
Não houve commit ou push.
