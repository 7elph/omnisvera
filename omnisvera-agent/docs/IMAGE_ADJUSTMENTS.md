# Ajustes dirigidos de imagens

Mestre > Assets IA > Pedir ajuste, na imagem gerada; ou
"Ajustar imagem da biblioteca" para um icone ja carregado.

Escreva somente a mudanca desejada e clique "Gerar nova versao".
O Flux Klein 9B recebe uma copia preservada da imagem atual como referencia.
Cada solicitacao consome a cota Workers AI; nao existe fallback pago.

O resultado aparece como novo job privado, com Antes/Depois. Aprovar adiciona
a nova opcao a biblioteca, sem substituir automaticamente imagens vinculadas
a pins, itens ou cenas. Escolha a nova imagem na edicao da entidade desejada.
O original e as versoes anteriores permanecem disponiveis.

Requisicoes repetidas com o mesmo ID retornam a mesma versao, sem gerar/cobrar
novamente. Falha preserva o original; uma nova tentativa explicita tem novo ID.
Somente Mestre pode gerar ajustes, consultar comparacoes e aprovar.
Instrucoes e imagens anteriores nao sao expostas aos jogadores.

O modelo pode mudar detalhes nao pedidos: compare antes de aprovar.
Falhas novas distinguem timeout, conexao, retorno sem imagem e HTTP/codigo
numerico do Workers AI. Mensagens cruas do provider nao sao persistidas, pois
podem conter dados privados. HTTP 429 sozinho nao comprova limite diario.
Tentativas antigas com erro generico nao permitem recuperar a causa original.
Repeticao unica autorizada do job 28: revisao 29 falhou com HTTP 500, codigo
3043 do Workers AI. Nenhuma imagem nova; referencia/original preservados.
A tabela oficial de erros consultada nao documenta 3043. Nao atribuir esta
falha a cota diaria sem evidencia adicional; nenhum fallback foi acionado.
Nova reproducao com prompt e referencia identicos gerou imagem com sucesso.
Isso demonstra intermitencia; a causa interna do 3043 nao esta documentada.
O provider agora repete somente HTTP 5xx, uma unica vez, preservando modelo,
referencias e o tempo restante do limite de 180s. Nao repete 401/403/429,
timeouts ambiguos ou imagens invalidas. Repeticoes podem consumir cota.
O resultado real dessa reproducao foi registrado como revisao 30, aguardando
aprovacao, via fluxo existente de ajustes (sem outra inferencia para registrar).
Imagem: draft:edit_30.png. Revisoes falhadas anteriores continuam no historico.
O original nao foi substituido nem a nova versao aprovada automaticamente.
Escopo inicial: imagens de jobs e icones da biblioteca; nao e editor grafico
com pincel/mascara nem navegador de todas as imagens do Vault.

## Validacao de 2026-10-06

Backend 322/322, frontend 137/137, TypeScript, build e diff-check passaram.
Backend operacional reiniciado pelo launcher existente, sem reconfigurar tunel.
Fluxo observado no Chrome autenticado: abrir Assets IA, escolher Misseis Magicos
na biblioteca, preencher a instrucao abaixo e gerar. Criou uma revisao privada
com Antes/Depois, aguardando aprovacao. Nao foi aprovada nem aplicada.

Instrucao usada: "Mude somente o fundo para preto neutro. Preserve os projeteis,
o brilho, as cores e a composicao."

Provider: Flux Klein 9B pela integracao do Companion; nao OpenAI imagegen.
QA visual observado no Chrome desktop e viewport 390x844: formulario legivel,
imagem escolhida visivel, comparacao Antes/Depois vertical sem overflow.
Celular fisico ainda nao testado. Formulario recolhivel, sem modal de tela inteira.

Revisao real de teste: job 25, `backend/data/asset_drafts/edit_25.png`, privada,
aguardando aprovacao. Original preservado por SHA-256. Ambas previews HTTP 200.
Esse rascunho nao foi promovido a biblioteca nem aplicado a personagem/pin.
