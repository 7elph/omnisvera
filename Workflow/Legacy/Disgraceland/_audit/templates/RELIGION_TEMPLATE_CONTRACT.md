# RELIGION TEMPLATE CONTRACT

## 1. Função do template

Template funcional para religiões, cultos, santos e sistemas de fé do Disgraceland.

Essas notas funcionam como referência de mundo e também como fontes visuais por tag `religion` e, em alguns casos, `cssclasses`.

## 2. Pasta de origem

- `Workflow/Legacy/Disgraceland/Religion`

Exemplos:

- `Church of the Ember Saint.md`
- `El Santo.md`
- `Faith of Mirella.md`
- `Word of the Stillborn Star.md`
- `RELIGION.md`

## 3. Frontmatter real

Obrigatórios para funcionamento do tipo:

- `tags`

Recorrentes:

- `NoteIcon`
- `cssclasses`

Opcionais:

- `cover`, quando houver card/imagem;
- tags específicas como `prophecy`, `ember-saint`.

Sensíveis:

- `tags`, especialmente `religion`;
- `cssclasses`, quando presente;
- `NoteIcon: religion`.

Visuais:

- `cssclasses`
- `NoteIcon`
- callout de retrato/imagem
- tag `religion`.

Usados por Dataview:

- tags, quando consultadas.

Usados por DataCards:

- potencialmente `cover`/tags se usado em cards.

Usados por Supercharged Links:

- `religion`.

Usados por CSS/snippets:

- `cssclasses`, exemplo `ember`;
- callout `[!NOTE|clean no-i right]+`.

Desconhecidos, mas preservados por segurança:

- tags teológicas específicas;
- `cssclasses` não documentadas fora do snippet.

## 4. Exemplo de frontmatter

```yaml
---
cssclasses:
  - ember
NoteIcon: religion
tags:
  - religion
  - prophecy
  - ember-saint
---
```

## 5. Estrutura interna da nota

```markdown
# Religion Name

> [!NOTE|clean no-i right]+ Religion Name
> ![[religion-image.png|400]]

> "Doctrine quote."

Introductory description.

## Core Beliefs

## History

## Practices & Traditions

## Symbols

## Structure

## Influence

## Holy Days

## Famous Quotes

## Notable Figures

## Relationship With Other Faiths

---

[[Disgraceland Religions]]
```

## 6. Blocos especiais

Usa:

- callout de imagem;
- embed de imagem;
- `cssclasses`;
- links internos para outras religiões/lore;
- listas e seções longas.

## 7. Dependências técnicas

- Supercharged Links
- Style Settings
- snippets de callout
- CSS ligado a `cssclasses`, quando presente
- `dgl.css`
- `supercharged-links-gen.css`
- `zz_media`

## 8. Campos que não podem ser removidos

- `tags`
- `cssclasses`
- `NoteIcon`
- `cover`, se existir

## 9. Tags críticas

- `religion`: Supercharged Links e categorização.
- `ember-saint`: agrupa personagens e notas ligadas à fé.
- `prophecy`: agrupamento narrativo.
- tags específicas de culto/fé devem ser preservadas até mapear uso.

## 10. Consultas relacionadas

Supercharged Links:

```text
religion -> uid 7e5f-283b -> cor/peso definidos em Style Settings
```

Personagens podem referenciar religião por campo:

```yaml
religion: "[[Church of the Ember Saint]]"
```

Home exibe `religion` em tabela de últimos personagens.

## 11. Critérios de validade

Uma nota de religião é válida se:

- possui tag `religion` ou equivalente religioso;
- preserva `NoteIcon`;
- preserva `cssclasses` quando existe;
- mantém imagem/callout quando já presente;
- preserva tags específicas que agrupam personagens ou lore.

## 12. Riscos de migração futura

- Remover `religion` quebra cor visual de links.
- Remover `cssclasses` pode alterar aparência temática.
- Renomear nota religiosa quebra campos `religion` em personagens.
- Mover imagem de `zz_media` quebra retrato/callout.
