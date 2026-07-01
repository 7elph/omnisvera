# Omnisvera — Frontmatter Mínimo Aplicado

Gerado em: 2026-07-01 14:58

Modo: `apply`
Filtro: `Locations` / risco `low`

> [!IMPORTANT]
> Esta etapa só adiciona campos Omnisvera mínimos em notas limpas do filtro informado.
> Campos legacy, tags e corpo das notas devem permanecer preservados.

## Resumo

| métrica | valor |
|---|---:|
| arquivos do filtro no plano | 14 |
| elegíveis | 5 |
| alterados/aplicáveis | 5 |
| pulados | 9 |

## Campos adicionados/aplicáveis

| campo | ocorrências |
|---|---:|
| `canon_status` | 5 |
| `created_by` | 2 |
| `requires_review` | 5 |
| `subtype` | 5 |
| `work_status` | 5 |

## Subtypes adicionados/aplicáveis

| subtype | ocorrências |
|---|---:|
| `district` | 1 |
| `port` | 1 |
| `ruin` | 1 |
| `settlement` | 1 |
| `wilderness` | 1 |

## Arquivos alterados/aplicáveis

| arquivo | campos adicionados | valores | campos legacy preservados |
|---|---|---|---|
| `Locations/Bairro dos Forasteiros.md` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | `subtype: district`, `work_status: Em desenvolvimento`, `canon_status: Working Canon`, `created_by: Sage`, `requires_review: true` | `NoteIcon`, `NoteStatus`, `cover`, `obsidianUIMode`, `status`, `tags`, `thumbnail` |
| `Locations/Bosque Sussurrante.md` | `subtype`, `work_status`, `canon_status`, `requires_review` | `subtype: wilderness`, `work_status: Em desenvolvimento`, `canon_status: Draft`, `requires_review: true` | `NoteIcon`, `NoteStatus`, `cover`, `obsidianUIMode`, `status`, `tags`, `thumbnail` |
| `Locations/Leth'valora.md` | `subtype`, `work_status`, `canon_status`, `requires_review` | `subtype: settlement`, `work_status: Em desenvolvimento`, `canon_status: Working Canon`, `requires_review: true` | `NoteIcon`, `NoteStatus`, `cover`, `obsidianUIMode`, `status`, `tags`, `thumbnail` |
| `Locations/Maré Baixa.md` | `subtype`, `work_status`, `canon_status`, `requires_review` | `subtype: port`, `work_status: Em desenvolvimento`, `canon_status: Working Canon`, `requires_review: true` | `NoteIcon`, `NoteStatus`, `cover`, `obsidianUIMode`, `status`, `tags`, `thumbnail` |
| `Locations/Ruínas de Valthor.md` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | `subtype: ruin`, `work_status: Em desenvolvimento`, `canon_status: Working Canon`, `created_by: Sage`, `requires_review: true` | `NoteIcon`, `NoteStatus`, `cover`, `obsidianUIMode`, `status`, `tags`, `thumbnail` |

## Arquivos pulados

| arquivo | motivo |
|---|---|
| `Locations/Bairro dos Anões.md` | DIRTY_PREEXISTING |
| `Locations/Bairro dos Dragonborns.md` | DIRTY_PREEXISTING |
| `Locations/Bairro dos Elfos.md` | DIRTY_PREEXISTING |
| `Locations/Bairro dos Humanos.md` | DIRTY_PREEXISTING |
| `Locations/Bairro Nobre.md` | DIRTY_PREEXISTING |
| `Locations/Distrito Comercial.md` | DIRTY_PREEXISTING |
| `Locations/Mercado Central.md` | DIRTY_PREEXISTING |
| `Locations/Nimalis.md` | Nimalis é capital; sugestão `settlement` precisa revisão antes de aplicar |
| `Locations/Porto de Nimalia.md` | DIRTY_PREEXISTING |

## Garantias verificadas

- Nenhum campo existente deve ser removido.
- Nenhuma tag deve ser removida ou alterada.
- O corpo da nota deve permanecer inalterado.
- Arquivos `DIRTY_PREEXISTING` são pulados.
