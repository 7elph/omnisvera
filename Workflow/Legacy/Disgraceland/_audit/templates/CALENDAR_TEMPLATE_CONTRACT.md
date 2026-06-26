# CALENDAR TEMPLATE CONTRACT

## 1. Função do template

Template funcional para a nota de calendário do Disgraceland. A nota documenta calendário, dias, meses, estações, feriados e eventos culturais, enquanto o plugin Calendarium guarda a estrutura executável em JSON.

## 2. Pasta de origem

- `Workflow/Legacy/Disgraceland/CALENDAR.md`
- configuração relacionada: `Workflow/Legacy/Disgraceland/.obsidian/plugins/calendarium/data.json`

## 3. Frontmatter real

Obrigatórios para o template observado:

- `obsidianUIMode`
- `NoteIcon`
- `cover`

Recorrentes:

- `NoteStatus`
- `status`
- `location`
- `faction`
- `tag`

Opcionais:

- valores vazios em `status`, `location`, `faction`;
- `tag` singular, observado como estrutura real e preservado.

Sensíveis:

- `cover`
- `tag: home`
- `NoteIcon: lore`
- bloco `calendarium`.

Visuais:

- `cover`
- `NoteIcon`

Usados por Dataview:

- não há Dataview principal na nota observada.

Usados por DataCards:

- pode participar de `#home` por `tag`, dependendo do comportamento do Obsidian/plugins.

Usados por Supercharged Links:

- tags religiosas/lore mencionadas por links internos, mas o contrato principal é Calendarium.

Usados por CSS/snippets:

- headings e tabelas Markdown padrão.

Desconhecidos, mas preservados por segurança:

- `tag` singular.

## 4. Exemplo de frontmatter

```yaml
---
obsidianUIMode: preview
NoteIcon: lore
NoteStatus: New
status:
location:
faction:
cover: zz_media/t52.png
tag:
  - home
---
```

## 5. Estrutura interna da nota

````markdown
```calendarium
```

## Weekdays

| Real-World Day | Disgraceland Day | Meaning |

---

## Months of the Year

| Real-World Month | Disgraceland Month |

---

## Seasons

| Season Name | Months | Description |

---

# Disgraceland Holidays & Events

## 1st of Frostsun — New Year's Day

**Type:**
**Meaning:**
**Common Practices:**
**Cultural Notes:**

---

# Notes
````

## 6. Blocos especiais

Usa:

- bloco `calendarium`;
- tabelas Markdown;
- headings com ícones;
- links para religiões, lore e territórios.

## 7. Dependências técnicas

- Calendarium
- Homepage, indiretamente
- Style Settings, para ajustes do Calendarium
- `zz_media`

## 8. Campos que não podem ser removidos

- `obsidianUIMode`
- `NoteIcon`
- `NoteStatus`
- `cover`
- `tag`
- `status`
- `location`
- `faction`

## 9. Tags críticas

- `home`, observado em `tag`, não `tags`.

Contrato: não corrigir automaticamente `tag` para `tags` sem testar comportamento e consultas.

## 10. Consultas relacionadas

Bloco renderizador:

```calendarium
```

Configuração técnica:

```text
.obsidian/plugins/calendarium/data.json
```

Eventos no JSON podem apontar para:

- `DISGRACELAND/01 - Main Event Shadows.md`
- `DISGRACELAND/02 - Ghosts On The Waves.md`
- capítulos B-Side;
- notas de lore como `Lore/Ashmoor Festival.md`.

## 11. Critérios de validade

A nota de calendário é válida se:

- contém bloco `calendarium`;
- mantém estrutura de dias, meses, estações e eventos;
- mantém `cover`;
- preserva `tag` singular até validação;
- eventos no JSON continuam apontando para notas existentes.

## 12. Riscos de migração futura

- Renomear notas de capítulo/lore quebra eventos do Calendarium.
- Remover bloco `calendarium` tira renderização interativa.
- Alterar `tag` para `tags` sem teste pode mudar comportamento.
- Remover `cover` quebra cards se a nota participa de `#home`.
