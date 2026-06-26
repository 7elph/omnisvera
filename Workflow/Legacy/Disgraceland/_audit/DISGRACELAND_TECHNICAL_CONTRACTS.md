# DISGRACELAND TECHNICAL CONTRACTS

Este documento resume os contratos técnicos extraídos da auditoria do vault legado de Disgraceland.

Escopo: `Workflow/Legacy/Disgraceland`.

Este arquivo não compara Disgraceland com Omnisvera e não propõe adaptação de conteúdo. Ele registra as regras técnicas que devem ser preservadas antes de qualquer comparação, migração ou reimplementação futura.

## 1. Contrato de plugins

O funcionamento visual e operacional do vault depende de plugins habilitados em `.obsidian/community-plugins.json`.

Plugins com contrato técnico direto:

- `dataview`: consulta campos YAML, tags, nomes de arquivo e pastas.
- `data-cards`: renderiza cards visuais a partir de consultas `TABLE ... FROM ...`.
- `supercharged-links-obsidian`: aplica estilo visual a links com base em tags.
- `obsidian-style-settings`: guarda cores, pesos e ajustes visuais usados por snippets/plugins.
- `obsidian-icon-folder`: pode depender de `NoteIcon` e de configuração visual de pastas/notas.
- `calendarium`: define calendário ficcional, eventos e datas ligadas a capítulos.
- `obsidian-leaflet-plugin`: define mapas, imagem base, marcadores, grupos e links para notas.
- `homepage`: usa `Home.md` como entrada/dashboard do vault.
- `templater-obsidian`: apoia criação de notas a partir de templates.
- `highlightr-plugin`, `advanced-progress-bars`, `obsidian-charts`, `media-extended`: adicionam capacidades visuais ou de mídia que não devem ser removidas sem validação.

Contrato: campos, tags, pastas, nomes de notas e arquivos de mídia referenciados por esses plugins não devem ser renomeados, removidos ou normalizados sem atualizar a configuração correspondente.

## 2. Contrato de snippets/CSS

Os snippets em `.obsidian/snippets` são parte da infraestrutura visual do vault.

Snippets auditados:

- `disgraceland-profile.css`
- `dgl.css`
- `world.css`
- `bside.css`
- `scriptwrite.css`
- `supercharged-links-gen.css`
- `topnav.css`
- `htc.css`
- `hrline.css`
- `videopop.css`
- `titlehide.css`
- `fullstat.css`
- `test.css`

Contrato:

- Callouts como `[!NOTE|clean no-i right]+`, `[!world]`, `[!news]`, `[!home]`, `[!cards]` e `[!infobox]` dependem de CSS.
- Classes HTML manuais, como `homepage`, também dependem de snippets.
- CSS não deve ser removido só porque não parece narrativo.
- `supercharged-links-gen.css` é arquivo gerado automaticamente pelo plugin Supercharged Links. Não deve ser editado diretamente.

## 3. Contrato de Supercharged Links

O plugin `supercharged-links-obsidian` está configurado para estilizar links com base em tags.

Contrato:

- `targetTags` está ativo.
- Tags configuradas possuem `uid`.
- Cores e pesos são definidos em `obsidian-style-settings/data.json`.
- O CSS gerado usa variáveis baseadas nesses UIDs.

Consequência: remover, renomear ou traduzir tags visuais altera a aparência dos links e pode destruir o código visual de facções, tipos de nota e agrupamentos.

## 4. Contrato de tags visuais

Estas tags devem ser tratadas como infraestrutura visual, não apenas como lore:

- `loyalist`
- `rancher`
- `third`
- `pirate`
- `widow`
- `steeltown`
- `individual`
- `lore`
- `religion`
- `territory`
- `murray`
- `water`
- `story`

Contrato:

- Não remover sem mapear o seletor Supercharged correspondente.
- Não renomear sem atualizar `supercharged-links-obsidian`, `style-settings` e validar o CSS gerado.
- Não presumir que uma tag de facção é apenas categorização narrativa.
- Tags também alimentam Dataview/DataCards quando usadas em consultas `FROM #tag`.

## 5. Contrato de frontmatter

O frontmatter é a principal API interna do vault.

Campos visuais:

- `obsidianUIMode`
- `NoteIcon`
- `thumbnail`
- `cover`
- `banner`
- `banner-x`
- `banner-y`
- `banner-height`
- `content-start`
- `banner-fade`
- `cssclasses`

Campos de consulta e dashboard:

- `tags`
- `status`
- `info`
- `location`
- `territory`
- `district`
- `faction`
- `religion`
- `role`
- `chapters`
- `leader`
- `population`
- `region`
- `date`
- `description`

Campos territoriais/econômicos:

- `Alignment`
- `Government`
- `reputation`
- `politics`
- `size`
- `exports`
- `imports`

Contrato:

- Não assumir que campo vazio é inútil.
- Não trocar `thumbnail` por `cover` sem alterar consultas e cards.
- Não trocar `chapters` por outro campo sem reescrever aparições.
- Não remover `NoteIcon` sem confirmar dependência com Icon Folder/tema.
- Não remover campos de banner enquanto a Home depender deles.

## 6. Contrato de personagens

Personagens seguem um template técnico recorrente.

Contrato estrutural observado:

- Frontmatter com `thumbnail`, `status`, `location`, `territory`, `district`, `faction`, `religion`, `role`, `chapters` e `tags`.
- Título em `# NOME`.
- Callout de retrato:
  - `> [!NOTE|clean no-i right]+ Nome`
  - embed de imagem com tamanho, geralmente `![[imagem.png|400]]`.
- Seção `## Overview`.
- Campos de overview em negrito.
- Bloco Dataview de aparições:
  - `from "DISGRACELAND"`
  - `where contains(this.chapters, file.name)`
  - `sort file.name asc`
- Seções narrativas como `## Biography`, `## Personality` e `## Role In Disgraceland`.

Contrato:

- `chapters` precisa conter nomes compatíveis com `file.name` dos capítulos.
- O retrato depende de imagem em `zz_media`.
- Tags de grupo/facção podem controlar cor de link.
- A pasta `Characters` é consultada diretamente por dashboards.

## 7. Contrato de facções

Facções funcionam como hubs visuais e relacionais.

Contrato:

- Notas de facção usam `tags`, `leader`, `status`, `location`, `faction` e `thumbnail`.
- A tag principal da facção alimenta DataCards, por exemplo `FROM #loyalist`, `FROM #rancher`, `FROM #third`, etc.
- O campo `thumbnail` alimenta cards.
- A nota pode conter callout de imagem.
- Personagens relacionados podem ser conectados por tag ou por campo `faction`.

Consequência: renomear uma tag de facção pode quebrar cards, cores de links e agrupamentos de personagens ao mesmo tempo.

## 8. Contrato de territórios

Territórios funcionam como páginas de região e como fontes para cards.

Contrato:

- Notas de território usam `tags`, `cover`, `leader`, `region`, `population`, `size`, `Alignment`, `Government`, `reputation`, `exports` e `imports`.
- A Home consulta territórios via `FROM #territory`.
- DataCards usa `cover`, `region`, `leader` e `population`.
- Algumas notas de território usam Dataview para listar residentes por `location`.
- Imagens de território dependem de `zz_media`.

Consequência: remover `cover`, `region`, `leader` ou `population` quebra cards territoriais.

## 9. Contrato de Dataview

Dataview é usado como camada de consulta.

Padrões críticos:

- `from "DISGRACELAND"`
- `from "Characters"`
- `FROM #tag`
- `where contains(this.chapters, file.name)`
- `where contains(lower(string(location)), "...")`
- `sort file.name asc`
- `limit`

Contrato:

- Nomes de pastas usados em `from "..."` são parte da API.
- Nomes de campos usados em `where`, `table` e expressões HTML são parte da API.
- `file.name`, `file.path`, `file.folder`, `file.mtime` e `file.ctime` são usados por dashboards.
- Alterar campo, pasta ou padrão de tag exige atualizar todas as consultas.

## 10. Contrato de DataCards

DataCards renderiza consultas como cards visuais.

Campos críticos:

- `thumbnail`
- `cover`
- `status`
- `location`
- `description`
- `date`
- `info`
- `region`
- `leader`
- `population`

Configurações críticas:

- `imageProperty`
- `preset`
- `columns`
- `imageHeight`
- `imageWidth`
- `cardSpacing`
- `showImageOnHover`

Contrato:

- `imageProperty: thumbnail` exige campo `thumbnail`.
- `imageProperty: cover` exige campo `cover`.
- Consultas `FROM #story`, `FROM #home`, `FROM #territory` e `FROM #location` dependem das tags correspondentes.
- Não normalizar imagens sem atualizar os campos e validar cards.

## 11. Contrato de Home/dashboard

`Home.md` é dashboard técnico, não apenas nota narrativa.

Contrato:

- Usa frontmatter de banner:
  - `obsidianUIMode`
  - `banner`
  - `banner-x`
  - `banner-y`
  - `banner-height`
  - `content-start`
  - `banner-fade`
- Usa callouts:
  - `[!cards]`
  - `[!world]`
  - `[!infobox]`
  - `[!news]`
  - `[!home]`
  - `[!note]`
- Usa Dataview para últimos personagens e últimos modificados.
- Usa DataCards para Home, capítulos, territórios e locais.
- Depende das tags:
  - `home`
  - `story`
  - `territory`
  - `location`
  - `character`
- Depende dos campos:
  - `cover`
  - `thumbnail`
  - `status`
  - `role`
  - `district`
  - `territory`
  - `faction`
  - `religion`
  - `date`
  - `description`
  - `info`

Consequência: a Home quebra se campos, tags ou imagens forem alterados sem atualização coordenada.

## 12. Contrato de Calendarium

Calendarium define o calendário ficcional do vault.

Contrato:

- Configuração principal em `.obsidian/plugins/calendarium/data.json`.
- Calendário auditado: `Tribucian Calendar`.
- Dias da semana, meses, eventos, categorias e data atual vêm do JSON.
- `Home.md` contém bloco `calendarium`.
- `CALENDAR.md` é parte do sistema de calendário.
- Eventos podem apontar para notas de capítulos e lore.

Consequência: renomear capítulos/event notes sem atualizar `data.json` cria eventos órfãos.

## 13. Contrato de Leaflet

Leaflet define o mapa interativo.

Contrato:

- Configuração principal em `.obsidian/plugins/obsidian-leaflet-plugin/data.json`.
- `TRIBUCIA MAP.md` é o arquivo de mapa.
- A layer principal usa `zz_media%2FTribucia.png`.
- Marcadores têm:
  - `type`
  - `loc`
  - `link`
  - `layer`
  - `tooltip`
- Tipos de marcadores possuem ícone/cor própria.

Consequência:

- Renomear notas quebra `link`.
- Mover ou renomear `zz_media/Tribucia.png` quebra o mapa base.
- Alterar tipos de marcador pode quebrar grupos/camadas visuais.

## 14. Contrato de mídia

`zz_media` é o repositório visual do vault legado.

Contratos de uso:

- `thumbnail` geralmente aponta para imagens pequenas, muitas com padrão `th_*.png`.
- `cover` aponta para imagens de cards/territórios/lore.
- Callouts usam embeds `![[imagem.png|400]]`.
- Home usa imagens embutidas e cards.
- Leaflet usa imagem base em `zz_media/Tribucia.png`.
- Alguns HTMLs manuais usam `<img src="...">`.

Contrato:

- Não apagar mídia apenas por parecer órfã no Markdown.
- Antes de remover mídia, checar Markdown, frontmatter, CSS, JSON de plugins, Canvas e HTML.
- Não mover imagens sem atualizar todos os campos e embeds.
- Não substituir formato/extensão sem atualizar referências.

## 15. Campos proibidos de remover

Estes campos não devem ser removidos numa migração futura sem contrato substituto e validação automatizada:

- `obsidianUIMode`
- `NoteIcon`
- `NoteStatus`
- `thumbnail`
- `cover`
- `banner`
- `banner-x`
- `banner-y`
- `banner-height`
- `content-start`
- `banner-fade`
- `status`
- `info`
- `location`
- `territory`
- `district`
- `faction`
- `religion`
- `role`
- `chapters`
- `leader`
- `population`
- `region`
- `size`
- `Alignment`
- `Government`
- `reputation`
- `politics`
- `exports`
- `imports`
- `date`
- `description`
- `cssclasses`
- `tags`

Regra: se um campo aparece em Dataview, DataCards, CSS, plugin JSON, Home, Calendarium, Leaflet ou template de personagem, ele é contrato técnico até prova contrária.

## 16. Regras para comparação futura com Omnisvera

Quando a comparação com Omnisvera for autorizada, seguir estas regras:

1. Comparar contratos, não apenas nomes de campos.
2. Verificar se cada campo de Disgraceland tem equivalente funcional em Omnisvera.
3. Separar campos narrativos de campos técnicos.
4. Não traduzir tags visuais sem recriar Supercharged Links.
5. Não trocar `thumbnail` por `cover` sem revisar DataCards.
6. Não alterar `chapters` sem revisar aparições de personagens.
7. Não mover mídia sem resolver referências em Markdown, YAML, CSS e JSON.
8. Não alterar Home antes de mapear todas as consultas.
9. Não alterar mapa antes de mapear layers, links e marcadores.
10. Não alterar calendário antes de mapear eventos e notas ligadas.
11. Tratar snippets como dependência visual até substituição comprovada.
12. Validar qualquer mudança futura com auditoria de:
    - frontmatter;
    - links;
    - Dataview;
    - DataCards;
    - mídia;
    - CSS/callouts;
    - plugins.

Este documento deve ser usado como base técnica antes de qualquer etapa de migração.
