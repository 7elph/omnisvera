# Revisão de imagens: projeção da biblioteca na oficina

A biblioteca de assets continua sendo a autoridade para revisar imagens.
Consultar a oficina agora projeta essa decisão nos cards e contadores, sem
reescrever a fila nem o banco da campanha e sem executar geração/publicação.

- Asset ignorado: o bloco aparece cancelado, fora de “aguardando aprovação”.
- Asset aprovado: aparece concluído somente quando corresponde ao mesmo
  resultado. O vínculo exige referência, entidade e hash de fonte; a mudança
  de caminho feita pela aprovação é conferida pelo digest nativo do arquivo
  original, restrito a `asset_drafts`, com limite de 25 MB.
- Asset reaberto/regenerado, referência divergente, arquivo antigo ausente
  ou banco indisponível: revisão necessária, sem mostrar uma imagem nova como
  se fosse o resultado antigo. Uma fila inicial externa continua pendente.
- Texto/código e decisões terminais da própria oficina são preservados.

O resultado original e seu hash permanecem disponíveis para auditoria. Não há
sincronização destrutiva, retry de provider, concessão de itens ou aprovação
implícita. A consulta continua exclusiva do Mestre. Aprovar uma imagem nova
exige o fluxo nativo da biblioteca; rascunhos de texto/código conservam o fluxo
de revisão em Cenas.

A projeção da lista/contadores considera os 1000 blocos de imagem mais
recentes, dentro do limite já existente de listagem. O detalhe verifica o ID
solicitado diretamente. Histórico maior que isso não é certificado por esta
projeção resumida. Aprovação de arquivo antigo cujo original foi removido
permanece para revisão, sem inferir equivalência apenas pelo ID.

Verificação operacional somente-leitura encontrou o bloco 288 ainda armazenado
como `awaiting_approval`, mas o asset 66 já estava `queued` (não mais `ignored`
como na observação de 27/10). Referência, entidade, fonte e caminho conferiam;
a nova projeção o classifica `needs_review/superseded`. Nenhum registro foi
alterado para fazer essa consulta.

Regressões: `test_workshop_asset_projection` cobre isolamento, cards/contadores,
aprovação da mesma imagem, geração diferente sob o mesmo ID, ausência de banco,
proveniência divergente, caminhos inseguros, fila inicial e privacidade.
Testes usam somente SQLite TEMP; não certificam anatomia ou lore geradas.
