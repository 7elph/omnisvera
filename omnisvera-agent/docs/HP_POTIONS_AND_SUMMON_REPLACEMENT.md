# Poções de HP e esqueleto fora do mapa

- A poção comum da sessão 5 cura **1d4**, consumindo um frasco. Sua identidade é
  `Items/Poção de HP.md`; o catálogo a oferece como `campanha-pocao-hp`, com preço
  base de 5 PO e identificação de escolha da campanha. O preço da loja prevalece.
- A compra entrega ao inventário nativo. A mesma entrada aparece em Recursos,
  pronta para usar. Cadastros manuais equivalentes são somados **na resposta**:
  nenhuma quantidade persistida é apagada, duplicada ou transferida por leitura.
  Variantes com cura/cargas/regras diferentes continuam separadas.
- Usar a pilha agregada consome uma linha física positiva dentro da transação
  de cura, orçamento do turno, recibo e ledger. Retry não cura/consome novamente.
  Serviços mágicos do livro continuam consultáveis, mas não são frascos físicos.
  Compras antigas incorretas não são convertidas em curas ou reembolsos implícitos.
- Morthak continua limitado a **um esqueleto ativo**, separado de Animar Mortos.
  “Usar” abre a unidade visível atual; para uma unidade oculta/em outro mapa,
  oferece confirmação para dispensar e invocar novamente. Não revela mapa oculto.
- A substituição exige uso diário e ação disponíveis. A dispensa antiga, nova
  posição, gasto, turno e ledger são atômicos. Falha/cancelamento preserva a unidade
  antiga. Dispensa não devolve usos, e a duração semanal não foi alterada.
- Validação reproduzível: MCP `companion_test_start`, quatro atores, `ui:true`,
  `ui_suite:"inventory_summons"`. Somente SQLite/Vault de fixture em TEMP.
