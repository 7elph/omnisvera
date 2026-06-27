# Validação do Alinhamento com a Taxonomia

Data: 2026-06-27

## Comandos executados

Validação de documentos ativos:

```powershell
Get-ChildItem Workflow -File -Filter 'OMNISVERA_*.md' |
  Where-Object { $_.Name -notin @('OMNISVERA_SYSTEM_TAXONOMY.md','OMNISVERA_SYSTEM_TAXONOMY_DECISIONS.md') } |
  Select-String -Pattern 'sessions|player_known|subtype|portrait|token_image|map_image|handout_image|life_status|old_dragon_class|old_dragon_race|requires_review|work_status|canon_status|source|state'
```

Resultado: sem ocorrências em documentos ativos, exceto a própria taxonomia que lista itens rejeitados como decisão.

Validação de termos antigos em documentos ativos:

```powershell
Get-ChildItem Workflow -File -Filter 'OMNISVERA_*.md' |
  Where-Object { $_.Name -notin @('OMNISVERA_SYSTEM_TAXONOMY.md','OMNISVERA_SYSTEM_TAXONOMY_DECISIONS.md') } |
  Select-String -Pattern 'Home_Jogadores|portal neutro|loyalist|rancher|pirate|widow|steeltown|water|individual|religion|territory'
```

Ocorrências justificadas:

| termo | motivo |
|---|---|
| `Home_Jogadores` | Aparece apenas para afirmar que não existe mais como Home operacional. |
| `territory` | Campo herdado preservado; não é recomendação de tag antiga. |
| `religion` | Campo herdado preservado; não é recomendação de tag antiga. |

Validação de templates:

```powershell
Get-ChildItem -Path Templates -Recurse -File -Filter *.md |
  Select-String -Pattern 'sessions|player_known|subtype|portrait|token_image|map_image|handout_image|life_status|old_dragon_class|old_dragon_race|requires_review|work_status|canon_status|source|state'
```

Resultado: sem ocorrências de campos rejeitados nos templates ativos.

Ocorrências restantes:

| termo | motivo |
|---|---|
| `territory` | Campo herdado preservado pela taxonomia. |
| `religion` | Campo herdado preservado pela taxonomia. |

## Documentos históricos marcados

Foram marcados 36 documentos históricos em:

- `Workflow/COMPATIBILITY_LAYER`;
- `Workflow/RPG_SYSTEM_DESIGN`;
- `Workflow/_audit/Decision_Packet`;
- `Workflow/_audit/Comparison`.

Também foram marcados:

- `Workflow/CHARACTER_SCHEMA.md`;
- `Workflow/AI_CONTEXT/05_FRONTMATTER_SCHEMA.md`;
- `Workflow/Templates/Character Template.md`;
- `Workflow/Templates/Player Character Template.md`.

## Pendências fora do escopo

- `.obsidian/plugins/obsidian-leaflet-plugin/data.json` continua modificado apenas por `lastAccessed`; não foi incluído.
- Documentos históricos ainda podem conter campos e tags antigos por contexto, mas agora carregam aviso de que não são fonte principal.
- Auditorias antigas em `Workflow/_audit/Omnisvera` e relatórios gerados não foram reescritos.

## Conclusão

Os documentos ativos principais foram alinhados à taxonomia atual do Sage.

O vault está mais consistente para preparar o primeiro lote real de migração de notas, desde que o lote piloto respeite os templates atuais e não use documentos históricos como fonte principal.
