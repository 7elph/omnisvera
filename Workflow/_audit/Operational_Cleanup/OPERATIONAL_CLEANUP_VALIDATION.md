# Operational Cleanup Validation

Status: concluído em 2026-06-27.

## Escopo validado

- normalização de Markdown/frontmatter dos arquivos operacionais críticos;
- organização inicial de `Workflow/`;
- remoção física controlada de `Workflow/Legacy/Disgraceland/`;
- reestruturação de Cultura, Religião, Calendário e Timeline;
- documentação de ambiente local;
- validadores locais.

## Newlines e frontmatter

Script simples de newline/frontmatter executado contra:

- `Home.md`;
- `Home_Mestre.md`;
- `CULTURE.md`;
- `Religion/RELIGION.md`;
- `CALENDAR.md`;
- `TIMELINE.md`;
- `CAMPANHA/ESTADO_DA_CAMPANHA.md`;
- `Templates/RPG/Story.md`;
- `Workflow/OMNISVERA_TAG_BRIDGE_GUIDE.md`;
- `Workflow/OMNISVERA_VISIBILITY_AND_SPOILER_GUIDE.md`;
- `Workflow/OMNISVERA_LOCATION_TERRITORY_GUIDE.md`;
- `Workflow/OMNISVERA_SYSTEM_TAXONOMY.md`;
- `Workflow/OMNISVERA_SYSTEM_TAXONOMY_DECISIONS.md`.

Resultado: todos com quebras de linha reais e sem indício de corpo colapsado.

Arquivos com YAML parseado diretamente no ambiente `.omnisvera-tools`:

- `Home.md`;
- `Home_Mestre.md`;
- `CULTURE.md`;
- `Religion/RELIGION.md`;
- `CALENDAR.md`;
- `TIMELINE.md`;
- `CAMPANHA/ESTADO_DA_CAMPANHA.md`;
- `Templates/RPG/Story.md`.

Resultado: `YAML_OK` para todos esses arquivos.

Os guias `Workflow/OMNISVERA_*.md` não têm frontmatter por padrão; isso não foi tratado como erro nesta etapa.

## Validação de Homes/Templates

Busca executada em `Home.md`, `Home_Mestre.md` e `Templates` para:

- `Workflow/Legacy/Disgraceland`;
- `TRIBUCIA`;
- `player_known`;
- `life_status`;
- `handout_image`;
- `#session`.

Resultado: nenhum match.

## Remoção de Disgraceland

`Workflow/Legacy/Disgraceland/` foi removido fisicamente após auditoria.

Arquivos de preservação criados:

- `Workflow/_audit/Operational_Cleanup/DISGRACELAND_PHYSICAL_REMOVAL_AUDIT.md`;
- `Workflow/_archive/legacy_removal/DISGRACELAND_REMOVAL_SUMMARY.md`.

`Workflow/Legacy/` não foi removido, pois ainda contém `Old Dragon anterior` e o índice de arquivo.

## Ambiente local

Comando executado:

```powershell
python .local-tools/check_environment.py
```

Resultado:

| ferramenta | status |
|---|---|
| Python | encontrado |
| Git | encontrado |
| PowerShell | encontrado |
| Ollama | encontrado |
| VS Code | encontrado |
| GitHub CLI | encontrado |
| Git LFS | encontrado |
| Tesseract | encontrado |
| ImageMagick | encontrado |
| FFmpeg | ausente no PATH |
| ExifTool | encontrado |
| jq | encontrado, mas verificação de versão retornou acesso negado |
| yq | encontrado, mas verificação de versão retornou acesso negado |
| ripgrep | encontrado |

Ferramentas obrigatórias mínimas disponíveis: sim.

## Validadores locais

Comandos executados:

```powershell
python .local-tools/validate_frontmatter.py . --ignore-legacy
python .local-tools/validate_links.py . --ignore-legacy
python .local-tools/validate_media.py . --ignore-legacy
python .local-tools/vault_audit.py
```

Resultado resumido:

| validador | resultado |
|---|---|
| frontmatter | executou; reportou 250 notas analisadas, 118 sem frontmatter e 113 com frontmatter inválido |
| links | executou; reportou 2025 wikilinks, 872 resolvidos e 1153 quebrados |
| mídia | executou; reportou referências quebradas e 150 imagens órfãs |
| auditoria geral | executou e atualizou `Workflow/Reports/latest_vault_audit.md` |

Interpretação:

- os validadores rodam no ambiente atual;
- a dívida técnica ainda é grande;
- os problemas reportados não foram corrigidos em massa nesta etapa;
- a migração do lote 2 deve continuar controlada, não global.

## Busca por termos legados operacionais

Busca em áreas operacionais:

- `Home.md`;
- `Home_Mestre.md`;
- `Templates`;
- `Characters`;
- `Factions`;
- `Territories`;
- `Locations`;
- `Lore`;
- `Religion`;
- `Items`;
- `Bestiary`;
- `Rules`;
- `CAMPANHA`;
- documentos ativos `Workflow/OMNISVERA_*.md`.

Resultado:

- ocorrências de tags antigas permanecem nos mapas de taxonomia e guia de tags-ponte;
- isso é esperado e histórico/técnico;
- não foram encontradas ocorrências operacionais bloqueadoras em Homes/Templates.

## Classificação final

`READY_FOR_BATCH_2`, com restrição:

- lote 2 deve continuar pequeno e controlado;
- não executar migração em massa;
- corrigir frontmatter e links apenas nas notas selecionadas para o lote;
- tratar mídia órfã em etapa própria.

## Pendências

- Corrigir frontmatter inválido em lotes controlados.
- Corrigir links quebrados por prioridade narrativa/operacional.
- Resolver referências de mídia nas notas migradas.
- Decidir quais documentos históricos de `Workflow/` devem ser arquivados em uma etapa posterior.
- Instalar/adicionar FFmpeg ao PATH apenas se houver necessidade real de áudio/vídeo.
