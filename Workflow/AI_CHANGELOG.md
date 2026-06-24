# AI Changelog

Registro de alterações feitas por IAs/agentes no vault Omnisvera.

## Template de entrada

### YYYY-MM-DD — IA — Branch

**IA executora:**  
**Solicitante:** Sage  
**Branch:**  
**Commit(s):**  
**Tipo de tarefa:**  
**Arquivos alterados:**  
**Mudou cânone?** Sim/Não  
**Mudou mídia?** Sim/Não  
**Mudou estrutura?** Sim/Não  
**Resumo:**  
**Pendências:**  
**Status:** Pendente / Revisado / Aprovado / Rejeitado

## Histórico

### 2026-06-24 — Sage — codex/vault-consolidation

**IA executora:** Cascade  
**Solicitante:** Sage  
**Branch:** codex/vault-consolidation  
**Commit(s):** 115954e, bf95605  
**Tipo de tarefa:** Consolidação de vault e correção de referências  
**Arquivos alterados:**  
- .obsidian/plugins/obsidian-leaflet-plugin/data.json (restaurado)
- Classes/Alquimista.md (restaurado, cover atualizado)
- Classes/Clérigo.md (restaurado, cover atualizado)
- Classes/Ladrão.md (restaurado, cover atualizado)
- Classes/Mago.md (restaurado, cover atualizado)
- Religion/Caminho dos Errantes.md (restaurado)
- Workflow/CANON.md (restaurado)
- Home.md (sintaxe corrigida)
- GM/Home do Mestre.md (sintaxe corrigida)
- Locations/Fortaleza de Gharok.md (referência corrigida)
- ~200 imagens deletadas (legado de Disgraceland)
- ~30 imagens novas organizadas em subpastas
- ~130 notas .md modificadas (covers atualizados)

**Mudou cânone?** Não (apenas restaurou conteúdo existente)  
**Mudou mídia?** Sim (reorganização e atualização de covers)  
**Mudou estrutura?** Sim (organização de mídia em subpastas)  
**Resumo:**  
Consolidou estrutura do vault Omnisvera, organizou biblioteca de mídia em subpastas, adicionou novas imagens, atualizou covers em notas ativas, corrigiu referências quebradas ativas, restaurou Leaflet com mapas preservados, restaurou classes oficiais e conteúdo mecânico, restaurou Caminho dos Errantes como Draft, restaurou diretrizes de IA em CANON.md.

**Pendências:**  
- Referências quebradas restantes existem apenas em Workflow/Legacy ou documentação/exemplos
- Imagens ora.png, oric.PNG, mira.PNG não são referenciadas por notas ativas, mas podem ser restauradas futuramente
- Limpeza de Tribucia/Disgraceland no Leaflet deve ser feita depois, de forma cirúrgica

**Status:** Pendente de revisão final do Sage

### 2026-06-24 — Sage — devin/create-vault-audit-scripts

**IA executora:** Cascade  
**Solicitante:** Sage  
**Branch:** devin/create-vault-audit-scripts  
**Commit(s):** Pendente  
**Tipo de tarefa:** Criação de scripts de auditoria para vault  
**Arquivos alterados:**  
- .local-tools/validate_frontmatter.py (novo)
- .local-tools/validate_links.py (novo)
- .local-tools/validate_media.py (novo)
- .local-tools/vault_audit.py (novo)
- .local-tools/README.md (novo)
- Workflow/Reports/.gitkeep (novo)

**Mudou cânone?** Não  
**Mudou mídia?** Não  
**Mudou estrutura?** Sim (ferramentas de auditoria adicionadas)  
**Resumo:**  
Criou scripts Python locais para validação e auditoria do vault Obsidian. Scripts validam frontmatter YAML, wikilinks e referências de mídia. O vault_audit.py executa todos os validadores e gera relatório consolidado em Markdown. Scripts não modificam arquivos, apenas leem e reportam problemas.

**Pendências:**  
- Nenhuma

**Status:** Pendente de revisão do Sage
