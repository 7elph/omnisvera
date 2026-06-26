# Disgraceland to Omnisvera Gap Analysis

Comparação técnica entre o vault original de Disgraceland e o estado atual do Omnisvera. Esta análise não julga lore e não aplica correções.

## Classificação usada

- preservado
- preservado parcialmente
- perdido
- modificado
- melhorado
- desconhecido
- precisa validação visual

## Matriz geral

| área | Disgraceland técnico | Omnisvera atual | classificação | lacuna técnica | risco |
| --- | --- | --- | --- | --- | --- |
| Plugins principais | Dataview, DataCards, Supercharged Links, Style Settings, Leaflet, Calendarium, Homepage e Templater ativos. | Mesma base principal auditada como ativa. | preservado | Validar configs específicas antes de migrar. | Médio |
| Plugins auxiliares | Highlightr, charts, media-extended, advanced-progress-bars e BRAT presentes. | Conjunto auxiliar preservado com variações. | preservado parcialmente | Alguns plugins podem estar instalados mas sem uso real atual. | Baixo/médio |
| Snippets CSS | 13 snippets, incluindo `dgl.css`, `world.css`, `bside.css`, `supercharged-links-gen.css`. | 13 snippets, 11 ativos, incluindo legados e `omnisvera-profile`. | modificado | CSS novo e antigo coexistem. | Alto visual |
| Supercharged Links | Tags legadas com UID/cor/peso. | Mesmas tags legadas aparecem configuradas. | preservado tecnicamente | Semântica ainda é Disgraceland. | Alto |
| Style Settings | Guarda valores de cor/peso para Supercharged e snippets. | Presente e necessário. | preservado parcialmente | Precisa validação visual no Obsidian. | Médio |
| Frontmatter base | `tags`, `NoteIcon`, `NoteStatus`, `thumbnail`, `cover`, `chapters`, `location`, `territory`, `faction`. | Campos críticos preservados em parte; alguns novos RPG aparecem. | preservado parcialmente | Uso irregular por tipo de nota. | Alto |
| Personagens | Template robusto com retrato, overview, biography, personality, role e aparições por `chapters`. | Estrutura RPG parcial com templates e campos novos. | melhorado parcialmente | Notas reais podem não seguir o mesmo contrato. | Médio/alto |
| Facções | Tags principais, `leader`, `status`, `thumbnail`, DataCards por tag. | Preservação parcial de campos e estrutura. | preservado parcialmente | Relação tag-facção precisa validação. | Médio |
| Territórios | `cover`, `region`, `leader`, `population`, tags e DataCards. | Campos preservados em parte. | preservado parcialmente | Divisão reino/região/local ainda ambígua. | Médio |
| Locais | `cover`, `territory`, `info`, tags e cards. | Parcial. | preservado parcialmente | Necessário distinguir settlement, location e dungeon. | Médio |
| Lore | Tags `lore`, `cover`, `info` e cards. | Parcial. | preservado parcialmente | Visibilidade/canonização ainda não é uniforme. | Médio |
| Religião | Tag `religion` e estrutura própria. | Parcial. | preservado parcialmente | Pode precisar separar religião, culto e entidade. | Médio |
| Capítulos/sessões | `DISGRACELAND` e `chapters` alimentam aparições. | `chapters` ainda existe; `sessions` não é campo funcional auditado. | modificado | Campo de aparições ainda é legado. | Alto |
| Home/dashboard | Home usa banner, callouts, Dataview e DataCards. | Home/dashboard existe com consultas e mídia. | preservado parcialmente | Escopo mestre/jogador não está resolvido. | Alto |
| Leaflet | `TRIBUCIA MAP.md`, imagem base e marcadores linkados. | Leaflet existe e mapa atual foi auditado. | preservado parcialmente | Marcadores e links precisam validação visual. | Alto |
| Calendarium | Calendário ficcional e eventos. | Calendarium existe. | preservado parcialmente | Relação entre calendário e sessões não está consolidada. | Médio |
| Mídia | 425 arquivos em `zz_media`, muitos usados por thumbnail/cover/embed/map. | 75 mídias auditadas; 69 refs não resolvidas; 35 possíveis órfãs. | perdido parcialmente | Grande redução e referências quebradas. | Alto |

## Dependências preservadas

- Dataview continua sendo a camada de consulta.
- DataCards continua dependendo de `thumbnail`, `cover`, tags e pastas.
- Supercharged Links continua dependendo de tags.
- `zz_media` continua sendo a pasta técnica de mídia.
- Banners da Home continuam dependentes de campos `banner-*`.
- `chapters` ainda é o campo seguro para aparições enquanto não houver ponte para sessões.

## Dependências modificadas ou frágeis

- `supercharged-links-gen.css` continua sendo arquivo gerado; não deve ser editado diretamente.
- A semântica das tags visuais ainda aponta para facções e grupos de Disgraceland.
- O sistema de personagens foi expandido para RPG, mas a compatibilidade com o template original ainda precisa validação por nota.
- A mídia atual não pode ser tratada como limpa; há referências não resolvidas e possíveis órfãos.

## Itens que precisam validação visual

- Cores de links com Supercharged Links.
- Cards de personagem, facção, território e local.
- Home/dashboard com imagens e banners.
- Leaflet com imagem base e marcadores.
- Callouts estilizados por snippets legados.

## Conclusão técnica

Omnisvera preservou a espinha técnica de Disgraceland, mas não preservou automaticamente os contratos semânticos. A migração segura precisa criar uma camada de compatibilidade antes de substituir tags, campos de imagem ou `chapters`.
