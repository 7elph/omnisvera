# Morthak: sprite, ficha e movimento

## Implementação

A spritesheet enviada foi copiada sem alterar seus bytes para
`assets/sprites/morthak-motion.jpg`. O manifesto `morthak.json` registra seu
SHA-256 e 40 quadros: idle, walk_down, walk_up, walk_left e walk_right, oito
por estado. Idle usa 5 FPS; caminhadas, 8 FPS.

O fundo quadriculado faz parte do JPG, sem canal alfa. Um shader de renderização
torna transparentes os pixels claros e neutros do fundo; a imagem original não
foi redesenhada, convertida ou substituída por arte gerada. Por ser chroma key
de JPEG, este filtro pode suavizar detalhes muito claros e neutros nas bordas;
uma folha PNG com transparência real seria a melhoria futura de qualidade.

O importador encontra as separações reais entre linhas pelo mínimo de pixels
do personagem. A divisão uniforme incluía o topo da linha seguinte na caminhada
para cima; a revisão visual detectou isso, e um teste RED/GREEN cobre o recorte.
Pivôs nas solas e escala constante por animação mantêm o corpo apoiado no piso.

O renderizador/movimento existente de Dorn agora aceita um manifesto como
parâmetro. A cena mantém Dorn e acrescenta Morthak usando essa mesma classe.
Não há duplicação de combate, atributos ou entidades persistidas: os sprites
projetam os tokens autorizados com `character_id=dorn7` e `morthak`.

O mapa recebe a rota somente depois de o comando nativo ter sido confirmado.
A velocidade permanece 0,5 s por metro, respeitando a configuração do grid.
Cada ator tem posição, direção e seleção próprias. Polling não reinicia o passo;
troca de mapa/reconexão limpa rotas anteriores. Tokens ausentes/ocultos na
resposta autorizada não geram um sprite revelado ao jogador.

A ficha de Morthak mostra uma prévia animada de idle, compartilhando texturas
e metadados do sprite do mapa. A prévia não contém regras nem pode mover o
personagem. O retrato original do backend/Vault e da presença é preservado.
O botão de câmera passa a chamar-se “Focar” e segue o personagem selecionado.

## Uso

1. Recarregar `/companion3/`.
2. Abrir Ficha e selecionar Morthak; a prévia animada aparece ao lado do nome.
3. Fechar a gaveta e pressionar Focar.
4. Clicar no piso para mover o token existente. O jogador só move sua própria
   entidade; o Mestre mantém seus controles existentes.

Se Morthak não estiver no mapa ativo, o Mestre vê uma prévia local identificada
e pode usar o comando existente “Colocar este personagem no mapa”. A integração
não cria nem reposiciona pins reais automaticamente. As regras e os gastos de
deslocamento continuam no backend. Nenhuma animação de ataque/conjuração foi
inventada: a folha entregue contém somente idle e quatro caminhadas.

## Arquivos

- Novos: `assets/sprites/morthak-motion.jpg`, `assets/sprites/morthak.json`,
  `scripts/checkerboard_key.gdshader`, `tools/import_morthak.py`,
  `tests/morthak_contract.gd`, `tests/morthak_browser.cjs` e este relatório.
- Atualizados: `scripts/dorn.gd`, `main.gd`, `grid_map.gd`, `panel_content.gd`,
  `scenes/main.tscn`, `tests/test_foundation.py`, `tests/run_browser.py`, README.

## Validação e limites

Teste nativo de Morthak cobre cinco estados, material, identidade/posição
independentes, retorno ao idle e ocultação de entidades ausentes. Os contratos
de movimento/UI e a persistência de Dorn permanecem cobertos. Testes Python
verificam integridade do original, 40 recortes, transparência de Dorn e proxy.

O lote `tests/run_browser.py --suite morthak` usa somente a base sintética TEMP,
com quatro fichas, Mestre desktop e acesso de Morthak em touch 844×390. Testa
as quatro direções, idle, ficha animada, posição de Dorn preservada e recusa do
movimento de Dorn pelo jogador Morthak. O lote `--suite playable` verifica a
regressão de movimento/Guarda/Relâmpago de Dorn e interfaces existentes.

Evidências e resultados finais ficam em
`%TEMP%/companion3-morthak-20261106`. Os logs identificam os diretórios de
capturas de cada ensaio. A verificação pública usa apenas leitura e heartbeat.
Celular físico e redes de jogadores distintas não são certificados pelo
emulador. Nenhuma ficha, inventário, regra ou arquivo do Vault é editado por
esta integração; sem commits/push ou reinício do backend/OpenCode.

Resultados observados:

- Contrato nativo de Morthak, movimento de Dorn, contrato de UI/mídia,
  persistência de Dorn e smoke da cena: PASS.
- Python de fundação: 9 testes PASS. Orientação: 4 testes Node PASS.
- TypeScript e build React: PASS, saída em TEMP; aviso preexistente de chunks.
- Backend completo: 2.155 testes em 1.150,441 s, OK, um skip. Avisos
  preexistentes de depreciação/SQLite não fechado em testes registrados no log.
- Exportação Web Compatibility: PASS.
- Morthak Web: PASS, `%TEMP%/omni-companion3-me5lzwp4`; oito capturas de quatro
  direções, idle, ficha e acesso mobile. Inspeção visual explícita confirmou
  fundo filtrado e recorte corrigido da caminhada para cima.
- Regressão Web de Dorn: PASS, `%TEMP%/omni-companion3-picqoj9a`; movimento,
  Guarda, Relâmpago, inventário, mapas/pins, sessões e privacidade preservados.
- Pacote público: somente `build/web/index.html` e `index.pck` substituídos,
  com backup em TEMP. Backend e OpenCode permaneceram ativos.
- HTTPS público 844×390: PASS; ficha real de Morthak lida com autorização,
  prévia animada visível, sem erros de script e sem POST mutável. O mapa
  operacional atual não possui pin de Morthak, portanto a captura do piso é
  identificada como prévia local. A posição real não foi inventada.
