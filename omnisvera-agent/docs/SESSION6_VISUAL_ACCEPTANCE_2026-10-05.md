# Aceitação visual/multicliente S6 — 2026-10-05

**Resultado: PARTIAL.** O circuito local de combate, efeito, invocação, fichas e recuperação foi observado em clientes reais de navegador. Distribuição final de loot e mesa multirrede continuam UNPROVEN. Nenhum PASS abaixo representa uma mesa com três aparelhos em redes distintas.

## A. Estado e checkpoint

- HEAD inicial: `d3a701e246469744b9acda165387ce4ed5d3267c`.
- Branch: `devin/create-omnisvera-class-standard`.
- Checkpoint local: `d8725db63f71d3f2bbf36604479ccc09a30fd506`, `fix: close S6 combat acceptance regressions`.
- Índice inicialmente vazio; staging somente por caminhos explícitos; conjunto conferido antes do commit. Exatamente cinco arquivos: `backend/app/main.py`, `backend/test_hemomante_techniques.py`, `backend/scripts/session6_acceptance.py`, `backend/test_session6_acceptance.py`, `docs/SESSION6_ACCEPTANCE_2026-10-05.md`.
- Depois do checkpoint, status do Companion: somente `.autonomy/` untracked. As alterações externas de Vault, personagens, itens, Obsidian e mídia continuaram presentes; não receberam escrita, staging, reset, stash ou commit. Não foi concluído um fingerprint agregado desses arquivos; não se afirma uma verificação criptográfica integral.
- Sem push. A correção visual deste relatório permanece sem staging/commit para revisão.

## Ambiente e modalidade de evidência

- Banco criado do zero por `session6_acceptance.py seed`: `%LOCALAPPDATA%/Temp/companion-s6-visual-20261005/test.sqlite3`.
- Servidor descartável: `cf01_probe.py serve`, porta `8872`; Vault temporário, credenciais fixture públicas do próprio harness. Não copiou banco operacional, tokens reais ou Vault.
- Build servido: `%LOCALAPPDATA%/Temp/companion-s6-acceptance-final-build-20261005`, não `frontend/dist` operacional.
- Sessão fixture 5: **Ensaio visual S6 — descartável**, número 99. Sessão, mapa, arma e inimigo preparados por API/harness; início de combate e demais ações descritas como UI foram efetivamente acionados no navegador.
- Três identidades simultâneas no Chrome: Mestre em `127.0.0.1:8872`, Vezemir em `localhost:8872`, Morthak em `localhost.:8872`. Origins distintos separaram armazenamento e autenticação. Um segundo tab GM permitiu continuar depois de o primeiro ficar preso em diálogo nativo.
- Não são três dispositivos nem três redes. Imagens de mapas/armas ausentes no fixture não foram diagnosticadas como defeito operacional. Inicialização também inclui registros estáticos de campanha distribuídos com o código, sem leitura do Vault real.

## B. Matriz visual

| Fluxo | Mestre | Jogador A — Vezemir | Jogador B — Morthak | Resultado/evidência |
| --- | --- | --- | --- | --- |
| Iniciar combate/iniciativa | Iniciativas 30/20/10 e início pela UI | Recebe turno e ações | Recebe turno de Vezemir; ações restritas | PASS local, transição automática para Mesa |
| Passar turno | Controle explícito disponível | Conclui turno | Recebe seu turno automaticamente | PASS local |
| Força Arcana/derivados | Efeito visível | Usa poder: Força 16→19, bônus +3→+4, dano 1d6→1d6+1, uso 1→0 | Estado compartilhado atualizado | PASS mecânico; FAIL de rótulo antes, PASS após correção |
| Duração/expiração | 2→1→ausente ao completar rodadas | Força volta a 16; reload durante efeito preservou 19 | Iniciativa/rodadas atualizadas | PASS local: rodadas 1→2→3, sem reduzir efeito duas vezes |
| Criar invocação | Recebe criatura e iniciativa | Recebe pin; não controla invocação alheia | Cria Esqueleto de Madeira, 10/10 PV, uso 1→0 | PASS local |
| Invocação ataca | Recebe resultado/PV | Observa inimigo 0/12 | Seleciona alvo, rola, confirma dano, orçamento 0 | PASS: resultado 3+2=5 contra CA1, dano6, inimigo1→0; invocação10PV e Morthak4PV independentes |
| Invocação/reconexão | Continua na iniciativa | Estado atualizado | Reload preserva proprietário, ficha, ataque, orçamento e vínculo | PASS local; remoção manual/duração temporal não ensaiadas, UNPROVEN |
| Loot: gerar privado | Sorteia carregado após 0PV; draft11PP | Não vê recompensa antes de revelar | Não vê recompensa antes de revelar | PASS local |
| Loot: revelar | Revela pela UI | Registro revelado observado | Recebe registro11PP automaticamente | PASS local |
| Loot: distribuição final | Abre confirmação nativa; automação não consegue aceitar | Sem controles GM | Sem controles GM | UNPROVEN; não se atribui defeito ao produto |
| Dorn: ficha/entrada incremental | Ficha completa disponível; iniciativa15 inserida sem reiniciar combate | Header de Dorn não selecionável | Header de Dorn não selecionável | PASS para PV13/CA11, atributos, inventário, recursos e magias; XP em superfície dedicada não comprovado visualmente |
| Dorn: magia/reload | Usa Escudo Arcano1→0, registro legível; recarga preserva ficha e turno | Recebe registro público | Recebe registro público | PASS de consumo e persistência; efeito é assistido pelo Mestre conforme descrição existente, não se inventou aplicação automática |
| Vezemir1→2 | Dado5; prévia BA1→2, PV12→20; confirma | Recebe20/20 e nível2 sem refresh manual | Recebe header atualizado | PASS; reabrir mostra avanço registrado, sem novo benefício |
| Raziel1→2 | Dado4; PV12→19; sangue5 e Sentido bloqueado preservados | Header atualizado | Header atualizado | PASS; reabrir bloqueia duplicação |
| Morthak1→2 | Dado2; PV4→9; capacidade apresentada sem recarga | Header atualizado | Ficha9/9/Nv2; reload preserva | PASS; reabrir bloqueia duplicação |
| Dorn: reconciliaçãoNv2 | Prévia sem alterações pendentes; confirma sem mudar13PV | Sem edição | Sem edição | PASS dentro do suporte existente; avanço2→3/XP pela UI não ensaiado, UNPROVEN |
| Encerrar combate | Encerra pela UI | Volta à exploração | Volta à exploração | PASS local, posições restauradas |
| Descanso existente | Descanso geral pela UI | Força Arcana0→1 | Levantar Esqueleto0→1 | PASS local; recursos de Dorn também recuperados, registro narrativo separado por ficha |

## C. Sincronização

Sem refresh manual para: início/fim, troca de turnos, Força Arcana, entrada/ataque da invocação, dano no inimigo, revelação de loot, progressões e descanso. Reload intencional foi usado para testar persistência, não para destravar atualização. Placeholders de autenticação no carregamento inicial resolveram após o bootstrap; não foram tratados como perda de credenciais.

Nenhuma divergência persistente, duplicação ou vazamento GM foi observado nesses cenários. Leituras imediatas após ações às vezes antecederam a resposta/polling; estados subsequentes convergiram sem intervenção. Console capturado nos três clientes sem erros no trecho observado. Isso não é teste de endurance ou garantia de ausência global de erros.

## D. Bug reproduzido

O efeito `strength_bonus` já era aplicado corretamente pelo backend, mas o dicionário de rótulos do `CombatEffectsPanel` não incluía esse campo. A interface imprimia **`undefined +3`**. Reproduzido no jogador e novamente no Mestre após recarga/avanço de rodada. O segundo modificador permitido pelo backend, `movement_multiplier`, tinha a mesma lacuna, comprovada por regressão de renderização.

## E. Correção mínima

- `frontend/src/components/CombatEffectsPanel.tsx`: somente dois rótulos adicionados: **Força** e **Multiplicador de movimento**. Nenhuma fórmula, duração, autorização, controle de editor ou regra alterada.
- `frontend/tests/combat-effect-labels.test.cjs`: dois testes de renderização reais do componente transpilado, perspectivas GM/player. Antes: 0/2; depois: 2/2. Também verificam ocultação de zero e preservação dos cinco controles GM existentes.
- Repetição visual com build corrigido e fixture descansado: Força Arcana usada novamente; painel GM e player mostram **Força +3**, sem `undefined`. Screenshot do player expandido observado. Não promoveu build para produção.

## F. Checks realmente executados nesta etapa

| Comando | Resultado |
| --- | --- |
| `node --test tests/combat-effect-labels.test.cjs` antes do patch | 0/2, FAIL esperado reproduzindo rótulo |
| `node --test tests/*.test.cjs` em frontend após patch | 88/88 PASS; zero skips |
| `npx --no-install tsc --noEmit` em frontend, também executado separadamente | PASS, exit0 |
| `npm run build -- --outDir C:/Users/delib/AppData/Local/Temp/companion-s6-acceptance-final-build-20261005` | PASS; aviso existente de chunk grande |
| `.venv-observer/Scripts/python.exe -m unittest discover -s backend -p test_*.py` | 278/278 PASS, 64,234s; ResourceWarnings de SQLite existentes |
| `git diff --check -- .` | PASS |

Os números do checkpoint anterior não foram usados como substituto desta execução. Não houve nova alteração backend, visibilidade ou permissões; a suíte completa reteve essas regressões protegidas.

## G. Limitações e confirmação de loot

- `Confirmar distribuição` abriu o diálogo correto: “Distribuir integralmente o espólio de Lobo visual S6?”. A ação não foi reenviada cegamente.
- A recuperação do diálogo pelo controle de navegador falhou por timeout de foco/CDP. Limitação de automação, não falha comprovada do Companion.
- Leitura externa **somente** do backend fixture confirmou: `status=revealed`, `distributed_at=null`, `allocations=[]`, `distribution_ledger_id=null`. Logo, distribuição não concluída. Não foi concluída por API para fingir PASS da UI.
- Outras abas continuaram operacionais; novo tab GM serviu para terminar os demais ensaios. `confirm()` não foi substituído nem interceptado.
- Faltam prova visual da distribuição/destino/retry, invocação removida, progressão Dorn2→3 e XP em UI específica; não são classificados como bugs sem reprodução.
- Mesa mobile/multirrede e endurance: UNPROVEN. Três origins no mesmo Chrome não substituem jogadores em redes diferentes.

## H. Pendências reais / preservação

Uma falha visual comprovada foi corrigida. Não surgiu nova falha de autorização ou de resolução do combate. Distribuição visual e os cenários não exercitados acima continuam pendentes de aceitação, não de reconstrução.

Mapa tático, escala, distância, alcance novo, orçamento de movimento, morte/PV negativos e canon continuam fora do corte. Nenhum Vault, MCP, OpenCode, token real, banco operacional ou `.autonomy/` foi alterado. Servidor operacional8787/PID2516 e Tailscale/PID980 preservados. Servidor8872 reservado ao ensaio; não representa link de produção.

## I. Próximo corte mínimo recomendado — não executado

**Concluir manualmente o mesmo fluxo de distribuição do loot no ambiente descartável**, aceitando o diálogo nativo e conferindo destino, persistência e tentativa repetida; acompanhar com Mestre e dois jogadores reais em redes distintas. Não abrir mapa/morte ou reconstruir loot antes dessa evidência.

Sem push, merge, publicação, OpenCode ou implementação do próximo corte. Checkpoint isolado pronto; patch visual e este relatório ficam para revisão. Ao concluir, somente o processo descartável8872 foi encerrado; listener8787/PID2516 e Tailscale/PID980 continuaram ativos, e o índice Git permaneceu vazio.

## Retomada exclusiva do loot visual

- Estado inicial reconfirmado: HEAD `d8725db63f71d3f2bbf36604479ccc09a30fd506`, mesma branch. Diff de produto continua somente os dois rótulos em `CombatEffectsPanel.tsx`; teste e este relatório ainda untracked. `.autonomy/` e alterações externas intocadas; índice vazio.
- Retomado o mesmo banco descartável na porta8872, sem recriar/alterar campanha operacional. Mestre abriu o espólio pendente11PP e selecionou explicitamente Vezemir como destino pela UI.
- Clique em `Confirmar distribuição` pelo locator oficial encontrou timeout em `Input.dispatchMouseEvent`. Não foi repetido cegamente. `getJsDialog()` para aceitar a confirmação retornou timeout em `Emulation.setFocusEmulationEnabled.confirm`; tentativa de observar estado/screenshot também retornou timeout de foco. Não houve override de `confirm()`, teclado às cegas, distribuição por API nem mudança de produto para acomodar automação.
- Cliente separado de Vezemir continuou funcionando: identidade player, registro do loot revelado11PP, nenhum controle de distribuição.
- Leitura externa do servidor fixture: resolução `loot:e99a2b2fb26ea82461d6b7512e2a889d` permanece `revealed`, `distributed_at=null`, `allocations=[]`, `distribution_ledger_id=null`; Vezemir `silver_coins=0`. Sem distribuição parcial. Destino/refresh/retry da distribuição continuam UNPROVEN.
- **LOOT_VISUAL = UNPROVEN**. Bloqueio demonstrado no ambiente de automação; nenhum defeito independente do produto reproduzido. Geração/revelação pertencem ao ensaio visual anterior; não se afirma nova reprodução completa nesta retomada.
- Checks realmente reexecutados: backend `unittest discover -s backend -p test*loot*.py` **7/7 PASS**; frontend `node --test tests/*.test.cjs` **88/88 PASS**, sem skips; `npx --no-install tsc --noEmit` **PASS**; build em `%LOCALAPPDATA%/Temp/companion-s6-loot-final-build-20261005` **PASS** com aviso existente de chunk grande; `git diff --check -- .` **PASS**. Não se declara reexecução dos278 testes backend nesta retomada.
- Nenhuma nova correção de código. Checkpoint `fix: close S6 visual acceptance` **NÃO CRIADO**, pois sua condição de aceitação visual PASS não foi satisfeita. Patch de rótulos preservado para revisão, sem staging/push.
- Pendências: confirmação visual integral do loot e teste humano multicliente em redes diferentes. Não se declara que reste somente a mesa humana enquanto o loot continuar UNPROVEN.
