---
obsidianUIMode: preview
NoteIcon: outline
NoteStatus: Active
status: Em andamento
tags:
  - workflow
  - migration
  - disgraceland
  - omnisvera
---

# Registro da Migração

Este documento controla a retirada de Disgraceland do conteúdo ativo sem perder sua utilidade como template.

## Estados

| Estado | Uso |
|:--|:--|
| **Migrado** | Estrutura e conteúdo já representam Omnisvera. |
| **Revisar** | A nota é de Omnisvera, mas contém afirmações provisórias ou estrutura antiga. |
| **Placeholder** | O nome precisa existir, mas o conteúdo ainda não foi definido. |
| **Template** | Ferramenta ou estrutura preservada; não é lore. |
| **Legado** | Conteúdo narrativo de Disgraceland que deve sair da navegação ativa. |
| **Bloqueado** | Depende de decisão do usuário. |

## Núcleo migrado

- [x] `Home.md`
- [x] `Workflow/CANON.md`
- [x] `Workflow/OUTLINES.md`
- [x] `Workflow/Scratch Notes.md`
- [x] `LATEST_NEWS.md`
- [x] [[Vezemir]]
- [x] [[Varkh Nimalis]]
- [x] [[Raziel]]
- [x] Itens principais de Vezemir e Raziel
- [x] [[Nimalia]], [[Floresta de Avenor]], [[Leth'valora]] e [[Ruínas de Valthor]]

## Resíduos de Disgraceland a isolar

- [x] `NOTES.md` — conteúdo legado movido para `Workflow/Legacy/Disgraceland/Legacy - Disgraceland Quick Notes.md`; a nota ativa agora é um índice de Omnisvera.
- [x] `EARTHROPO/01 - Ecos do Mundo Perdido.md` — capítulo legado arquivado; o caminho ativo agora contém apenas o outline de Omnisvera.
- [x] `Workflow/Legacy/Disgraceland/Legacy - Disgraceland OUTLINES.md` — arquivado como fonte.
- [x] `Workflow/Legacy/Disgraceland/Legacy - Disgraceland Scratch Notes.md` — arquivado como fonte.
- [x] `Workflow/Vault Report.md` — dashboard de Disgraceland arquivado; relatório ativo refeito para Omnisvera.
- [x] `Workflow/Format Audit Report.md` — relatório antigo substituído pelo estado atual.
- [x] Calendarium de Tribucia — configuração original preservada como template; calendário ativo migrado para o rascunho de Omnisvera.
- [x] Snippet de perfil — renomeado para `omnisvera-profile`, mantendo a classe antiga como alias de compatibilidade.

## Templates e ferramentas a preservar

- [x] `Workflow/Templates/Character Template.md`
- [x] `Workflow/Charts.md` — consultas antigas removidas e painel adaptado.
- [x] `Workflow/Property Key Dashboard.md` — preservado como ferramenta técnica com frontmatter explícito.
- [x] Plugins, snippets e configurações do Obsidian.
- [x] Frontmatter herdado quando necessário ao funcionamento visual.
- [x] `scriptwrite.css` e classes regionais antigas — preservados como compatibilidade de template; não são usados como lore ativa.

## Conteúdo de Omnisvera ainda em revisão

- [ ] `CULTURE.md`
- [ ] `ECONOMY.md`
- [ ] `LORE.md`
- [ ] `TIMELINE.md`
- [x] Fontes de regras de Old Dragon — fontes oficiais, independentes e legadas classificadas em `Workflow/RULES_SOURCES.md`.
- [x] Classes-base — notas ativas de Guerreiro, Ladrão, Clérigo e Mago reescritas como resumos de OD2; versões anteriores arquivadas.
- [ ] Raças e terminologia racial.
- [ ] Religiões.
- [ ] Facções ainda não consolidadas.
- [x] Validação técnica de Dataview, DataCards, frontmatter e Leaflet — registrada em `Workflow/Runtime Audit Report.md`.
- [x] Mapas Leaflet — IDs, imagens e links ativos validados; estado persistido de Tribucia isolado dos mapas ativos.
- [x] Arquivo de legado — notas narrativas antigas agrupadas em `Workflow/Legacy/`.
- [ ] Revisar posições e nomes dos marcadores conforme a geografia canônica for definida.

## Placeholders deliberados

- [ ] [[Capital de Nimalia]] — falta nome próprio.
- [ ] [[Fortaleza de Gharok]] — falta posição definitiva.
- [ ] [[Campos de Earthropo]] — região provisória.
- [ ] [[Bosque Sussurrante]] — existência não confirmada.
- [ ] [[Vale Dourado]] — existência não confirmada.
- [ ] [[Theron Elensar]] — identidade e história incompletas.

## Links essenciais ausentes

- [x] [[Mestre Odran Veyl]] — nota provisória criada a partir da história de Varkh.
- [x] [[OMNISVERA|Nota-raiz de Omnisvera]].
- [x] [[Véu Cinzento]] — nota de trabalho criada; a denominação inconsistente Véu do Eclipse foi retirada do conteúdo ativo.
- [x] Comandante Aldric Vane — mantido como texto provisório na Guarda Real, sem criar personagem antes da confirmação.

## Critério de conclusão

A migração estará concluída quando:

1. nenhuma nota narrativa de Disgraceland aparecer na navegação ativa;
2. todo conteúdo legado estiver identificado como `Legacy` ou fora das pastas canônicas;
3. relatórios técnicos refletirem o estado atual;
4. YAML, wikilinks e consultas estiverem validados;
5. os placeholders restantes forem decisões conscientes, não lacunas acidentais;
6. o assistente local e Codex lerem o mesmo handoff versionado;
7. GitHub e o backup local puderem restaurar o trabalho.
