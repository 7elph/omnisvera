# Characters/Individual Standardization Report

Status: aplicado em 2026-06-28.

## Critério aplicado

- Frontmatter reordenado em padrão único inspirado em `Characters/Individual/Vezemir.md` e no guia `Workflow/OMNISVERA_CHARACTER_TEMPLATE_GUIDE.md`.
- `type: character`, `visibility`, `spoiler_level`, `gm_secret` e `campaign_status` garantidos.
- `chapter` e `chapters` espelhados para compatibilidade.
- `tags` preservadas e complementadas com `character`/`personagem`.
- `NoteIcon: magicitem` aplicado para manter o comportamento visual herdado usado nos personagens.
- Dataview de aparições padronizado para `this.chapters`.
- Seções mínimas comuns adicionadas sem apagar blocos narrativos existentes.
- Campos rejeitados como `canon_status` e `requires_review` não foram mantidos no novo frontmatter.

## Arquivos processados

| arquivo | papel inferido | capítulos | resultado |
|---|---|---:|---|
| `Augustus Terra Decimus.md` | npc/creature | 1 | alterado |
| `Dragão de Colar Dourado.md` | npc/creature | 0 | alterado |
| `Elarion Vaelthor.md` | npc/creature | 0 | alterado |
| `General Cassian Valerius.md` | npc/creature | 2 | alterado |
| `Kaelen, o Flagelo.md` | npc/creature | 0 | alterado |
| `Lorde Malakar.md` | npc/creature | 0 | alterado |
| `Mestre Odran Veyl.md` | npc/creature | 0 | alterado |
| `Mira Valen.md` | npc/creature | 0 | alterado |
| `Padre Oric.md` | npc/creature | 0 | alterado |
| `Raziel.md` | player | 1 | alterado |
| `Vandor, o Senhor das Bestas.md` | npc/creature | 0 | alterado |
| `Varkh Nimalis.md` | player | 1 | alterado |
| `Vezemir.md` | player | 1 | alterado |

## Observações

- `Theron Elensar.md` já estava removido no workspace antes desta padronização e não foi recriado.
- A padronização não executou lote 2 de migração narrativa.
- Biografias e blocos narrativos longos foram preservados.
- Notas ainda podem precisar revisão manual de conteúdo, mas agora compartilham estrutura operacional mínima.
