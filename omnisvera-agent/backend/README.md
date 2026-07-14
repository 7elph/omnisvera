# Omnisvera Companion — Backend

Backend local somente leitura para consultar o vault Omnisvera pelo celular via webapp.

## Stack

- Python
- FastAPI
- SQLite
- Ollama via HTTP local

## Segurança do MVP

- O backend lê o vault, mas não altera notas.
- O Ollama não deve ser exposto diretamente na rede.
- O backend chama o Ollama em `localhost:11434`.
- O celular deve acessar apenas o backend/frontend na rede local.

## Configuração

Variáveis de ambiente:

```powershell
$env:OMNISVERA_VAULT_PATH="C:\Users\delib\Desktop\OMNISVERA"
$env:OLLAMA_BASE_URL="http://localhost:11434"
$env:OMNISVERA_FAST_MODEL="qwen2:1.5b"
$env:OMNISVERA_QUALITY_MODEL="llama-3.2-omnisvera-3b"
$env:OMNISVERA_EMBED_MODEL="nomic-embed-text"
$env:OMNISVERA_RESPONSE_MODE="grounded"
$env:OMNISVERA_MODEL_MODE="baseline" # baseline, candidate ou production
$env:OMNISVERA_TRAINING_CAPTURE_MODE="manual" # off, manual ou master_session
$env:OMNISVERA_UNREVIEWED_RETENTION_DAYS="30"
```

No modo `baseline`, `qwen2:1.5b` compõe respostas narrativas a partir de cartões
factuais validados. `candidate` e `production` selecionam o modelo Omnisvera;
se ele falhar, o backend tenta qwen2 e depois usa a resposta factual determinística.
Um candidato só deve ser promovido após os gates de `omnisvera-model/README.md`.

O backend pode atualizar o índice SQLite automaticamente quando arquivos `.md` mudam:

```powershell
$env:OMNISVERA_AUTO_REFRESH_INDEX="true"
$env:OMNISVERA_AUTO_REFRESH_INTERVAL_SECONDS="12"
```

Isso atualiza o corpo das notas no app após salvar no Obsidian. O índice semântico
`.local-index/vault.jsonl` continua manual para evitar recalcular embeddings a cada salvamento.

## Diagnóstico da voz narrativa

O modo `grounded` monta um cartão factual autorizado antes de chamar o Ollama.
O modelo só reescreve os fatos; nomes, números, relações, causas, motivações e
eventos novos são rejeitados por afirmação. Se a resposta não sobreviver à
validação, o backend monta uma resposta natural determinística.

Para registrar um diagnóstico local player-safe, sem expor o trace na API:

```powershell
$env:OMNISVERA_NARRATIVE_TRACE_PATH="C:\caminho\local\narrative-trace.jsonl"
```

O trace contém pergunta, intenção, fontes liberadas, cartão factual, prompt,
resposta bruta, afirmações rejeitadas, resposta final e tempos por etapa. Ele só
é escrito para o modo jogador e deve ficar em diretório ignorado pelo Git, como
`.local-index/`.

Testes principais:

```powershell
python ..\..\scripts\test_narrative_composer.py
python ..\..\scripts\test_narrative_quality.py
python ..\..\scripts\test_chat_question_battery.py
```

Se `OMNISVERA_VAULT_PATH` não for definido, o backend assume a raiz do repositório acima de `omnisvera-agent/`.

## Instalação

```powershell
cd omnisvera-agent/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Rodar

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8787
```

## Endpoints

- `GET /health`
- `POST /index/rebuild`
- `GET /notes`
- `GET /notes/{id}`
- `POST /search`
- `POST /chat`
- `POST /gm/training/interactions/capture`
- `GET /gm/training/examples`
- `PATCH /gm/training/examples/{id}`
- `POST /gm/training/examples/{id}/approve`
- `POST /gm/training/examples/{id}/reject`
- `GET /gm/training/stats`

Os endpoints de curadoria exigem `OMNISVERA_MASTER_TOKEN`; sem o token configurado,
o backend nega o painel por padrão. O guia operacional completo está em
`omnisvera-model/CURATION_FOR_SAGE.md`.

## Fluxo inicial

1. Subir Ollama no notebook.
2. Subir backend.
3. Rodar `POST /index/rebuild`.
4. Subir frontend.
5. Abrir o IP do notebook no celular.

## Perfis individuais de jogador

O launcher mantém um token coletivo e quatro tokens individuais no arquivo
local `data/access_tokens.json`, ignorado pelo Git. Os perfis atuais são
Vezemir, Varkh Nimalis, Raziel e Morthak.

Com um token individual, o jogador age apenas pelo próprio personagem, recebe
somente seu histórico de ações e possui uma área de descobertas particulares.
O Mestre revela ou revoga essas descobertas pelo Painel da Sessão. O token
coletivo permanece como acesso de compatibilidade para uma tela compartilhada.

## RAG Watchdog

O backend possui um verificador contínuo de qualidade do chat:

```powershell
$env:OMNISVERA_PLAYER_TOKEN="player-token-aqui"
$env:OMNISVERA_MASTER_TOKEN="master-token-aqui" # opcional, necessário só para --auto-rebuild
python .\rag_watchdog.py
```

Para deixar rodando em loop:

```powershell
.\start_rag_watchdog.ps1 -IntervalSeconds 300
```

Para rodar em loop e reconstruir o índice quando o vault mudar:

```powershell
.\start_rag_watchdog.ps1 -IntervalSeconds 300 -AutoRebuild
```

O watchdog não altera notas do vault e não edita código automaticamente. Ele:

- testa perguntas de regressão;
- verifica fontes esperadas;
- detecta termos técnicos vazando para jogadores;
- detecta respostas repetidas ou longas demais;
- reconstrói o índice apenas se `-AutoRebuild` for usado;
- gera relatório em `Workflow/_audit/App_RAG/RAG_WATCHDOG_REPORT.md`;
- registra histórico em `omnisvera-agent/backend/data/rag_watchdog_runs.jsonl`.
