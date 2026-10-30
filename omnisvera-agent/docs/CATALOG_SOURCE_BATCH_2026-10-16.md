# Catálogo: primeiro lote de proveniência (16/10/2026)

## Escopo entregue

Quatro referências verificadas foram ligadas aos IDs do catálogo existente, sem duplicar descrições, importar PDFs/imagens ou editar fichas. `source_verified` significa que a fonte e suas páginas foram conferidas, **não** que a magia está automaticamente implementada. Todas as referências têm `execution_approved: false`; contratos e exceções aprovadas da campanha permanecem separados.

| ID existente | Páginas físicas | Páginas impressas |
| --- | --- | --- |
| `arcana-relampago` | 82 | 82 |
| `arcana-reflexos` | 64 | 64 |
| `arcana-teia` | 65–66 | 65–66 |
| `arcana-dissipar-magia` | 71–72 | 71–72 |

As seis páginas de regras e a página 3 de créditos foram renderizadas e inspecionadas visualmente. Teia continua na página 66; não foi reduzida à página inicial. O PDF possui 190 páginas. A numeração física coincide com a impressa neste lote.

Fonte: *Tomo da Magia Arcana para Old Dragon 2*, escrito/diagramado por Rangel Perez Sardinha, versão 1.0.0 (14/05/2024). Os créditos na página 3 declaram Old Dragon 2a Edição © 2023 Buró Editora, criação de Antonio Sá Neto, Dan Ramos e Fabiano Neme, sob CC BY-SA 4.0. A referência mantém atribuição e URL da licença. Não se importaram elementos gráficos.

SHA-256 da cópia conferida: `c24002d7fdd87af03435b66d065f462a9ce9112bdff9a660d649e4ee63244b51`. O manifesto contém somente nome base, não o caminho privado da fonte. Renderizações intermediárias ficaram fora do repositório.

## Contrato para integração

- `get_catalog_provenance(kind, catalog_id) -> dict | None`.
- `list_catalog_provenance(kind=None) -> list[dict]`.
- `kind="spell"` é o único tipo deste primeiro lote; desconhecidos retornam `None`/lista vazia.
- Cada retorno inclui `source` expandida; cópias defensivas impedem alteração acidental do cache pelas respostas.
- O loader valida versão, metadados obrigatórios/hash, páginas positivas/ordenadas/sem repetição/dentro do documento, pares físicos/impressos, IDs nativos, duplicatas e negação explícita de aprovação de execução.
- Runtime lê somente o JSON empacotado e o catálogo nativo: sem banco, leitura de PDF, caminhos externos, rede, alteração de campanha ou habilitação de habilidade. Rotas chamadoras continuam responsáveis pela autorização Mestre/Jogador.

## Inventário e limites

Já existem 854 magias (450 arcanas/404 divinas), 326 itens, 47 habilidades e 255 monstros nos catálogos. Este lote enriquece quatro referências; não declara as demais verificadas. Extração de dados por regex ou primeiro dado textual não autoriza automação. Foi observada uma associação suspeita em habilidade `Adivinho` cuja descrição trata de abjurante; não alterada neste corte.

O Livro Básico Aprimorado local (1ª edição aprimorada, novembro/2017) declara Creative Commons v3.0 by-sa/Open Game com exclusão de arte, logo, ilustrações e diagramação; a metadata global atual de itens o descreve genericamente como proprietário. A divergência foi registrada, **sem mudar licença global nem tomar a licença dos Tomos como licença de outras fontes**. Mestres do Arcano continua exigindo conferência específica de direitos. Força Arcana não foi equiparada silenciosamente a outra magia do Tomo.

## Verificação

RED: o teste novo falhou inicialmente porque `app.catalog_provenance` não existia. GREEN: `..\.venv-observer\Scripts\python.exe -m unittest test_catalog_provenance`, em `backend/`: **8/8 PASS**. Cobertura: quatro vínculos nativos, páginas/hash/versão, desconhecidos sem aprovação, cópia defensiva, duplicatas, IDs inexistentes, páginas inválidas e proibição de execução/caminhos privados. Demais checks e integração de rotas serão realizados pelo corte integrador; não foram reivindicados aqui.

Arquivos novos: `backend/app/catalog_provenance.py`, `backend/app/data/catalog_provenance.json`, `backend/test_catalog_provenance.py` e este documento. Nenhum catálogo anterior, regra, token, banco, mídia ou estado operacional foi alterado. Sem commit/push/reinício.
