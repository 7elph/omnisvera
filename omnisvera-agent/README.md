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
- token do Mestre;
- token dos Jogadores.

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

## Modos de acesso

O Companion possui dois modos:

| Modo | O que vê | Token |
|---|---|---|
| Mestre | Todo o índice do vault | Token do Mestre |
| Jogador | Apenas notas player-safe | Token dos Jogadores |

Uma nota é considerada player-safe quando:

- `visibility` é `Jogadores` ou `Público`;
- `gm_secret` não é `true`;
- `spoiler_level` não é `medium` nem `heavy`;
- a nota não está em pastas técnicas como `Workflow/`, `Templates/` ou `.obsidian/`.

Os endpoints do backend também são separados:

```txt
/gm/search
/gm/chat
/gm/notes

/player/search
/player/chat
/player/notes
/player/dashboard
```

## Modelos Ollama

Por padrão, o script usa:

```txt
omnisvera-fast:latest
```

O perfil recomendado para o notebook é:

```powershell
.\start_companion.ps1 -ResponseMode fast
```

Para testar uma resposta fundamentada mais lenta:

```powershell
.\start_companion.ps1 -ResponseMode grounded -QualityModel "qwen3:4b"
```

## Aviso de segurança

O token protege o backend, mas este MVP ainda é uma ferramenta local de campanha. Não publique URL/token em lugar público.

Para jogadores, compartilhe somente o token dos Jogadores. O token do Mestre abre notas de mestre e segredos.
