---
obsidianUIMode: preview
NoteIcon: audit
NoteStatus: Active
status: Atualizado
tags:
  - workflow
  - audit
  - dataview
  - leaflet
  - frontmatter
---

# Auditoria de Runtime do Vault

_Atualizado em 21 de junho de 2026._

Esta auditoria cobre integrações que não são verificadas apenas pela validação de YAML e wikilinks.

## Resultado

- **Notas ativas:** 84.
- **Blocos DataCards:** 16.
- **Blocos Dataview:** 12.
- **Blocos DataviewJS:** 2.
- **Mapas Leaflet:** 2.
- **Code fences incompletos:** 0.
- **Referências de mídia inexistentes:** 0.
- **Links de marcadores inexistentes:** 0.

## Consultas

As consultas centrais possuem fontes com resultados:

- Home: 8 notas `#home`, 2 histórias, 10 personagens, 2 territórios visíveis, 5 localizações visíveis, 7 raças e 5 classes ativas.
- Capítulos: 3 notas `#chapter`.
- Itens de Vezemir: 4 notas.
- Lore: 5 notas.
- Religiões: 4 notas.

### Consultas vazias intencionais

- `CULTURE.md`: `#entertainment`, `#music`, `#sport` e `#news`.
- `Factions/Guarda Real de Nimalia.md`: `#guarda`.

Essas consultas pertencem a notas em desenvolvimento. Avisos foram adicionados às páginas para deixar claro que os resultados vazios são placeholders e não falhas dos plugins.

## Frontmatter e cartões

- As capas inexistentes de classes e raças foram substituídas por imagens válidas de Omnisvera.
- A Home agora usa `zz_media/avenor.png`; o banner de Disgraceland deixou de aparecer na página ativa.
- A tabela de personagens trata `thumbnail` ausente sem produzir imagem quebrada.
- [[Mestre Odran Veyl]] continua sem thumbnail por decisão editorial pendente. Theron Elensar não está mais na pasta ativa de personagens.
- Campos vazios de facção e classe permanecem preservados quando ainda dependem de decisões do mestre ou dos jogadores.

## Leaflet

### Mapas ativos

| Mapa | ID | Imagem | Marcadores no Markdown |
|:--|:--|:--|--:|
| [[MAPA DE EARTHROPO]] | `earthropo-map` | `zz_media/earthropo.png` | 5 |
| [[MAPA DE NIMALIS]] | `nimalia-capital-map` | `zz_media/mapa-de-nimalis.png` | 1 |

Todos os seis marcadores declarados no Markdown apontam para notas existentes.

O novo marcador de [[Ruínas de Valthor]] registra apenas a posição geral confirmada no sudeste. [[Fortaleza de Gharok]], [[Campos de Earthropo]], [[Bosque Sussurrante]] e [[Vale Dourado]] permanecem sem marcador.

O mapa da capital também conserva dois marcadores manuais ainda sem link. Eles não foram removidos nem convertidos.

### Estado de template

O grupo persistido `tribucia-map`, com 82 marcadores de Disgraceland, foi mantido como fonte de template, mas teve sua associação com os dois mapas ativos removida. O plugin carrega dados persistidos por `id`; portanto, esse grupo não é aplicado aos IDs `earthropo-map` ou `nimalia-capital-map`.

## Calendarium

- A configuração original de Tribucia foi preservada em `Workflow/Templates/Plugin Configs/Calendarium - Disgraceland Template.json`.
- O calendário ativo passou a espelhar os nomes de dias e meses de `CALENDAR.md`.
- O ano de trabalho foi ajustado para 2100, acompanhando `TIMELINE.md`.
- Eventos, categorias e links narrativos de Disgraceland foram retirados da configuração ativa.
- O calendário permanece um rascunho editorial: seus nomes, feriados e significados ainda não são cânone confirmado.

## Snippets de template

- O snippet habilitado de perfil foi renomeado para `omnisvera-profile`.
- A classe `.disgraceland-profile` e as classes regionais antigas permanecem como aliases de compatibilidade para páginas importadas.
- `scriptwrite.css` continua disponível como template, mas não está habilitado na aparência ativa.

## Plugins

As integrações necessárias estão instaladas e habilitadas:

- Dataview `0.5.68`;
- DataCards `1.0.4`;
- Leaflet `6.0.5`.

## Limitação da verificação visual

O Obsidian foi aberto, mas a captura automatizada da janela falhou com `0x80004002` — interface não suportada pelo capturador do Windows. Nenhuma inspeção visual foi alegada como concluída.

A validação desta etapa foi feita pela estrutura das consultas, dados reais do frontmatter, arquivos de mídia, configuração dos plugins e estado persistido do Leaflet. Uma conferência visual manual no Obsidian continua recomendada quando conveniente.

## Comandos

```powershell
.omnisvera-tools\Scripts\python.exe .local-tools\vault_tools.py audit
.omnisvera-tools\Scripts\python.exe Workflow\audit_runtime.py
```
