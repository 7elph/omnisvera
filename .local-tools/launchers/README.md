# Iniciadores Omnisvera

Os tres CMDs do Desktop chamam os scripts deste diretorio. As pastas de
projetos continuam nos caminhos originais; nao mover o Vault para limpar o Desktop.

## Uso

- OpenCode: inicia/verifica 9Router, configura o MCP Omnisvera sem apagar os
  MCPs existentes, inicia OpenCode em localhost e publica HTTPS privado.
  Endereco: https://desktop-p30ui0j.taildecf09.ts.net:4096
- Companion: inicia o backend e publica HTTPS privado, sem perguntas e sem
  criar um link Cloudflare temporario.
  Endereco: https://desktop-p30ui0j.taildecf09.ts.net:8787
- MCP: inicia o HTTP local e o perfil OpenAI Tunnel omnisvera-mia.
  O OpenCode inicia uma fachada stdio propria, independente do tunnel.

O PC precisa estar ligado, com internet e sem suspensao. No celular, conectar
o Tailscale antes de abrir os links. O launcher nao altera energia/suspensao,
nao convida jogadores e nao modifica ACLs da tailnet.

Nao compartilhar acesso amplo ao PC com jogadores: configurar acesso somente
ao Companion antes de convida-los. A senha do OpenCode e os tokens individuais
do Companion continuam obrigatorios. A publicacao MCP preexistente na porta
8765 foi preservada; os iniciadores e a integracao OpenCode nao dependem dela.

## Credenciais e limites

As credenciais sao carregadas do ambiente autorizado e guardadas via DPAPI em
.assistant-runtime/launchers/*.dpapi (fora do Git, ligadas ao usuario Windows).
Nao imprimir o conteudo desses arquivos ou os valores das variaveis.

Se a runtime API key ainda nao foi salva, executar uma unica vez:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .local-tools\launchers\setup_credentials.ps1 -Name CONTROL_PLANE_API_KEY

Digitar a chave somente na janela local. Nenhuma chave e criada automaticamente.
Sem ela, uma instancia de tunnel ja ativa pode funcionar, mas nao e possivel
garantir seu reinicio apos desligar o PC. A conexao local do OpenCode continua
independente disso.

O MCP no OpenCode expoe somente system.health, get_handoff,
get_companion_state, memory.get e memory.list, com client=opencode.
Nao expoe propostas, auditorias com efeitos ou escritas.

## Verificacao

Os scripts aceitam -NoBrowser em OpenCode e Companion. Rodar novamente deve
reutilizar servicos ativos, conferir saude e reaplicar apenas a publicacao da
porta correspondente. Tailscale Serve usa --bg, persistente apos reinicio
do Tailscale; os aplicativos sao iniciados pelos respectivos CMDs.

Logs dos launchers: .assistant-runtime/launchers/.
Logs do Core HTTP: %TEMP%/omnisvera-mcp-http.*.log.
Teste MCP:

    .omnisvera-tools/Scripts/python.exe -m unittest discover -s .local-tools/tests -v

configure_opencode.ps1 preserva as outras entradas e cria backup do JSON
global antes da primeira mudanca. Nao altera opencode.jsonc.
