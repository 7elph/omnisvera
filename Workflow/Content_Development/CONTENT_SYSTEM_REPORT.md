# Relatório do Sistema de Desenvolvimento de Conteúdo

## Arquivos criados/atualizados

- `Workflow/Content_Development/CONTENT_CREATION_QUEUE.md`
- `Workflow/Content_Development/NOTE_DEVELOPMENT_QUESTIONS.md`
- `Workflow/Content_Development/SAGE_CONTENT_INBOX.md`
- `Workflow/Content_Development/CONTENT_GENERATION_PROTOCOL.md`
- `Workflow/Content_Development/Briefs/`
- `scripts/generate_content_queue.py`

## Arquivos alterados pela migração pontual

- `Items/O Frasco Afogado.md` → `Locations/O Frasco Afogado.md`
- `Factions/Rede de Falsificadores de Maré Baixa.md`
- `Items/INDICE_DE_ITENS.md`
- `Workflow/MISSING_NOTES_BACKLOG.md`
- `scripts/audit_vault_standard.py`
- `scripts/plan_frontmatter_minimum.py`
- `Workflow/_audit/Vault_Standardization/VAULT_STANDARDIZATION_AUDIT.md`

## Migração de O Frasco Afogado

- Status: migrado para `Locations/O Frasco Afogado.md`.
- `type` aplicado: `location`.
- `subtype` aplicado: `shop`.
- Link explícito antigo em `Factions/Rede de Falsificadores de Maré Baixa.md` atualizado para wikilink simples.
- `Items/INDICE_DE_ITENS.md` atualizado para não listar o Frasco como item pendente.

## Top 10 notas recomendadas para o Sage desenvolver primeiro

| ordem | nota | tipo | subtipo | motivo |
|---:|---|---|---|---|
| 1 | [[O Frasco Afogado]] | `location` | `shop` | nota indicada como prioridade inicial; muitas referências internas (8); possui pendências ou marcadores de revisão |
| 2 | [[Maré Baixa]] | `location` | `port` | nota indicada como prioridade inicial; muitas referências internas (33); corpo pode ganhar detalhe jogável |
| 3 | [[Nimalis]] | `location` | `` | nota indicada como prioridade inicial; muitas referências internas (109); possui pendências ou marcadores de revisão |
| 4 | [[Coroa de Nimalia]] | `faction` | `noble_house` | nota indicada como prioridade inicial; muitas referências internas (29); corpo pode ganhar detalhe jogável |
| 5 | [[Varkh Nimalis]] | `character` | `player_character` | nota indicada como prioridade inicial; muitas referências internas (60); possui pendências ou marcadores de revisão |
| 6 | [[Guilda dos Mercadores]] | `faction` | `guild` | nota indicada como prioridade inicial; muitas referências internas (17); corpo pode ganhar detalhe jogável |
| 7 | [[ESTADO_DA_CAMPANHA]] | `story` | `` | nota indicada como prioridade inicial; muitas referências internas (47); possui pendências ou marcadores de revisão |
| 8 | [[Porto de Nimalia]] | `location` | `` | nota indicada como prioridade inicial; muitas referências internas (8); corpo pode ganhar detalhe jogável |
| 9 | [[Raziel]] | `character` | `` | nota indicada como prioridade inicial; muitas referências internas (67); possui pendências ou marcadores de revisão |
| 10 | [[Culto dos Sussurrantes]] | `faction` | `religious` | nota indicada como prioridade inicial; corpo pode ganhar detalhe jogável; possui pendências ou marcadores de revisão |

## Briefs criados

- `Workflow/Content_Development/Briefs/O_Frasco_Afogado.md` para [[O Frasco Afogado]]
- `Workflow/Content_Development/Briefs/Mare_Baixa.md` para [[Maré Baixa]]
- `Workflow/Content_Development/Briefs/Nimalis.md` para [[Nimalis]]
- `Workflow/Content_Development/Briefs/Coroa_de_Nimalia.md` para [[Coroa de Nimalia]]
- `Workflow/Content_Development/Briefs/Varkh_Nimalis.md` para [[Varkh Nimalis]]
- `Workflow/Content_Development/Briefs/Guilda_dos_Mercadores.md` para [[Guilda dos Mercadores]]
- `Workflow/Content_Development/Briefs/ESTADO_DA_CAMPANHA.md` para [[ESTADO_DA_CAMPANHA]]
- `Workflow/Content_Development/Briefs/Porto_de_Nimalia.md` para [[Porto de Nimalia]]
- `Workflow/Content_Development/Briefs/Raziel.md` para [[Raziel]]
- `Workflow/Content_Development/Briefs/Culto_dos_Sussurrantes.md` para [[Culto dos Sussurrantes]]
- `Workflow/Content_Development/Briefs/Sentinelas_de_Leth_valora.md` para [[Sentinelas de Leth'valora]]
- `Workflow/Content_Development/Briefs/Bosque_Sussurrante.md` para [[Bosque Sussurrante]]
- `Workflow/Content_Development/Briefs/Mestre_Odran_Veyl.md` para [[Mestre Odran Veyl]]
- `Workflow/Content_Development/Briefs/Guarda_Real_de_Nimalia.md` para [[Guarda Real de Nimalia]]
- `Workflow/Content_Development/Briefs/Vale_Dourado.md` para [[Vale Dourado]]

## Dúvidas ou ambiguidades

- Prioridades são heurísticas; o Sage pode promover ou rebaixar qualquer nota.
- Notas com muitos backlinks podem ser importantes mesmo quando o corpo já parece longo.
- Segredos de mestre devem continuar centralizados em notas de mestre quando houver risco de spoiler.

## Recomendações para próxima etapa

1. Sage escolher de 3 a 5 briefs de alta prioridade.
2. Sage responder no `SAGE_CONTENT_INBOX.md`.
3. IA/Codex desenvolver as notas uma por vez usando o protocolo.
4. Validar links, Dataview/DataCards e visibilidade após cada lote.
