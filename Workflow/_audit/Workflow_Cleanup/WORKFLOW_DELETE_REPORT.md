# Workflow — Relatório de Limpeza Segura

Data: 2026-07-04

## Escopo

Limpeza limitada à pasta `Workflow/`.

Não foram alterados:

- notas de campanha fora de `Workflow/`;
- personagens;
- facções;
- itens;
- locais;
- territórios;
- mídia;
- templates ativos;
- scripts.

## Arquivos e diretórios apagados

| caminho | tipo | motivo | referência relevante encontrada? |
|---|---|---|---|
| `Workflow/_audit/Vault_Standardization/LEAFLET_ID_ALIGNMENT_FIX_REPORT.md` | relatório técnico | Diagnóstico/fix de Leaflet já resolvido; mapas estão operacionais e o relatório foi substituído por auditorias posteriores. | Não; apenas menções em relatórios gerados. |
| `Workflow/_audit/Vault_Standardization/LEAFLET_IMAGE_LOAD_RESET_REPORT.md` | relatório técnico | Diagnóstico/fix de Leaflet já resolvido; continha referências antigas de mídia. | Não; apenas menções em relatórios gerados. |
| `Workflow/_audit/Vault_Standardization/LEAFLET_MAP_FIX_REPORT.md` | relatório técnico | Diagnóstico/fix de Leaflet já resolvido. | Não; apenas menções em relatórios gerados. |
| `Workflow/_audit/Vault_Standardization/LEAFLET_MAP_DIAGNOSTIC_REPORT.md` | relatório técnico local não rastreado | Diagnóstico antigo de Leaflet, já substituído por correções posteriores. | Não; apenas menções em relatórios gerados. |
| `Workflow/_audit/Leaflet_Map_Diagnostics/` | diretório local não rastreado | Backups locais de mapas antes de reset do Leaflet; não são fonte operacional do vault. | Não; apenas menções em relatórios gerados. |
| `Workflow/Legacy/Disgraceland/.smtcmp_vector_db.tar.gz` | artefato legado | Banco vetorial legado do Disgraceland, sem uso operacional em Omnisvera. | Não. |
| `Workflow/Legacy/Disgraceland/.smtcmp_json_db/` | artefato legado | Banco/chat auxiliar legado do Disgraceland, sem uso operacional em Omnisvera. | Não. |
| `Workflow/Legacy/Disgraceland/.trash/` | lixeira legada | Conteúdo de lixeira do vault Disgraceland, sem uso operacional em Omnisvera. | Não; apenas menções em relatórios gerados quando existia. |

## Arquivos preservados

Arquivos preservados porque são padrões vivos, documentação ativa, fila de conteúdo ou possuem referências ainda relevantes:

- `Workflow/OMNISVERA_VAULT_STANDARD.md`
- `Workflow/Content_Development/PLAYER_SAFE_ENTITY_MODEL.md`
- `Workflow/Content_Development/CONTENT_CREATION_QUEUE.md`
- `Workflow/MISSING_NOTES_BACKLOG.md`
- `Workflow/_audit/Vault_Standardization/VAULT_STANDARDIZATION_AUDIT.md`
- `Workflow/Runtime Audit Report.md`
- `Workflow/Format Audit Report.md`
- `Workflow/Charts.md`
- `Workflow/Property Key Dashboard.md`
- `Workflow/Vault Report.md`
- `Workflow/Reports/latest_vault_audit.md`
- `Workflow/COMPATIBILITY_LAYER/`
- `Workflow/RPG_SYSTEM_DESIGN/`
- `Workflow/_audit/Comparison/`
- `Workflow/_audit/Decision_Packet/`
- `Workflow/_audit/Omnisvera/`
- `Workflow/Content_Development/Briefs/`
- `Workflow/AI_CONTEXT/`
- `Workflow/Legacy/Old Dragon anterior/`

## Motivo das preservações conservadoras

Alguns arquivos parecem antigos, mas ainda aparecem em links, briefs, ledger ou auditorias. Exemplos:

- `Workflow/Runtime Audit Report.md` ainda é referenciado por briefs de conteúdo e pelo `MIGRATION_LEDGER`.
- `Workflow/Format Audit Report.md` ainda é referenciado por `Vault Report` e pelo `MIGRATION_LEDGER`.
- `Workflow/Charts.md` ainda contém/recebe referências de auditorias e já havia sido marcado como `NEEDS_SAGE_REVIEW` em limpeza anterior.
- `Workflow/Property Key Dashboard.md` já havia sido marcado como `NEEDS_SAGE_REVIEW`.
- `Workflow/Vault Report.md` é antigo, mas ainda é referenciado por `Charts.md` e auditorias.
- `Workflow/Reports/latest_vault_audit.md` é histórico/desatualizado, mas ainda está referenciado por relatórios de validação e planos.

Por segurança, esses arquivos não foram apagados nesta etapa.

## Dúvidas para o Sage

1. `Workflow/Runtime Audit Report.md`, `Workflow/Format Audit Report.md`, `Workflow/Charts.md`, `Workflow/Property Key Dashboard.md` e `Workflow/Vault Report.md` devem ser:
   - apagados;
   - arquivados;
   - ou convertidos em documentação histórica com aviso no topo?
2. A pasta `Workflow/COMPATIBILITY_LAYER/` ainda deve ficar como documentação ativa, ou pode ser marcada como histórica?
3. As auditorias antigas em `Workflow/_audit/Comparison/`, `Workflow/_audit/Decision_Packet/` e `Workflow/_audit/Omnisvera/` devem permanecer por rastreabilidade?
4. O conteúdo em `Workflow/Legacy/Old Dragon anterior/` ainda é útil como referência ou pode ser arquivado/removido futuramente?
5. O relatório `Workflow/Reports/latest_vault_audit.md` deve ser apagado depois que `VAULT_STANDARDIZATION_AUDIT.md` for confirmado como auditoria oficial única?

## Validação esperada

Após esta limpeza:

- rodar auditoria global do vault;
- confirmar `YAML/frontmatter com problema: 0`;
- confirmar que mídia não foi alterada;
- confirmar que não houve alteração fora de `Workflow/`;
- confirmar que os arquivos apagados não eram fonte operacional.

## Validação executada

### Auditoria global

Comando:

```powershell
python scripts/audit_vault_standard.py --root . --output Workflow/_audit/Vault_Standardization/VAULT_STANDARDIZATION_AUDIT.md
```

Resultado:

| métrica | resultado |
|---|---|
| notas Markdown auditadas | 454 |
| YAML/frontmatter com problema | 0 |
| mídias em `zz_media` | 120 |

### Validador de wikilinks

Comando:

```powershell
python .local-tools/validate_links.py . --ignore-legacy
```

Resultado:

| métrica | resultado |
|---|---|
| wikilinks encontrados | 2763 |
| links resolvidos | 2758 |
| links quebrados | 5 |

Links quebrados reportados:

- `[[CONTENT_CREATION_QUEUE]]` em `CAMPANHA/ESTADO_DA_CAMPANHA.md`
- `[[PLAYER_SAFE_ENTITY_MODEL]]` em `CAMPANHA/ESTADO_DA_CAMPANHA.md`
- `[[A Grande Fratura]]` em `CAMPANHA/ESTADO_DA_CAMPANHA.md`
- `[[A Grande Fratura]]` em `CAMPANHA/ESTADO_DA_CAMPANHA.md`
- `[[Paladino]]` em `CAMPANHA/ESTADO_DA_CAMPANHA.md`

Observação: esses links não apontam para os arquivos removidos nesta limpeza. Não foram corrigidos porque ficam fora do escopo desta tarefa.

### Validador de mídia

Comando:

```powershell
python .local-tools/validate_media.py . --ignore-legacy
```

Resultado:

| métrica | resultado |
|---|---|
| referências de mídia | 286 |
| referências válidas | 285 |
| referências quebradas ativas | 1 |
| imagens órfãs | 26 |

Referência quebrada ativa:

- `zz_media/characters/th_mestre_odran.jpeg` em `Characters/Individual/Mestre Odran Veyl.md`

Observação: essa mídia não foi afetada pela limpeza de `Workflow/`.

### Validador de frontmatter

Comando:

```powershell
python .local-tools/validate_frontmatter.py . --ignore-legacy
```

Resultado:

| métrica | resultado |
|---|---|
| notas analisadas | 257 |
| notas sem frontmatter | 0 |
| frontmatter inválido | 0 |
| campos vazios importantes | 0 |

## Conclusão

A limpeza removeu apenas artefatos obsoletos em `Workflow/`.

Nenhum padrão vivo, template ativo, script, mídia, personagem, item, facção, local, território, lore ou nota de campanha foi alterado por esta etapa.
