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

### 2026-06-24 — Sage — devin/create-missing-raziel-notes-batch-01

**IA executora:** Cascade  
**Solicitante:** Sage  
**Branch:** devin/create-missing-raziel-notes-batch-01  
**Commit(s):** Pendente  
**Tipo de tarefa:** Criação de notas Draft de suporte ao arco de Raziel  
**Arquivos alterados:**  
- Workflow/MISSING_NOTES_BACKLOG.md (novo)
- Factions/Clã Sanguinallis.md (novo)
- Characters/Individual/Lorde Malakar.md (novo)
- Characters/Individual/Kaelen, o Flagelo.md (novo)
- Characters/Individual/Vandor, o Senhor das Bestas.md (novo)
- Lore/Ancião Primordial.md (novo)
- Lore/Sangue Antigo.md (novo)

**Mudou cânone?** Não (todas as notas são Draft/Em desenvolvimento)  
**Mudou mídia?** Não  
**Mudou estrutura?** Sim (notas Draft adicionadas)  
**Resumo:**  
Criou Batch 01 de notas faltantes focado no arco de Raziel. Todas as notas foram criadas como Draft/Em desenvolvimento com canon_status: Draft. Conteúdo baseado apenas em fontes internas existentes (Raziel.md, EARTHROPO/00 - O Retorno de Raziel.md, Items, Locations). Incertezas foram marcadas como "Pendente de confirmação do Sage". Nenhuma estatística de jogo, data exata, origem definitiva ou regra final foi definida.

**Pendências:**  
- Confirmação do Sage sobre origem e natureza do Ancião Primordial
- Confirmação do Sage sobre origem e natureza do Sangue Antigo
- Confirmação do Sage sobre detalhes do Clã Sanguinallis
- Confirmação do Sage sobre detalhes de Lorde Malakar, Kaelen e Vandor
- Definição de regras mecânicas para vampiro, hemomancia e regeneração

**Status:** Pendente de revisão do Sage
