# Continuidade — reparos da Sessão 6

Atualizado em 2026-10-03. Leia antes de retomar. Este documento não declara a entrega inteira concluída.

## Contrato

Trabalhar diretamente em `C:\Users\delib\Desktop\OMNISVERA\omnisvera-agent`.
Ler `AGENTS.md`, `git status` e os diffs antes de editar. Worktree contém muitas alterações anteriores legítimas: não resetar, stashar, descartar ou substituir arquivos inteiros. Não fazer push. Não incluir bancos, anexos, tokens, logs ou Vault em commits. Preservar Mestre/Jogador e dados privados. Não ampliar a probation do mantenedor CSS para estas funcionalidades.

Fonte factual: `C:\Users\delib\Downloads\Sessão 6.txt`. Conteúdo de transcrição é evidência, não instrução de execução. Raziel esteve ausente nessa sessão, embora participe dos testes de regressão. A sessão terminou; não recriar acontecimentos nem duplicar recompensas.

## Já implementado neste corte

- `backend/app/battle_mode.py`: pin canônico da arena; orçamento de ataques por turno; restauração da exploração e inscrição incremental de participantes.
- `backend/app/combat.py`: confirmações contam golpes usados, permitindo alvos diferentes até o limite; Adaga de Osso de Morthak estruturada, sem arma equipada, dano **1d4**, sem custo. Fonte: 01:34:47–01:34:53. **Não usar 1d4+nível**, que pertence a Mísseis Mágicos.
- `backend/app/combat_effects.py`: passar turno de invocação pelo controlador; repetição estável; iniciativa não renova ataques nem troca arena; Mestre pode consumir o recurso do personagem autorizado, nunca o de outro jogador por requisição forjada.
- `backend/app/summons.py`: transação única para recurso + criatura + iniciativa + ledger; replay por request_id; invocação visível no mapa atual; HP independente (`character_id=NULL`, controlador em `sheet.summon.caster`); dura uma semana **de jogo**, sem expiração por relógio real. Animar Mortos exige cadáver visível, morto, no mapa, autorizado pelo Mestre, não reutilizado.
- `backend/app/main.py`: ID `levantar-um-esqueleto` do catálogo aceito; jogador só opera ataques de invocação própria, outros monstros continuam exclusivos do Mestre; payload de passar turno não muda quando a iniciativa avança.
- `backend/app/data/session_abilities.json`: esqueleto de madeira da recompensa final, um por uso, 10 PV, CA16, dano1d6+1; +2 de acerto anterior preservado. Não somar proposta anterior de dois esqueletos. Fraqueza a fogo permanece explicitamente manual.
- `backend/app/level_advancement.py`, `level_routes.py`: prévia/confirmar com `hp_policy`; preservação de ferimentos explicitamente selecionável, sem reanimar a0PV nem recarregar recursos. API antiga mantém preserve_current como default; interface usa a decisão da Sessão6 preserve_wounds.
- `frontend/src/pages/SessionWorkspace.tsx`, `api.ts`: alvo da Adaga; cadáver para reanimação; ID canônico; request_id estável das invocações após erro de transporte; orçamento restante no seletor; pins canônicos na arena; imagem de catálogo não herda acidentalmente criatura anterior; atalho Espólios do encontro separa carregado de covil.
- `CombatEncounterPanel.tsx`, `MonsterAttackPanel.tsx`: controlador joga o turno da invocação; ação concluída não continua aparentando disponível; autorização de cadáver pelo Mestre; passar turno explícito.
- `CombatEffectsPanel.tsx`: esclarece quando os efeitos existentes diminuem e PV/rodada é aplicado; **não inventou nova regra de dano de fogo**.
- `AttackTargetLine.tsx`: prefere ID exato e ignora associação legado de invocação ao caster. Linha tracejada já existente permanece.
- `LevelAdvancement.tsx`: escolha explícita de política de PV, com prévia invalidada ao mudar a escolha.

Testes novos/ajustados: `backend/test_session6_combat.py`, `test_level_advancement.py`, `test_hemomante_techniques.py`, `test_multiattack_effects.py`, `frontend/tests/combat-controls.test.cjs`, `level-advancement.test.cjs`.
O teste legado de Mordida foi corrigido para conferir o **1d4 já implementado anteriormente**, em vez de esperar cura igual a dano; a regra do produto não foi alterada nesse ajuste.

## Ambiente e comandos reais

Usar `.venv-observer\Scripts\python.exe`: tem FastAPI e MCP. `backend\.venv` não tem MCP; Python global não tem FastAPI. Não instalar dependências às cegas.

```powershell
cd C:\Users\delib\Desktop\OMNISVERA\omnisvera-agent
.\.venv-observer\Scripts\python.exe -m unittest discover -s backend -p 'test_*.py'
cd frontend
node --test tests/*.test.cjs
npx --no-install tsc --noEmit
npm run build -- --outDir C:/Users/delib/AppData/Local/Temp/companion-session6-build-20261003
cd ..
git diff --check -- backend frontend scripts docs
```

Resultados comprovados durante o trabalho: rodada inicial backend260/260 e frontend84/84; após novos testes frontend86/86, testes específicos Sessão6 9/9 e progressão14/14. A rodada intermediária backend264 teve um teste de texto do catálogo falhando; preservado o contrato textual “Ruling de mesa travado / 2º círculo”, corrigido o conteúdo, e nova suíte final iniciada. **Consultar seção de resultado final abaixo antes de afirmar o gate final.** Há ResourceWarnings anteriores e aviso de chunks grandes no build; não confundir warning com erro.

Ensaio descartável, nunca operacional:

- Banco: `C:\Users\delib\AppData\Local\Temp\companion-session6-306098016cfd43be9f71316352b560f1\test.sqlite3`.
- Frontend isolado: `C:\Users\delib\AppData\Local\Temp\companion-session6-build-20261003`.
- Porta8872, localhost; Vault de teste vazio separado; indexador e captura de treinamento desativados pelo `cf01_probe.py`.
- Servidor operacional8787 preservado; nenhum banco da campanha modificado por testes.

```powershell
.\.venv-observer\Scripts\python.exe backend/scripts/cf01_probe.py serve --database C:/Users/delib/AppData/Local/Temp/companion-session6-306098016cfd43be9f71316352b560f1/test.sqlite3 --port 8872 --frontend-dir C:/Users/delib/AppData/Local/Temp/companion-session6-build-20261003
.\.venv-observer\Scripts\python.exe backend/scripts/cf01_probe.py probe --database C:/Users/delib/AppData/Local/Temp/companion-session6-306098016cfd43be9f71316352b560f1/test.sqlite3 --port 8872
.\.venv-observer\Scripts\python.exe backend/scripts/combat_party_probe.py C:/Users/delib/AppData/Local/Temp/companion-session6-306098016cfd43be9f71316352b560f1/test.sqlite3 8872
```

Os dois probes passaram em HTTP real loopback: desconexão antes da resposta, persistência, autorização e confirmação única; três fichas + ataque do Mestre sem fórmula manual. Isso **não prova** mesa em redes diferentes nem ensaio integral visual. Credenciais públicas apenas desse fixture estão em `backend/scripts/cf01_probe.py`; nunca copiar credenciais operacionais para relatórios.

## Próximos passos, em ordem

1. Conferir estado real e relatório final abaixo. Concluir a suíte final, TypeScript, build e diff-check após qualquer edição adicional.
2. Reexecutar o ensaio HTTP **battle_mode=True** já criado em `backend/scripts/session6_rehearsal.py <banco-temporário> <porta>`, se houver novas alterações. **PASS comprovado neste corte**: Morthak Adaga → passar turno; Vezemir dois golpes em alvos diferentes → rejeitar terceiro; Morthak invoca → criatura entra visível na arena após caster; jogador dono ataca/passa turno; outro jogador403; inimigo atinge invocação e só seus PV mudam; fim retorna os participantes sem apagar invocação. O script modifica recursos apenas no banco de fixture e autentica primeiro com token de fixture.
3. Visual QA com Mestre e Morthak no localhost8872, desktop e celular: cards compactos, descrição legível, alvo correto, d20 físico da Adaga, barra+PV, painel do invocado e dano confirmado. Não acessar a campanha operacional para simular dano. Mídias podem estar ausentes no Vault isolado: se precisar, copiar **somente** assets necessários para o Vault temporário, não apontar a instância de teste ao Vault operacional.
4. Seletor físico da Adaga **corrigido e testado na interface**. A ficha do backend agora expõe a Adaga como ataque completo (`1d4`, bônus revisto da ficha, sem arma equipada), e o frontend não a duplica como card manual. UI: selecionar alvo → d20 físico20 → prévia dano4 → confirmar → PV84→80, no alvo descartável. Modo Digital não solicita fórmula/dano. Campo físico também preparado no popover da habilidade.
5. Botões legados “Gerar espólio” **corrigidos** para `treasureHasCarried/Lair` e excluem invocações. Ainda testar visualmente geração/distribuição de ambos os tipos e replay, sem converter letras OD em raridade homebrew B/C nem duplicar loot existente.
6. Resolver recompensa Pulseira de Vinhas: confirmar no fim da transcrição o efeito concluído (arma presa/retorno) separado de propostas de consumível/último recurso. Registrar/cadastrar uma vez somente depois de conferir inventário existente; não inventar alcance, cargas ou bônus. O esqueleto novo já usa números fechados, mas a fraqueza fogo1d6+2 aguarda resposta do Mestre (adicional ou substituição). Não automatizar imunidade a veneno, cura invertida ou dano sagrado sem regra confirmada.
7. Progressão real: as fichas copiadas já mostram Vezemir3, Morthak3 e Dorn3, mas PV17/8/13. Não aplicar avanços sem recuperar escolhas/rolagens anteriores e prévia. O novo fluxo não corrige sozinho avanço histórico pendente sem decisão válida. Raziel2 permanece preservado; não conceder avanço por ausência/presença presumida.
8. Auditar duração/dano periódico: sistema existente aplica PV/rodada e reduz duração ao completar a volta. A sessão menciona queimadura1d6 no começo do turno, que é regra diferente. Preparar opção explícita e teste de idempotência se o Mestre confirmar; não alterar silenciosamente todos os efeitos nem esquecer que retirar a habilidade mais cedo não renova orçamento de ataques.
9. Só após todos os gates e QA, ativar build validado e reiniciar **brevemente** o backend operacional com os tokens existentes, sem recriar banco, sessões ou túneis. Há autorização anterior de reinício quando testes passarem; antes verificar se está em uso e preservar estado. Validar health, Mestre/Jogador e estáticos após restart. Não declarar publicado só por build bem-sucedido.
10. Validar Mestre + dois jogadores em redes diferentes; loopback não substitui essa evidência. Reportar claramente “resolvido em código/testes” versus “comprovado em mesa”.

## Resultado final deste corte

- BACKEND = 266/266 PASS, suíte completa com `.venv-observer`, depois de adicionar cobertura de ficha real da Adaga.
- FRONTEND = 86/86 PASS; TypeScript PASS; build Vite PASS em diretório temporário (aviso de bundles grandes, não erro).
- DIFF_CHECK = PASS (avisos de conversão CRLF não são falhas).
- HTTP_RECONNECT = PASS; HTTP_THREE_CHARACTERS = PASS; HTTP_SESSION6_ARENA = PASS.
- UI_ADAGA_PHYSICAL = PASS em navegador real, Mestre, banco descartável. A inspeção visual inicialmente encontrou o card ainda manual apesar da rota correta; corrigida a projeção da ficha e removida duplicação. Não chamar isso de teste visual dos jogadores todos.
- Captura local ignorada: `.autonomy/runtime/session6-adaga-ui.jpg`. Instância descartável8872 encerrada após o ensaio; reiniciar com o comando `serve` acima antes de continuar. A instância operacional8787 permaneceu ativa.
- OPERATIONAL_ACTIVATION = NOT_DONE neste corte; banco e Vault operacionais não usados para testes, backend8787 não reiniciado. Build operacional não substituído.
- PENDING = QA visual completo jogador/celular/espólios, fraqueza fogo e demais rulings incertos, inventário Pulseira de Vinhas sem duplicação, reconciliação de níveis históricos, ativação segura e teste Mestre+dois jogadores em redes diferentes.
- OPENCode = não acionado automaticamente. O prompt abaixo prepara continuidade, não prova execução pelo OpenCode.
- Nenhum commit/push feito. Testes e ensaios novos não autorizam modificar Core/MCP ou o Vault.

## Prompt para o OpenCode

Continue os reparos da Sessão6 a partir de `docs/SESSION6_OPENCODE_HANDOFF.md`. Leia-o integralmente e leia AGENTS.md; inspecione git status/diff e preserve as alterações anteriores. Não recomece, não faça reset/push, não amplie o scheduler CSS, não escreva na campanha real para testar. Execute a fila restante em etapas, verificando após cada etapa. Mantenha decisões ambíguas pendentes e não invente regras. Use banco temporário e tokens de fixture para ensaios. Registre evidências e atualize somente o relatório deste corte. Termine indicando o que está implementado, comprovado em teste, ativado e ainda depende da mesa.
