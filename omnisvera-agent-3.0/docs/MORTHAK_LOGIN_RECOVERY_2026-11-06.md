# Login de Morthak: personagem invisível

## Causa confirmada

O acesso individual de Morthak respondeu HTTP 200 em health, ficha e workspace,
identificado como jogador `morthak`. A ficha estava disponível. O mapa ativo
do Mestre era privado; a API corretamente entregava Earthropo como alternativa
pública. Earthropo tinha pins de Raziel/Vezemir, mas não tinha grid lógico nem
pin de Morthak. O cliente Godot só desenha sprites com posição autorizada, e
ocultava a prévia anônima de Dorn após autenticar.

Portanto, não era uma falha da arte nem das credenciais. Faltava preparar o
mapa recebido pelo jogador. O cliente também não explicava essa ausência.

## Recuperação operacional

- Backup SQLite consistente em `backend/data/backups/before-morthak-login-20261106-234057`.
- Comando nativo do Mestre configurou Earthropo com 32 colunas, 24 linhas,
  células de 1 m, origem zero e distância Chebyshev. As dimensões correspondem
  à camada de fog existente. O grid é provisório/editável, conforme o contrato.
- Comando nativo colocou Morthak na célula livre [16,5], entre os aliados,
  vinculado à ficha existente. O servidor usou os PV e o retrato da ficha.
- Os pins antigos conservaram suas coordenadas persistidas. O grid passou a
  projetá-las nos centros das respectivas células para movimentação autorizada.
- Comparação antes/depois: fichas, estados, inventários, itens, estoques e
  mapas preservados; nenhum pin existente alterado; arquivo de acessos intacto.
- O mapa privado do Mestre e a visibilidade dos mapas não foram alterados.
  Não houve combate, movimento de teste real, recarga ou gasto de recursos.

## Correção do cliente

`scripts/main.gd` agora informa quando o personagem do jogador não possui uma
posição disponível no mapa, mantendo a ficha acessível. Quando o próprio pin
aparece, a câmera o enquadra imediatamente; não exige nova autenticação nem
mantém a câmera na posição da prévia de Dorn. A autorização continua no servidor.

Atualização Web limitada a `index.html`/`index.pck`, com backup anterior em TEMP.
Nenhum reinício do backend/OpenCode e nenhuma rotação de acessos.

## Ensaios

- RED/GREEN nativo em `tests/morthak_contract.gd`: aviso sem pin e câmera
  centralizada quando o pin é recebido após o primeiro snapshot.
- `tests/run_browser.py --suite morthak_login`: reprodução em SQLite/Vault
  sintéticos, mapa privado do Mestre e fallback público sem grid/pin. Login,
  ficha, configuração/posicionamento nativos, recuperação sem refresh,
  movimento do próprio jogador e preservação de recursos/inventário: PASS.
  Evidências em `%TEMP%/omni-companion3-_a5ky2wr`; capturas inspecionadas.
- Contratos de UI/mídia, movimento de Dorn e testes de fundação do Godot.
- Resultados: contratos nativos PASS, fundação 9/9, backend focado em
  workspace/grid 34/34, TypeScript/build React PASS. A suíte completa do
  backend não foi repetida neste ajuste; nenhum código Python foi alterado.
- Conferência pública autenticada como Morthak, Chrome touch 844×390: PASS,
  sprite centralizado e ficha visíveis, sem erro de script nem POST de jogo.
  Não foram executados movimentos contra o banco operacional.

Logs, recibos de comparação e capturas:
`%TEMP%/companion3-morthak-login`. O teste emulado não substitui a confirmação
de rede/desempenho no celular físico de Lucas.

Arquivos de código: `scripts/main.gd`, `tests/morthak_contract.gd`,
`tests/run_browser.py`, novo `tests/morthak_login_browser.cjs`. Backend Python
permaneceu sem alterações; foram utilizados os contratos existentes.
