# Hospedar o Companion em outra máquina

Branch: `devin/create-omnisvera-class-standard`. O diretório da aplicação é
`omnisvera-agent/`. Este guia substitui as instruções antigas de MVP somente leitura.
O backend serve a interface compilada e grava fichas, inventários, mapas e combate
no SQLite. Não precisa manter o notebook original ligado após a transferência.

## Dois componentes da entrega

1. Código público do GitHub, incluindo dependências e scripts abaixo.
2. Pacote **privado** da campanha, entregue separadamente por canal seguro.
   Contém banco, acessos, notas privadas do Mestre, mídias e rascunhos de imagens.
   Quem hospeda tem acesso administrativo a esses dados: escolha pessoa de confiança.
   Nunca anexe esse pacote a issue, release ou commit público.

O pacote contém manifesto versionado e hashes por arquivo; não carrega modelos,
conectores de IA, backups antigos, caches, dependências ou credenciais de provedores.
PNG, SVG, fotos, PDFs, áudio/vídeo e documentos do Vault são copiados com os arquivos
de licença. Sprites persistidos no banco também acompanham o snapshot.
A fila privada de preparação/Cenas pode acompanhar o pacote com `--workshop`.
Ela é restaurada em `host-data/state/ai-workshop.sqlite3`; processos, locks e
modelos não são reiniciados. Jobs vinculados a caminhos da origem precisam de
revisão antes de voltar a executar, sem geração automática durante a migração.

## Instalação Windows

Requisitos: Git, Python e Node/npm. O ensaio de instalação usa Python 3.14 e Node 24.
Em PowerShell, usando uma pasta de sua escolha:

```powershell
git clone --branch devin/create-omnisvera-class-standard --single-branch https://github.com/7elph/omnisvera.git
cd omnisvera/omnisvera-agent
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-host.txt
cd frontend
npm ci
npm run build
cd ..
backend/.venv/Scripts/python.exe backend/scripts/transfer_bundle.py restore --bundle "C:/caminho/companion.private.zip" --destination host-data
backend/.venv/Scripts/python.exe serve_companion.py --check
backend/.venv/Scripts/python.exe serve_companion.py
```

Abra `http://127.0.0.1:8787`. Os tokens importados continuam os mesmos; o launcher
não os imprime nem os troca. Use os links/acessos privados já fornecidos pelo Mestre.
`--check` não inicia o servidor. O importador exige um destino inexistente, valida
integridade/hashes/caminhos e nunca sobrescreve uma instalação operacional.

Para iniciar em segundo plano a cada login desse usuário, após a instalação:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./install_host_task.ps1
```

A tarefa roda sem elevação, com janela oculta e log em `host-data/logs/server.log`.
O parâmetro de execução vale somente para esse processo, sem alterar a política
global do Windows; evita o bloqueio de scripts em uma instalação nova.
Inicia no próximo login; não fecha servidores existentes. Para operar sem login,
configure uma conta de serviço no host ou use o serviço Linux abaixo. A tarefa
não é instalada no notebook de origem durante a preparação desta entrega.

## Linux

Use os mesmos arquivos e etapas, trocando os executáveis do ambiente virtual:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-host.txt
cd frontend && npm ci && npm run build && cd ..
backend/.venv/bin/python backend/scripts/transfer_bundle.py restore --bundle /caminho/companion.private.zip --destination host-data
backend/.venv/bin/python serve_companion.py --check
backend/.venv/bin/python serve_companion.py
```

O clone e o `cd` iniciais são iguais. O exemplo `companion.service.example` deve
ser ajustado ao usuário/diretório reais antes de instalá-lo em systemd. Não
declare validação em Linux apenas porque o ensaio Windows passou.

## HTTPS e rede

O launcher escuta somente em loopback por padrão. Configure HTTPS no host novo
com seu proxy/túnel. Para Tailscale Funnel já instalado e autorizado nesse host:

```sh
tailscale funnel --bg http://127.0.0.1:8787
```

Use o endereço fornecido pelo **host novo** nos celulares. O domínio
`desktop-p30ui0j.taildecf09.ts.net` pertence ao dispositivo antigo; não é transferido
pelo Git ou pelo backup. Não publique a porta do Ollama. Tokens são obrigatórios
e a separação Mestre/Jogador continua sendo aplicada nas APIs.

## Configuração e IA

Os padrões procuram `host-data/vault` e `host-data/state` ao lado do launcher.
Se precisar mudar, copie `.env.host.example` para `.env.host` e use caminhos
absolutos. Variáveis do processo prevalecem. `.env.host` e `host-data/` são ignorados
pelo Git. Não use `start_backend.ps1 -NoBuild` para uma instalação sem frontend.

O VTT usa o backend normal; chat/geração de IA dependem de Ollama/provedores
configurados no host novo. Credenciais de nuvem, modelos e executores OpenCode
não são transferidos automaticamente nem necessários para servir fichas e mapas.

Para desenvolvimento, a suíte backend completa também usa as dependências de
`backend/requirements-observer.txt`; elas não são exigidas pelo servidor web.
Testes frontend de preparação privada ficam como skip se os arquivos privados
de sessão não estiverem presentes. Eles não são publicados no GitHub.

## Exportação na origem e troca definitiva

O exportador usa a API de backup SQLite com origem somente leitura, incluindo
transações já confirmadas no WAL, e confere `quick_check`. Exemplo na origem:

```powershell
python backend/scripts/transfer_bundle.py export --vault "C:/caminho/OMNISVERA" --database "C:/caminho/omnisvera_companion.sqlite3" --tokens "C:/caminho/access_tokens.json" --output "C:/Transferencia/companion.private.zip" --code-ref "COMMIT_PUBLICADO"
```

O pacote precisa ficar fora do Vault/repositório. Guarde também o SHA-256 retornado.
Para preservar a fila de Cenas, acrescente `--workshop` com o caminho da base
`.autonomy/runtime/ai-workshop.sqlite3` da aplicação de origem.
Na troca definitiva, pare novas ações no host antigo, faça um snapshot final e
importe esse pacote antes de liberar o novo endereço. Não mantenha dois bancos
aceitando ações: eles divergiriam. A preparação do pacote não encerra a mesa atual.
Confirme no destino login de Mestre/jogador, quatro fichas, mapas/imagens, estoque,
compra/venda e reload antes de desativar a origem. Faça ensaios destrutivos em
fixture isolada, nunca nas fichas importadas reais.
