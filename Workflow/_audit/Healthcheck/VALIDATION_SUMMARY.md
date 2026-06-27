# Validation Summary

Data: 2026-06-27

## Comandos principais executados

```text
git branch --show-current
git status --short
git log --oneline -12
git remote -v
git fetch origin
git status -sb
```

Resultado:

- Branch: `devin/create-omnisvera-class-standard`.
- Remoto sincronizado; sem indicação de branch remota à frente.
- Pendências locais antigas ainda presentes antes dos commits temáticos.

## Validação de Homes

Comandos equivalentes executados no PowerShell/rg:

```text
ls raiz filtrando Home*.md
busca por *home*.md e *dashboard*.md
rg para [[Home_Jogadores]]
rg para portal neutro / Home_Jogadores / Home_Mestre / Home dos Jogadores / dashboard do mestre
leitura de .obsidian/plugins/homepage/data.json
```

Resultado:

- `Home.md` existe na raiz.
- `Home_Mestre.md` existe na raiz.
- `Home_Jogadores.md` não existe na raiz.
- `Workflow/_archive/obsolete_review/Home_Jogadores_ARCHIVED.md` existe.
- Não há wikilinks operacionais para `[[Home_Jogadores]]`.
- O plugin Homepage aponta para `Home`.
- `Home.md` é a Home dos Jogadores.

## Validação de Home dos Jogadores

Comando:

```text
rg "Workflow/_audit|Workflow/Legacy|gm_secret: true|visibility: Mestre|spoiler_level: heavy|spoiler_level: medium" Home.md
```

Resultado:

- Nenhuma referência proibida encontrada em `Home.md`.

## Validação de frontmatter/YAML

Método:

- PyYAML não disponível.
- Checagem heurística conservadora via Python.

Resultado:

- 122 arquivos auditados.
- 94 `OK`.
- 26 `NO_FRONTMATTER`, principalmente documentação técnica.
- 2 `NEEDS_REVIEW`: `CULTURE.md`, `LATEST_NEWS.md`.
- 0 `BROKEN_FRONTMATTER`.
- 0 `INLINE_FRONTMATTER`.
- 0 `MISSING_CLOSING_DELIMITER`.
- 0 `YAML_PARSE_ERROR`.

## Arquivos corrigidos

Nenhum arquivo de frontmatter foi corrigido automaticamente.

## Arquivos que precisam revisão do Sage

- `CULTURE.md` — `tags: home` em formato escalar.
- `LATEST_NEWS.md` — `tags: home` em formato escalar.
- `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` — alterações locais antigas sobre Classes ainda precisam decisão.
- `Workflow/Property Key Dashboard.md` — já apontado em cleanup anterior como possível revisão futura.

## Problemas restantes

- Mídia continua com risco alto por referências quebradas/possíveis órfãs já documentadas.
- `visibility` ainda não está aplicado em massa.
- `sessions` ainda não está aplicado em massa.
- Tags RPG novas ainda não estão padronizadas.
- Alterações remanescentes em `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` não foram commitadas porque pertencem ao tema Classes/dashboard e precisam decisão.

## Conclusão

O vault está liberado para piloto pequeno de templates, mas não para migração em massa.

Próximo passo recomendado:

1. commitar relatórios de healthcheck;
2. commitar padrões seguros de mídia/classes em commits separados;
3. decidir o destino das alterações remanescentes em `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md`;
4. iniciar piloto com poucas notas.
