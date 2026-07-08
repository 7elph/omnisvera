# Omnisvera Companion

MVP local para acessar o vault Omnisvera pelo celular via navegador/PWA.

## Como funciona

- O notebook roda o backend FastAPI.
- O backend lê o vault em Markdown, cria índice SQLite local e chama o Ollama via `localhost:11434`.
- O celular acessa o webapp pelo navegador.
- O Ollama não é exposto diretamente.
- O MVP é somente leitura: não altera notas do vault.

## Rodar em casa, na mesma Wi-Fi

```powershell
cd C:\Users\delib\Desktop\OMNISVERA\omnisvera-agent
.\start_companion.ps1
```

O terminal mostra:

- URL local;
- URL da rede Wi-Fi;
- token de acesso.

No celular, se estiver na mesma Wi-Fi, abra a URL da rede.

## Rodar fora de casa

Em um terminal:

```powershell
cd C:\Users\delib\Desktop\OMNISVERA\omnisvera-agent
.\start_companion.ps1
```

Em outro terminal:

```powershell
cd C:\Users\delib\Desktop\OMNISVERA\omnisvera-agent
.\start_ngrok_tunnel.ps1
```

Abra a URL pública HTTPS impressa pelo ngrok no celular.

Use o token impresso pelo `start_companion.ps1`.

## Modelos Ollama

Por padrão, o script usa:

```txt
omnisvera-fast:latest
```

Também pode usar:

```powershell
.\start_companion.ps1 -Model "omnisvera-local:latest"
```

## Aviso de segurança

O token protege o backend, mas este MVP ainda é uma ferramenta local de campanha. Não publique URL/token em lugar público.

Se for liberar para jogadores, o ideal é criar uma versão player-safe com índice filtrado por `visibility`.
