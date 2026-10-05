# Aceitação funcional S6 — 2026-10-05

**Resultado geral: PARTIAL.** Ensaio HTTP e regressões automatizadas aprovados após uma correção comprovada. Aceitação visual completa e mesa multirrede ainda não demonstradas. Não confundir esses níveis de evidência.

## A. Estado encontrado

- HEAD: `d3a701e246469744b9acda165387ce4ed5d3267c`.
- Branch: `devin/create-omnisvera-class-standard`.
- Início: Companion limpo, exceto `.autonomy/` untracked, não utilizada nem modificada.
- O repositório pai já tinha alterações legítimas de Vault, mídia e outros arquivos. Nenhuma foi descartada ou incluída nesta intervenção.
- Backend operacional: porta 8787, PID 2516; encaminhamento Tailscale PID 980. Não reiniciado. OpenCode também não utilizado.
- Python usado: `.venv-observer/Scripts/python.exe`; o Python global não representa o ambiente de dependências do Companion.
- Ao final: duas alterações rastreadas e três arquivos novos desta tarefa, listados em E. Sem commit, push, promoção ou alteração do frontend servido em produção.

## B. Baseline executado antes de editar

| Comando | Resultado real |
| --- | --- |
| `.venv-observer/Scripts/python.exe -m unittest discover -s backend` | 274/274 PASS, 79,338 s |
| `node --test tests/*.test.cjs` em `frontend` | 86/86 PASS, sem skips |
| `npx --no-install tsc --noEmit` em `frontend` | PASS |
| `npm run build -- --outDir C:/Users/delib/AppData/Local/Temp/companion-s6-acceptance-build-20261004` | PASS |

Build isolado; não substituiu `frontend/dist`. Avisos existentes de SQLite não fechado e chunks acima de 500 kB não foram convertidos em falhas nem silenciosamente eliminados.

## C. Matriz de aceitação

PASS abaixo se refere ao cenário e à modalidade indicados, não a uma sessão completa com jogadores reais. `PARTIAL` não significa automaticamente bug.

| Área / cenário | Antes | Resultado | Evidência | Alteração necessária |
| --- | --- | --- | --- | --- |
| Combate: iniciar, PCs/inimigos, iniciativa, turno, fora do turno, fim | Baseline verde; ensaio a executar | PASS | HTTP sintético + `test_battle_mode`, `test_session6_combat`; tentativa fora do turno retorna 400; repetição de passar turno não avança novamente | Nenhuma |
| Ataques: disponibilidade, escolha, alvo, orçamento, dano, PV e confirmação repetida | Baseline verde | PASS | `session6_rehearsal.py`: Adaga de Osso, dois alvos, terceiro ataque negado, confirmação exactly-once; UI GM: Morthak resolve e confirma ataque, alvo sinalizado, orçamento consumido | Nenhuma |
| Monstros: ataques próprios e painel do Mestre | Baseline verde | PASS API / PARTIAL visual | Testes de ataques de criatura e painel GM real com ataque, alvo, rolagem, dano e passar turno. Não concluída uma bateria visual de todas as criaturas com múltiplos ataques | Completar aceitação visual, não reconstruir resolver |
| 0 PV | Contrato atual de clamp a zero | PASS | HTTP: inimigo 1→0; confirmação repetida não duplica dano; alvo sem vida rejeitado; encerramento possível | Nenhuma regra nova de morte |
| Força Arcana: modificador, duração, decremento e expiração | Baseline verde | PASS API / PARTIAL visual | HTTP: Força aumenta, duração player/GM coincide, rodadas decrementam, expiração restaura atributo; `test_multiattack_effects` cobre derivados | Falta acompanhar a duração pela UI player durante todo o ciclo |
| Magias: consumo, limite, alvo, dano | Baseline verde | PASS | HTTP: Morthak e Dorn usam Mísseis Mágicos até zero; nova tentativa rejeitada; confirmação idempotente; regressões de magias e recursos | Nenhuma |
| Descanso existente | Baseline verde | PASS | HTTP: dois descansos não ultrapassam máximos; magias e PV restaurados conforme `rest_at_inn`; testes de recuperação | Não criar outro sistema |
| Invocações | Baseline verde | PASS API / PARTIAL visual | HTTP: invocação própria na iniciativa, ataque/alvo, orçamento, outro jogador negado, PV da criatura independentes, retorno à exploração. Duração em tempo de jogo não foi tratada como relógio de parede | Falta executar o fluxo inteiro pela perspectiva visual do proprietário |
| Dorn | Implementação existente | PASS API / PARTIAL visual | Ficha sintética baseada em SPEC: nível 2, PV 13, CA 11, atributos/recursos/magias; adição incremental preserva turno; testes Dorn e progressão 2→3 | Sem redesign; falta percorrer toda a ficha pela UI |
| Mordida: ataque confirmado, dano, cura 1d4, sem custo de sangue, persistência, repetição | FAIL entre combates sucessivos | PASS após correção | HTTP reproduziu `Mordida já usada neste turno` no novo combate; teste novo falhou antes e passou depois; ensaios repetidos após patch | Corrigida apenas a chave de turno |
| Loot: criatura derrotada → gerar → revelar → distribuir → histórico | Baseline verde | PASS API / PARTIAL UI | HTTP e `test_combat_loot_circuit`, `test_loot`: geração privada, revelação, distribuição integral e retry sem duplicação. UI gerou e revelou espólio; confirmação final não concluída | Retomar somente confirmação visual |
| Level-up: Vezemir, Raziel, Morthak e Dorn | Baseline verde | PASS API / PARTIAL visual | HTTP preview/confirm/retry ao nível 2; testes de XP, derivados, preservação de ferimentos/recursos, conflitos e rollback; frontend testa ocultação de mudanças nulas | Aceitação visual das fichas ainda incompleta |
| Varkh: progressão não conferida | Ausência deliberada de suporte | PASS do bloqueio / PARTIAL da capacidade | HTTP preview retorna 400; `level_advancement.py` possui tabelas para Vezemir, Raziel, Morthak e Dorn, não Varkh | Não habilitar sem regras aprovadas |
| Permissões / privacidade | Auditoria independente encerrada | PASS nas regressões reexecutadas | Suíte completa: token oculto, loot draft, ledger filtrado; teste explícito novo: cena draft invisível, private_notes/private_status removidos, HP/condição pública de outro PC preservados | Nenhuma mudança em owner/gm/public |

### Evidência visual e limitação do navegador

Usado navegador real contra a instância descartável, com token público de fixture. Foi observado: iniciar arena, iniciativa, selecionar Morthak/ataque/alvo, preview e confirmação, HP 90→86, orçamento encerrado, turno do monstro com resolução automática, HP de Morthak 9→8, passar turno e encerrar. A linha de alvo consta na árvore de acessibilidade; barras e números de PV estavam presentes.

No loot, foi criado apenas um inimigo sintético morto. A UI gerou 7 PP, revelou, selecionou destinatário e abriu o diálogo nativo de distribuição. O controle do navegador passou a falhar com timeout em `Emulation.setFocusEmulationEnabled`; tentativas de confirmar e fechar a aba também falharam. A API mostrou esse espólio ainda revelado e não distribuído. Portanto, **a distribuição final desse fluxo visual não foi comprovada**. A distribuição em outro cenário HTTP passou. Não atribuir o travamento da ferramenta ao produto sem reprodução independente.

Não há screenshots finais nem ensaio completo de perspectivas player/mobile nesta entrega. Os testes Node não substituem um navegador com jogadores reais.

## D. Bug realmente reproduzido

**Mordida bloqueada na primeira vez de um combate novo.** A chave persistida no ledger era `r1i0` para a primeira rodada/posição. Como uma nova luta reinicia rodada e posição, uma Mordida histórica era interpretada como já usada no turno atual. O defeito ocorreu em HTTP e foi isolado em `test_mordida_first_turn_of_new_encounter_does_not_reuse_previous_claim`.

Erros intermediários de fixture (sem mapa ativo, distribuição parcial incompatível com o contrato, alvo já morto, recurso Dorn não preparado e tipo de participante inválido no teste novo) foram corrigidos no ensaio, não no produto. Não são bugs comprovados do Companion.

## E. Correções e arquivos

- `backend/app/main.py`: `_technique_battle_turn` usa a sequência de turno já persistida pelo combate, que avança entre lutas e é preservada por edição de iniciativa. Mantém fallback para estados legados sem sequência. Não altera autorização, dano, cura, custo ou limites da Mordida.
- `backend/test_hemomante_techniques.py`: regressão com dois combates reais pela máquina de estado, ambos rodada 1/posição 0, permitindo uma Mordida em cada um. Regressões existentes continuam impedindo duplicação no mesmo turno/acerto.
- `backend/scripts/session6_acceptance.py` (novo): cria fixture totalmente sintética em diretório temporário; recusa overwrite; confirma IDs aleatórios dos mapas locais/remotos antes de writes; executa ensaio HTTP com tokens fixture. Não usa a operação de cópia do banco real.
- `backend/test_session6_acceptance.py` (novo): segurança/completude do seed, recusa de caminho não temporário, privacidade de cenas e preservação do estado público entre PCs. Coleta conexões cíclicas antes do cleanup no Windows.
- Este relatório (novo).

Não alterados: frontend de produto, permissões, loot, cena, Vault/CAMPANHA, `.autonomy`, MCP, regras de morte, mapa tático e configuração operacional.

**Ativação:** não realizada. Para adotar a nova chave, prefira encerrar qualquer combate antes de reiniciar o backend; um claim legado de uma batalha em andamento tem outro formato. Não foi feita migração de ledger nem reescrita de evidência histórica.

## F. Revalidação

- Técnicas Hemomante/Vezemir/invocações no arquivo de técnicas: 18/18 PASS após patch; regressão nova comprovadamente FAIL antes dele.
- Testes específicos do novo harness: 3/3 PASS.
- Backend completo final: **278/278 PASS**, 68,761 s (274 da baseline + quatro regressões novas).
- Frontend novamente: 86/86 PASS, zero skips.
- TypeScript novamente: PASS.
- Build novamente em `Temp/companion-s6-acceptance-final-build-20261005`: PASS; mesmo bundle JS `index-CH1dKITg.js` da baseline.
- `session6_acceptance.py probe`: PASS em repetições consecutivas após patch; inclui bloqueio legítimo de Varkh, quatro fluxos suportados, Dorn incremental, expiração, zero PV, loot, descanso e Mordida. Varkh não foi promovido.
- `session6_rehearsal.py`: PASS nos oito checks de ataques, alvos, orçamento, invocação, propriedade, PV, exactly-once e restauração.
- `git diff --check -- .`: PASS.

Ocorreram execuções intermediárias FAIL dos novos testes por cleanup SQLite no Windows e tipo de participante incorreto. Não foram ocultadas com skip/mocks/asserts enfraquecidos. Os avisos existentes de conexões SQLite e de bundle grande continuam visíveis.

Ensaio em `127.0.0.1:8872`, SQLite e Vault vazio temporários. Nenhuma requisição de mutação foi enviada ao backend operacional. O servidor de teste foi separado do PID operacional; nenhum restart de produção autorizado implicitamente por esta tarefa.

## G. Mapa tático — auditado, não implementado

| Item | Classificação | Evidência |
| --- | --- | --- |
| Escala formal persistida | AUSENTE | Registro do mapa não contém metros/célula, cols/rows ou escala física |
| Coordenadas de grid | PARCIAL | Pins persistem coordenadas normalizadas 0–100; fog tem células; grade visual CSS de 10%; não são células táticas com snap |
| Cálculo de distância | AUSENTE | Linha SVG de alvo usa posições normalizadas, sem cálculo métrico |
| Unidade de medida espacial do mapa | AUSENTE | Movimento e alcance mencionam metros nas fichas/textos; não existe conversão posição→metros |
| Alcance automático atacante/alvo | AUSENTE | Mísseis Mágicos apresenta conferência manual de alcance/linha de visão |
| Orçamento de movimento por turno | AUSENTE | Orçamento de ataques existe; movimento da ficha não é descontado por deslocamento no mapa |
| Validação automática de movimento tático | AUSENTE | Clamp de coordenadas e controle do proprietário existem, não custo de movimento/distância |

A linha tracejada de alvo **já existe** em `AttackTargetLine.tsx`; não representa medição de alcance. Nenhuma decisão de 1 quadrado = 1 metro foi tomada.

## H. Decisões de Sage

- Escala e regras de movimento/alcance para um corte tático futuro.
- Regras de morte/PV negativos se forem desejadas; o contrato atual fica em 0 PV.
- Progressões adaptadas ainda não conferidas (Varkh; escolhas de Raziel acima dos níveis aprovados) antes de liberar benefícios novos.
- Nenhuma dessas decisões foi necessária para corrigir a Mordida ou justificar reconstrução de permissões.

## I. Pendências reais

- Completar o diálogo de distribuição de loot pela UI e os fluxos player de efeitos/invocações/fichas; o blocker visual não prova um defeito funcional.
- Mestre + dois jogadores reais em redes diferentes: NOT TESTED. Loopback não prova estabilidade móvel/multirrede.
- Alcance, movimento e escala continuam ausentes por escopo deliberado.
- Efeitos com contrato de conferência manual/tempo de jogo não ganharam automação nova neste corte.
- Correção local ainda não ativada no processo operacional. Sem push/merge.

## J. Próximo corte mínimo recomendado

**Uma rodada de aceitação visual multicliente em ambiente descartável**, sem novas features: fechar loot, efeitos e invocação pela perspectiva dos jogadores e repetir com Mestre + dois clientes em redes diferentes. Corrigir somente se ela reproduzir um defeito. Não iniciar esse corte antes da revisão de Sage.
