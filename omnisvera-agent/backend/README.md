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
$env:OLLAMA_MODEL="qwen2.5:1.5b"
```

Se o modelo acima não estiver instalado, use um modelo local existente. No notebook atual do Sage, os modelos preparados são:

```powershell
$env:OLLAMA_MODEL="omnisvera-fast:latest"
# ou
$env:OLLAMA_MODEL="omnisvera-local:latest"
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

## Fluxo inicial

1. Subir Ollama no notebook.
2. Subir backend.
3. Rodar `POST /index/rebuild`.
4. Subir frontend.
5. Abrir o IP do notebook no celular.

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
