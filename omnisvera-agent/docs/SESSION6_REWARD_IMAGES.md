# Imagens e entrega das recompensas

Aplicado em 9 de outubro de 2026, pelos endpoints autenticados do Mestre:

- Sessão 6: capa original `1000208295.jpg`.
- `levantar-um-esqueleto`: arte original `1000208296.jpg` no catálogo de imagens.
- Pulseira de Vinhas: `session-item:20`, uma unidade entregue a Vezemir.
- Essência de Mana: `session-item:21`, uma unidade entregue a Morthak.
- Página de Grimório: `session-item:22`, uma unidade entregue a Morthak.

Os três itens usam o encaixe Acessório, como o anel de Raziel. Foram entregues
sem equipar, sem consumir recursos ou alterar a ficha atual do esqueleto.
Não houve duplicação de inventário nem alteração de datas históricas de aquisição.
As cinco imagens foram preservadas byte a byte e os itens/imagens conferidos
pelos endpoints de jogador. Não havia esqueleto invocado no mapa ativo para
atualização de imagem do pin.

## Mecânicas implementadas após confirmação do Mestre

- Pulseira: Vezemir precisa equipar o item e estar no próprio turno em combate
  tático. Escolhe alvo participante; sem JP configurada, o uso é rejeitado.
  No início de cada turno do alvo, d20 digital + bônus da JP normal contra a
  JP normal. Sucesso liberta; falha pula automaticamente o turno e registra
  o resultado público. Expira após três turnos do alvo ou fim do combate.
  Movimento pelo endpoint de posição é bloqueado enquanto preso. Não há
  consumo de quantidade ou cargas inventadas. Repetir a requisição não duplica
  o efeito, os testes ou o gasto da ação.
- Essência: confirmar a ficha-base sem equipamento. A ficha atual é PV 10,
  CA 16, ataque +2 e dano 1d6+1; não inventar os valores inferiores nem curar
  uma invocação existente ao equipar/desequipar.
- Página: confirmado pelo Mestre como usos diários, não projéteis. O limite
  é quatro com equipamento e três sem; a quantidade já gasta é preservada,
  inclusive ao alternar equipamento depois de gastar os quatro usos. O
  descanso normal limpa essa dívida e recarrega o limite atual.

O Mestre pediu nesta etapa apenas a imagem da essência no card do esqueleto.
O snapshot do mapa projeta nome, descrição, imagem e estado equipado do item
concedido a Morthak; não projeta inventário nem notas privadas. O card aberto
pelo pin usa o mesmo SheetDetail da ficha. Os atributos atuais do esqueleto
não foram alterados, pois a ficha-base sem essência permanece indefinida.

Alterações em código e testes não ativam o backend já em execução sem reinício.
Há um combate ativo no processo atual; a ativação aguarda autorização do Mestre
para não interromper a mesa. Não chamar a validação local de prova em mesa.
