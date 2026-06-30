# Revisão de Padronização — Characters/Individual

Data: 2026-06-30

## Objetivo

Padronizar a camada técnica das notas em `Characters/Individual` contra os templates ativos de personagem, sem reescrever biografias, sem inventar lore nova e sem remover pontes que ainda podem alimentar Dataview/DataCards.

Templates considerados:

- `Templates/Characters/Personagem Jogador.md`
- `Templates/Characters/NPC Importante.md`
- `Templates/Characters/NPC Menor.md`
- `Templates/Characters/Antagonista.md`
- `Templates/Characters/Criatura.md`

## Resultado geral

Foram auditadas 14 notas de personagem.

| nota | formato atual | estado |
|---|---|---|
| `Characters/Individual/Vezemir.md` | Personagem Jogador | alinhado |
| `Characters/Individual/Varkh Nimalis.md` | Personagem Jogador | alinhado |
| `Characters/Individual/Raziel.md` | Personagem Jogador | alinhado |
| `Characters/Individual/Augustus Terra Decimus.md` | NPC Importante | alinhado |
| `Characters/Individual/General Cassian Valerius.md` | NPC Importante | alinhado |
| `Characters/Individual/Elarion Vaelthor.md` | NPC Importante | alinhado |
| `Characters/Individual/Mestre Odran Veyl.md` | NPC Importante | alinhado |
| `Characters/Individual/Mira Valen.md` | NPC Importante | alinhado |
| `Characters/Individual/Padre Oric.md` | NPC Importante | alinhado |
| `Characters/Individual/Kaelen, o Flagelo.md` | Antagonista | alinhado |
| `Characters/Individual/Lorde Malakar.md` | Antagonista | alinhado |
| `Characters/Individual/Vandor, o Senhor das Bestas.md` | Antagonista | alinhado |
| `Characters/Individual/Dragão de Colar Dourado.md` | Criatura | alinhado |
| `Characters/Individual/Unidade DORN-7.md` | Criatura | alinhado |

Nenhuma nota ativa foi classificada como `NPC Menor` nesta leva.

## Correções aplicadas

- Removida a tag residual `Category/Character` das notas de personagem.
- Removida a tag `draft` de personagens em desenvolvimento, mantendo `NoteStatus` e `status` como fonte do estado editorial.
- Adicionada tag `npc-importante` aos NPCs de peso narrativo.
- Adicionada tag `antagonista` aos antagonistas ligados à história de Raziel.
- Adicionada tag `criatura` às notas que seguem o template de criatura.
- Adicionado `cover: zz_media/varkh.jpeg` em `Varkh Nimalis.md`.
- Removido aviso duplicado de estado canônico em `Kaelen, o Flagelo.md`.

## O que foi preservado

- Biografias, histórias e conteúdo narrativo foram preservados.
- `chapters` foi preservado como eixo funcional de aparições.
- `thumbnail` foi preservado para DataCards.
- Tags-ponte como `character`, `player`, `npc`, `creature` e `antagonist` foram preservadas por compatibilidade.
- `NoteIcon: magicitem` foi preservado conforme decisão anterior do Sage.

## Pendências editoriais

| pendência | notas afetadas | recomendação |
|---|---|---|
| Imagem pendente | `Dragão de Colar Dourado`, `Kaelen`, `Lorde Malakar`, `Unidade DORN-7`, `Vandor` | Criar/associar `thumbnail` e `cover` quando houver arte aprovada. |
| Tags inglesas de valor narrativo | `human`, `elf`, `missing`, `mystery`, `alchemist`, `vampire`, `warrior`, `guild` etc. | Revisar em lote próprio; não foram removidas agora para evitar quebrar filtros antigos. |
| Vezemir com `human` e `elf` além de `meio-elfo` | `Vezemir.md` | Decidir depois se as tags raciais antigas ficam como ponte ou se apenas `meio-elfo` deve permanecer. |
| Classes e raças como tags | várias notas | Definir se classe/raça devem continuar em tags ou apenas em campos YAML e links internos. |
| NPC menor | nenhuma nota atual | Criar/usar somente quando houver personagem secundário de cena. |

## Validação

- Todas as 14 notas possuem frontmatter com abertura e fechamento em linhas próprias.
- Não restaram ocorrências de `Category/Character` em `Characters/Individual`.
- Não restaram tags `draft` em `Characters/Individual`.
- As notas continuam compatíveis com as consultas atuais que dependem de `thumbnail`, `tags`, `status`, `location`, `territory` e `faction`.

## Próximo passo recomendado

Depois desta leva, o próximo ajuste seguro é revisar as tags inglesas de classe, raça e estado narrativo, separando:

1. tags que ainda servem como ponte técnica;
2. tags que podem virar português BR;
3. tags que devem desaparecer porque duplicam YAML;
4. tags que podem causar falso positivo em DataCards.
