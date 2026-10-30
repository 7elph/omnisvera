# Cards e alcance no mapa — 14/10

Clique no card para iniciar a ação. Campos de arma, quantidade e forma continuam escolhas;
clicar neles não conjura. Comandos nativos preservam permissões, orçamento e idempotência.
Cards sem mecânica executável continuam informativos. Cards de descrição racial/classe não mudaram.
Leitura de card ativo: Shift+clique ou menu de contexto no ícone/nome (inclui gesto de contexto
do navegador móvel). Não executa habilidade; usa as descrições/imagens já existentes.

O overlay ocupa a imagem inteira, acima de grid/fog e abaixo dos pins. Branco translúcido
marca o alcance lógico; o contorno circular é referência visual em metros. A região elegível
segue a distância configurada do grid (Chebyshev provisório ou Manhattan), sem mudar regras
de diagonal. Alcance maior que o mapa ilumina o mapa inteiro; o contorno pode ficar fora dele.
Ainda não há paredes, visão, iluminação ou bloqueio por obstáculos.

Relâmpago: exceção aprovada pelo Mestre neste corte, até **3 alvos**, alcance **40 + 10 m/nível**,
uma JPD por alvo e uma rolagem de dano atual compartilhada (metade ao resistir).
Não é implementação de linha/bifurcação/reflexões. O modo manual de mapas sem grid permanece
compatível, mas também respeita três alvos e uma JP por alvo; contatos antigos não multiplicam JP.
Selecionar/cancelar não gasta. Terceiro alvo abre Sim/Não. Repetir um selecionado oferece
Deselecionar, Terminar ação com 1–2 alvos ou Continuar selecionando. Backend rejeita duplicados,
alvos mortos, sem posições, fora do alcance, fora da arena e quantidade acima de três.
Um comando transacional cobra uma vez, aplica o resultado e registra ledger/realtime existentes.

Mestre e jogador usam o card de combate real junto à ficha. A versão compacta não contém
prévia de jogadores nem editor de efeitos/multiataque; administração permanece no painel Mestre.
Título do mapa no Mestre é o seletor existente; ação redundante “Ficha da entidade” foi retirada.

Arquivos principais: `frontend/src/components/{TargetingOverlay,AttackTargetLine,TargetConfirmation,
SpellCard,SpellTargetControl,VineBraceletControl,DornProtocolControls,CombatEncounterPanel,SheetDetail}.tsx`,
`cardActivation.ts`, `gridTargetSelection.ts`; `frontend/src/{api.ts,styles.css,pages/SessionWorkspace.tsx}`;
`backend/app/{main,dorn_spells}.py`, `backend/test_dorn_spells.py`, `backend/scripts/run_sheet_test.py`.
Testes: `{targeting-surface,grid-target-selection,combat-sync-recovery,session6-rewards}.test.cjs`
e smokes `{grid-action-flow,range-multitarget,approved-spells,vezemir-inventory}-smoke.cjs`.
O smoke `morthak-new-spell-art-smoke.cjs` verifica o gesto secundário de descrição.

Checks completos: backend 779, frontend 275; typecheck/build PASS.
Ensaio visual isolado e ativação devem ser registrados após conclusão. Não prova redes distintas.

Primeiro MCP `test-50314af9f9dd467c8a9d97e783eeda3b`: 4 cenários API PASS,
fichas e fluxo dos quatro cards PASS; seleção múltipla FAIL por clique durante carregamento
que abria a ficha do pin. O frontend agora retém o modo mira enquanto aguarda o backend,
sem abrir essa ficha. A repetição visual usa resposta atrasada controlada e não força clicks.

Segundo MCP `test-5b268703069447299575fbe791b9a0c8`: seleção múltipla PASS (incluindo atraso,
desktop/mobile e reload); FAIL no ensaio posterior por clicar Magia da Morte durante a
sincronização de encerramento dos clones. O runner passa a aguardar o comando habilitado
antes do clique real no card; cards indisponíveis têm indicação visual esmaecida.

Terceiro MCP `test-2238be51df1d4fa1805190a199b4f6ba`: ações, múltiplos alvos, magias e design
PASS; FAIL no teste de artes que ainda abria descrição pelo clique comum. Leitura foi mantida
como gesto secundário, sem botão extra; o smoke de artes acompanha esse contrato.

## Resultado final e ativação

MCP `test-cca0177ff681423fb3a0fc145f5ea8b6`: PASS, quatro cenários API selecionados e
sete scripts visuais PASS, incluindo dados aplicados em 1/3 alvos, atraso controlado,
descrições/imagens, cancelamento, dois clientes locais de Clonagem e reload.
Capturas de desktop e viewport móvel foram conferidas. Não certifica celular físico/redes distintas.
Suítes completas repetidas após a regra final: backend 779 e frontend 275 PASS; typecheck/build PASS.
Persistem avisos existentes de conexões SQLite/dep­recações e chunks Vite acima de 500 KB.

Backend 8787 reiniciado em 14/10, 14:48 (PID 78724); Tailscale não foi reiniciado.
Backup: `C:\Users\delib\OmnisveraBackups\pre-range-activation-20261014-144813`.
Health local/público e fichas dos três jogadores: 200. Relâmpago: 200, grid, alcance 90 m no
nível atual 5 e limite 3. Comparação de fichas, definições, inventário, combate/efeitos,
pins, posições, sessões e cenas: hashes idênticos. Valores de tokens preservados.
Não se conjurou, moveu ou descansou em produção. Sem staging, commit ou push.
