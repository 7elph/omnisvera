# Fog e acesso público — 13/10/2026

## Ativado

- O Funnel HTTPS 443 existente foi desligado/religado, mantendo backend 8787, outras portas e credenciais. DNS público antes retornava NXDOMAIN no Google e Cloudflare; depois ambos publicaram os IPs do Funnel. GET pelo IP público com hostname/TLS original confirmou frontend e fichas proprietárias de Morthak e Vezemir com HTTP 200.
- Não prova conectividade nas redes físicas dos jogadores; seus resolvers podem manter o erro anterior em cache por alguns minutos.
- A tentativa de criar alternativa Cloudflare foi rejeitada pela revisão de segurança, sem executar a criação. Não houve necessidade de novo domínio após o Tailscale recuperar.

## Interface

- Fog aberta por padrão, antes da biblioteca, no topo de Mapas.
- Drawer dessa aba usa altura natural, sem ocupar uma tela adicional dentro do scroll lateral.
- Editor e início de pintura aguardam a identidade do mapa atual; evita salvar no mapa `default` antes de carregar o mapa real.
- Mesmas camadas, pincel, densidade, persistência e permissões anteriores. Nenhum comando desta tarefa alterou a fog operacional.

## Checks

- Backend: 665 testes passaram.
- Frontend: 248 testes passaram; typecheck e build passaram.
- Teste RED confirmou controles antes ocultos abaixo da biblioteca; teste GREEN passou após o ajuste.
- Smoke Playwright em fixture TEMP/8874: desktop, mobile, pintura salva, reload e controles exclusivos do Mestre passaram. Fixture encerrada ao terminar.
- Primeira tentativa de build/testes teve leitura do esbuild bloqueada pelo sandbox; repetição autorizada passou. Primeira tentativa de smoke revelou o problema de pintar antes de carregar o mapa; após guarda e espera explícita, passou.
- Aviso de bundles grandes permanece. Sem restart do backend, commit ou push.

## Arquivos

- `frontend/src/pages/SessionWorkspace.tsx`
- `frontend/src/components/mapManagement.css`
- `frontend/tests/map-management.test.cjs`
- `frontend/tests/fog-controls-smoke.cjs`
- Este documento.

Alterações preexistentes desses arquivos e do restante do worktree foram preservadas.
