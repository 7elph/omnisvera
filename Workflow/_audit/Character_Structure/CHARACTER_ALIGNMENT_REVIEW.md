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
- Removidas tags inglesas narrativas dos personagens.
- Convertidas tags de origem `origin-*` para `origem-*`.
- Atualizado o grupo visual do grafo de `#character` para `#personagem`.
- Ajustado `Vezemir.md` para manter apenas `meio-elfo` como tag racial.
- Convertidas tags estruturais de capítulo `chapter`/`chapter01`/`chapter00_*` para `capitulo`/`capitulo01`/`capitulo00-*` nos pontos operacionais relacionados.

## O que foi preservado

- Biografias, histórias e conteúdo narrativo foram preservados.
- `chapters` foi preservado como eixo funcional de aparições.
- `thumbnail` foi preservado para DataCards.
- Tags PT-BR como `personagem`, `jogador`, `npc`, `criatura`, `antagonista` e `npc-importante` foram usadas como padrão operacional.
- `bside` foi preservada como marcador estrutural de capítulos de origem, conforme referência funcional do Disgraceland.
- `NoteIcon: magicitem` foi preservado conforme decisão anterior do Sage.

## Pendências editoriais

| pendência | notas afetadas | recomendação |
|---|---|---|
| Imagem pendente | `Dragão de Colar Dourado`, `Kaelen`, `Lorde Malakar`, `Unidade DORN-7`, `Vandor` | Criar/associar `thumbnail` e `cover` quando houver arte aprovada. |
| Classes e raças como tags | várias notas | Definir se classe/raça devem continuar em tags ou apenas em campos YAML e links internos. |
| NPC menor | nenhuma nota atual | Criar/usar somente quando houver personagem secundário de cena. |

## Validação

- Todas as 14 notas possuem frontmatter com abertura e fechamento em linhas próprias.
- Não restaram ocorrências de `Category/Character` em `Characters/Individual`.
- Não restaram tags `draft` em `Characters/Individual`.
- Não restaram tags inglesas narrativas como `human`, `elf`, `missing`, `mystery`, `warrior`, `guild`, `paladin`, `alchemist`, `vampire`, `hemomancer`, `military`, `priest`, `deceased`, `creature`, `dragon`, `player`, `character` ou `antagonist` nas tags de `Characters/Individual`.
- Tags de capítulo em inglês foram removidas dos pontos operacionais revisados: `chapter`, `chapter01`, `chapter00_varkh` e `chapter00_raziel`.
- As notas continuam compatíveis com as consultas atuais que dependem de `thumbnail`, `tags`, `status`, `location`, `territory` e `faction`.

## Próximo passo recomendado

Depois desta leva, o próximo ajuste seguro é revisar se tags de classe/raça devem continuar como tags ou se devem ficar apenas nos campos YAML e links internos.

Pontos ainda conscientes:

1. `bside` permanece como estrutura de capítulo de origem;
2. `story` permanece por decisão anterior do Sage;
3. `chapters` permanece como campo funcional de aparições;
4. tags de classe/raça podem ser simplificadas depois, se o Sage preferir que essa informação fique só no frontmatter.
