# Itens e ofertas — inventário privado do Mestre

**Rascunho de auditoria e seleção. Não cria estoque, NPC, preço ou canon.**

## Guardas e prontidão

`item_catalog.item_offer_readiness` distingue oferta comercial de efeito de jogo.
Referência de tabela, item inexistente e preço ausente, negativo ou não finito
impedem a oferta. Zero explícito continua válido; não se converte ausência em
gratuidade. Texto de item mágico, cargas ou preço não comprovam um executor.
Um pedido para anunciar efeito automatizado não comprovado fica bloqueado.

O mesmo validador protege estoque novo, compra GM legada, consulta/cotação/
confirmação de compra e venda no mapa, além de entrega por serviço. Uma oferta
alterada é revalidada antes de gastar moedas ou entregar o objeto. Retry já
confirmado continua recuperando o recibo original, sem nova entrega.

`map_commerce.offer_readiness_report(path, access)` faz apenas SELECT com
`mode=ro`, é exclusivo do Mestre e não inicializa schema. Mostra lacunas por
oferta. A consulta pelo pin acrescenta `readiness`; nomes/ofertas bloqueados
ficam em `blocked_offers` somente para o Mestre, fora da projeção de jogadores.

O inventário de catálogo agora usa `is_catalog_reference` como fonte única.
Foram corrigidos 23 falsos fragmentos: preço/peso no título de carroça, cavalo,
propriedade ou hospedagem não transforma o bem em cabeçalho de tabela.

## Fotografia de 28/10

- 326 entradas: **96 referências** e **230 itens/ofertas concretos**.
- Os 230 concretos têm preço numérico válido; 35 usam preço de campanha já
  identificado pelo cadastro. Nenhum preço foi criado ou alterado neste corte.
- 37 ofertas operacionais consultadas em leitura: nenhuma lacuna bloqueante
  de identidade/referência/preço. Isso não certifica estoque disponível,
  automação dos efeitos, imagem de cada item ou capacidade de todos os serviços.
- Armas podem carregar dano base; isso não certifica alcance, crítico,
  propriedades especiais ou toda a ficha. Proteções, consumíveis e efeitos
  mágicos sem regra estruturada continuam assistidos.
- Testes focados: 56/56 aprovados, incluindo dez novas regressões; antes do
  patch, seis falhas e quatro erros reproduziram as lacunas. SQLite descartável.
  Browser, ativação e suíte completa pertencem à validação integrada do lote.

## Seleção sugerida — não publicada

Preços abaixo são apenas os valores existentes no catálogo OD1. Quantidades,
vendedores, serviços e localização permanecem para revisão da campanha.

| Uso sugerido | Entrada existente | Preço do cadastro | Limite |
|---|---|---:|---|
| Loja de equipamentos / Thoradin | Espada longa | 10 PO | Dano base configurável; propriedades não certificadas |
| Loja de equipamentos / Thoradin | Armadura de couro | 20 PO | Conferir regra de CA da unidade equipada |
| Exploração | Corda, 15 m | 1 PO | Uso físico/narrativo; sem pathfinding/cordas automáticas |
| Transporte / estábulo | Carroça, capacidade 100 kg | 8 PO | Entrega de bem; viagem/carga assistidas |
| Transporte / estábulo | Cavalo de montaria | 13 PO | Compra não cria ficha de montaria automaticamente |
| Hospedagem | Quarto individual | 1 PP | Reserva; descanso só pelo fluxo nativo do Mestre |
| Serviço arcano | Poção (serviço) | 50 PO | Serviço genérico não define poção, cura ou receita |

Não distribuir automaticamente itens mágicos por sua descrição. Antes de
anunciar cura, buff ou outro benefício executável, precisa existir contrato
de uso revisado, custo/cargas e teste de consequência no motor nativo.

Arquivos: `item_catalog.py`, `catalog_readiness.py`, `map_commerce.py`,
`merchant.py`, `test_item_offer_readiness.py`. Nenhuma ficha ou loja real foi
modificada. Sem staging, commit ou push.
