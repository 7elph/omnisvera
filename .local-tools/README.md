# Ferramentas Locais de Auditoria do Vault

Scripts Python para validação e auditoria do vault Obsidian Omnisvera.

## Scripts

### validate_frontmatter.py

Valida frontmatter YAML em notas Markdown.

**O que valida:**
- Presença de frontmatter YAML
- Frontmatter bem formado (aberto e fechado corretamente)
- Campos vazios importantes (title, name, type, category)

**Como rodar:**
```powershell
python .local-tools/validate_frontmatter.py
python .local-tools/validate_frontmatter.py . --ignore-legacy
```

**Saída:**
- Total de notas analisadas
- Notas sem frontmatter
- Notas com frontmatter inválido
- Notas com campos vazios importantes

---

### validate_links.py

Valida wikilinks em notas Markdown.

**O que valida:**
- Wikilinks [[...]]
- Links com aliases [[Nota|Texto]]
- Se o destino existe como nota .md
- Links quebrados

**Como rodar:**
```powershell
python .local-tools/validate_links.py
python .local-tools/validate_links.py . --ignore-legacy
```

**Saída:**
- Total de wikilinks encontrados
- Links resolvidos
- Links quebrados
- Arquivo e linha do problema

---

### validate_media.py

Valida referências de mídia em notas Markdown.

**O que valida:**
- Referências a arquivos em zz_media
- Se os arquivos existem
- Referências quebradas em notas ativas vs legacy
- Imagens órfãs não referenciadas

**Como rodar:**
```powershell
python .local-tools/validate_media.py
python .local-tools/validate_media.py . --ignore-legacy
```

**Saída:**
- Total de referências de mídia
- Referências válidas
- Referências quebradas ativas
- Referências quebradas em legacy
- Imagens órfãs

---

### vault_audit.py

Executa todos os validadores e gera relatório consolidado.

**O que faz:**
- Roda os três validadores
- Gera relatório em Markdown em Workflow/Reports/latest_vault_audit.md
- Inclui data/hora, branch atual, resumo Git
- Classifica riscos (críticos, médios)
- Fornece recomendação final (Seguro, Seguro com ressalvas, Não seguro)

**Como rodar:**
```powershell
python .local-tools/vault_audit.py
python .local-tools/vault_audit.py . --ignore-legacy
```

**Saída:**
- Relatório completo em Workflow/Reports/latest_vault_audit.md

---

## Comportamento Geral

- **Não modifica arquivos** - Apenas lê, valida e gera relatório
- **Ignora diretórios:** .git, .obsidian, .trash, node_modules, .venv, .local-tools
- **Trabalha com arquivos .md**
- **Flag --ignore-legacy:** Ignora Workflow/Legacy/ quando presente

## Requisitos

- Python 3.x
- Biblioteca padrão do Python (sem dependências externas)
- Compatível com Windows

## Exemplo de Uso Completo

```powershell
# Auditoria completa do vault
python .local-tools/vault_audit.py

# Auditoria ignorando legacy
python .local-tools/vault_audit.py . --ignore-legacy

# Validar apenas frontmatter
python .local-tools/validate_frontmatter.py

# Validar apenas links
python .local-tools/validate_links.py

# Validar apenas mídia
python .local-tools/validate_media.py
```

## Relatórios

Os relatórios são salvos em:
- `Workflow/Reports/latest_vault_audit.md` - Relatório mais recente
