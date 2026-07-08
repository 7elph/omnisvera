# Omnisvera Companion — Guia Operacional

> [!IMPORTANT]
> Este documento descreve o estado atual do webapp local do Omnisvera.
> O Companion é uma camada de consulta do vault para mesa, celular e IA local.
> Ele não substitui o Obsidian como fonte canônica.

## Objetivo

O Omnisvera Companion serve para:

- consultar notas do vault pelo celular;
- mostrar conteúdo liberado para jogadores sem abrir bastidores do mestre;
- conversar com o vault usando Ollama local;
- abrir fontes usadas pela resposta;
- acelerar preparação de sessão para o Mestre.

## Modos

| Modo | Uso | Escopo |
|---|---|---|
| Jogador | Consulta em mesa | Apenas notas `player-safe` |
| Mestre | Preparação e bastidor | Vault completo indexado |

## Regra player-safe

O modo jogador só deve mostrar notas que passem pelos filtros:

- `visibility: Jogadores` ou `visibility: Público`;
- `gm_secret` diferente de `true`;
- `spoiler_level` diferente de `medium` e `heavy`;
- fora de `Workflow/`, `Templates/`, `.obsidian/` e arquivos internos;
- sem caminhos bloqueados como `CAMPANHA/ESTADO_DA_CAMPANHA.md`.

Quando uma nota existe mas não está liberada, o chat deve bloquear a resposta em vez de improvisar com uma nota lateral.

## Perguntas boas para jogadores

- Quem é Vezemir?
- Quem é Varkh?
- Quem é Raziel?
- Quem é Morthak?
- Quem são os personagens jogadores?
- Quais missões estão ativas?
- Quais rumores estão ativos?
- O que aconteceu até agora?
- O que sabemos sobre Nimalis?

## Perguntas boas para o Mestre

- O que preciso preparar para a próxima sessão?
- Quais segredos não devo revelar aos jogadores?
- Quais NPCs entram na sessão 01?
- Quais pistas apontam para remédios falsos?
- Quais notas precisam revisão?

## Reindexar

Reindexar atualiza o banco local SQLite usado pelo app.

Use quando:

- uma nota foi criada;
- frontmatter mudou;
- uma imagem/caminho foi corrigido;
- o chat não encontra uma nota recém-editada.

No app, o botão aparece apenas no modo Mestre.

## Validação rápida do RAG

Rodar na raiz do vault:

```powershell
python omnisvera-agent/backend/rag_smoke_test.py
```

Resultado esperado:

- Vezemir usa `Characters/Individual/Vezemir.md`;
- Raziel usa `Characters/Individual/Raziel.md`;
- Varkh usa `Characters/Individual/Varkh Nimalis.md`;
- Morthak usa `Characters/Individual/Morthak.md`;
- missões e rumores vêm de `CAMPANHA/Quests/` e `CAMPANHA/Rumors/`;
- perguntas sobre nota não liberada no modo jogador são bloqueadas.

## Princípio de resposta

O chat deve:

- responder primeiro;
- citar fontes separadamente;
- não inventar cânone;
- não trocar o assunto principal por item relacionado;
- preferir nota exata quando existir;
- mostrar aviso quando o contexto for insuficiente;
- sugerir próximas perguntas úteis.

## Próximas melhorias recomendadas

- criar página de personagem do jogador com inventário, missões e rumores ligados;
- permitir favoritos locais no navegador;
- criar visão “Sessão de hoje” separada para jogadores;
- adicionar busca por tags com chips visuais;
- criar validação automática antes de abrir o app para mesa.
