---
obsidianUIMode: preview
NoteIcon: outline
NoteStatus: Active
status: Ativo
visibility: gm
tags:
  - workflow
  - assistant
  - ollama
  - protocol
---

# Protocolo do Assistente Local

## Função

A IA local é uma assistente de continuidade. Ela localiza evidências, resume estado, detecta candidatos a conflito e prepara propostas. Codex continua responsável por decisões delicadas, edição final, validação e commits.

## Fluxo

```text
Vault + CANON + MIGRATION_LEDGER
               ↓
       índice semântico local
               ↓
     pacote curto de evidências
               ↓
        modelo Ollama local
               ↓
        proposta não aplicada
               ↓
       revisão por Codex/usuário
               ↓
       edição validada + Git
```

## Modos permitidos

- **Consulta:** responder com fontes do vault.
- **Triagem:** classificar notas como migradas, provisórias, template ou legado.
- **Extração:** listar entidades, datas, lugares, relações e campos vazios.
- **Proposta:** preparar texto ou patch conceitual em `.local-proposals/`.
- **Contingência:** explicar o estado atual a partir de [[ASSISTANT_HANDOFF]].

## Modos proibidos

- Reescrever o cânone automaticamente.
- Fazer commits ou pushes sem Codex ou o usuário.
- Apagar material legado.
- Resolver conflitos narrativos por inferência.
- Alterar arquivos de plugin, Leaflet ou mídia em massa.

## Comandos

```powershell
# Estado compartilhado
.omnisvera-tools\Scripts\python.exe .local-tools\assistant_bridge.py status

# Pergunta fundamentada em fontes explícitas
.omnisvera-tools\Scripts\python.exe .local-tools\assistant_bridge.py ask "Liste apenas as informações confirmadas sobre Gharok" --file "Locations/Fortaleza de Gharok.md" --file "Workflow/CANON.md"

# Criar proposta local sem editar o vault
.omnisvera-tools\Scripts\python.exe .local-tools\assistant_bridge.py propose "Classifique as facções ainda provisórias" --file "Workflow/MIGRATION_LEDGER.md" --file "Workflow/CANON.md"
```

## Continuidade

O servidor `.local-tools/mcp_server.py` expõe esse estado por MCP local em `stdio`. Assim, novas sessões do Codex podem consultar o handoff, a migração, a busca semântica e o estado do Git sem depender de um endereço externo.

Uma proposta sem arquivos-fonte explícitos deve ser recusada. A busca semântica serve para encontrar candidatos; ela não autoriza o modelo a combinar trechos automaticamente.

## Restauração

Os ambientes, índices e pesos dos modelos não entram no Git. O código, os Modelfiles e o instalador entram.

```powershell
powershell -ExecutionPolicy Bypass -File .local-tools\bootstrap.ps1
```

Depois, adicionar o conteúdo de `.local-tools/codex-mcp-snippet.toml` ao arquivo `C:\Users\delib\.codex\config.toml` e reiniciar o Codex.
