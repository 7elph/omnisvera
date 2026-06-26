# LORE TEMPLATE CONTRACT

## 1. Função do template

Template funcional para notas de lore: eventos históricos, conceitos, substâncias, instituições, festivais, massacres, tecnologias e elementos de mundo.

O template é menos uniforme que personagens/facções, mas tem contratos técnicos recorrentes em tags, capa, status e callouts.

## 2. Pasta de origem

- `Workflow/Legacy/Disgraceland/Lore`

Exemplos:

- `Blackshift Massacre.md`
- `Abbsidian.md`
- `Ashmoor Festival.md`
- `Luxyn.md`
- `World Lucha Libre.md`

## 3. Frontmatter real

Obrigatórios para funcionamento do tipo:

- `tags`

Recorrentes:

- `obsidianUIMode`
- `NoteIcon`
- `NoteStatus`
- `status`
- `location`
- `faction`
- `cover`
- `info`

Opcionais:

- `cssclasses`
- valores vazios em `location` e `faction`;
- tags específicas de evento/facção/local.

Sensíveis:

- `tags`, especialmente `lore`;
- `cover`, quando a nota aparece em cards ou visual;
- `info`, quando usado como resumo.

Visuais:

- `NoteIcon: lore`
- `cover`
- `cssclasses`
- callouts customizados como `[!column]`, `[!rustwater]`.

Usados por Dataview:

- tags.

Usados por DataCards:

- `cover`, quando lore participa de cards.

Usados por Supercharged Links:

- `lore`.

Usados por CSS/snippets:

- callouts customizados;
- `cssclasses` quando presente.

Desconhecidos, mas preservados por segurança:

- `status`
- `location`
- `faction`
- tags de tema.

## 4. Exemplo de frontmatter

```yaml
---
obsidianUIMode: preview
NoteIcon: lore
NoteStatus: New
status: Alive
location:
faction:
cover: zz_media/lore.png
tags:
  - lore
  - neutral
info: Short lore summary.
---
```

## 5. Estrutura interna da nota

```markdown
# LORE TITLE

> [!column] Information
>> [!rustwater] Description
> **Date:**
> **Location:**
> **Summary:**

>> [!rustwater] Related Image
>> ![[lore-image.png|400]]

## Main Section

## Aftermath

## Legacy

---

### See also
- [[Related Note]]
```

Variações existem: algumas notas usam texto corrido, outras tabelas, outras listas e seções temáticas.

## 6. Blocos especiais

Usa:

- callouts customizados;
- embeds de imagem;
- links internos;
- tabelas/listas;
- `cssclasses` em alguns casos.

Não há padrão obrigatório universal de Dataview/DataCards dentro da nota de lore.

## 7. Dependências técnicas

- Supercharged Links
- Style Settings
- snippets de callout
- `dgl.css`
- `world.css`
- `zz_media`
- DataCards, quando lore aparece em cards

## 8. Campos que não podem ser removidos

- `tags`
- `cover`
- `info`
- `NoteIcon`
- `NoteStatus`
- `obsidianUIMode`
- `status`
- `location`
- `faction`
- `cssclasses`

## 9. Tags críticas

- `lore`: Supercharged Links e categorização.
- `story`, quando uma lore também funciona como história/card.
- tags temáticas, como `neutral`, `water`, `religion`, podem afetar agrupamento visual ou narrativo.

## 10. Consultas relacionadas

Consulta geral da Home por #home não é de lore, mas lore pode participar de DataCards quando marcada com tags consultadas.

Supercharged Links usa a tag:

```text
lore -> uid e997-0713 -> cor/peso definidos em Style Settings
```

## 11. Critérios de validade

Uma nota de lore é válida se:

- possui tag `lore` ou tag temática explícita;
- mantém `cover` quando tem imagem/card;
- preserva `info` quando usado como resumo;
- preserva callouts customizados existentes;
- não remove `cssclasses` quando presente.

## 12. Riscos de migração futura

- Remover `lore` altera cor de links e categorização.
- Remover `cover` quebra visual/card quando usado.
- Padronizar estrutura pode apagar callouts customizados.
- Apagar imagens de `zz_media` pode quebrar embeds.
- Remover campos vazios pode afetar templates/plugin expectations.
