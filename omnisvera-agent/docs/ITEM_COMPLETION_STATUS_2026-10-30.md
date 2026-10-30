# Itens e economia — cobertura real em 30/10/2026

Consulta somente de leitura ao SQLite operacional e ao registro unificado.
Não certifica execução de todos os itens. Evidência compacta em
`economy-resale-20261030/all-items-summary.json` nos artefatos locais.

| Medida | Resultado |
|---|---:|
| Entradas no registro, incluindo referências e serviços | 486 |
| Cadastros físicos, excluindo referências e serviços | 380 |
| Sem vínculo próprio de imagem | 230 |
| Classificação comercial indefinida | 112 |
| Sem avaliação de preço | 48 |
| Descrição sem regras estruturadas: revisão mecânica indicada | 245 |
| Estabelecimentos configurados e vinculados | 2 |

As lacunas se sobrepõem. Cadastros de fontes diferentes podem representar
variações do mesmo bem. A existência de um vínculo de imagem não prova que
o arquivo existe. Ausência de `effect_rules` não prova ausência de backend:
o motor também tem inferências/adaptadores nativos. O marcador genérico de
`test_evidence` ainda não consolida os ensaios por item e não deve ser usado
para afirmar que cada item nunca foi testado.

Compra, venda, barganha, entrega, avaliação, hospedagem e quatro serviços
mágicos foram ensaiados nos estabelecimentos existentes. Isso não representa
economia completa de todas as localidades, nem todas as mecânicas dos itens.

## Prioridade definida pelo Mestre

Concluir os itens antes de ampliar o catálogo de magias. Trabalhar por famílias:
armas/munição, armaduras/escudos, consumíveis, equipamentos de exploração,
transporte/montarias e itens mágicos. Para cada família verificar identidade,
preço/fonte, quantidade, peso/carga quando aplicável, imagem, equipamento/uso,
efeito/custo/duração quando aplicáveis, compra/venda e ensaio de consequência.
Objetos narrativos não precisam de uma ação artificial para serem utilizáveis.

Reparo e ferrugem são casos específicos dessa cobertura. Regra aprovada:
reparo mágico pode restaurar até o bônus original registrado, por preço
definido pelo Mestre, sem recriar item destruído nem restaurar cargas.
Ainda não implementado/ativado. O esboço de regressões foi preservado como
proposta nos artefatos, fora da descoberta de testes; não há testes quebrados
adicionados à suíte nem mudanças de fichas/estoques reais neste diagnóstico.

## Conexão

Amostragem HTTPS autenticada: 48 leituras de fichas/cabeçalho dos quatro atores,
zero erros, mediana 0,974 s e maior resposta 2,338 s. Executada pelo computador
servidor contra o endereço público; não prova conectividade de celulares em
redes independentes nem estabilidade de uma sessão prolongada.
