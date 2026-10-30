# Anel Rúnico e fechamento da Sessão 7 — 12/10/2026

## Corrigido e ativado

O item existente `session-item:7` declarava cura de 4 PV, uma carga e recarga
`inn_rest`, mas usava `consume_mode=none`: curava sem gastar a carga.
O cadastro foi corrigido pelo editor/API nativo, preservando nome, imagem,
efeito e identidade. Nenhum anel foi usado, concedido ou recarregado na mesa
como teste. Inventário, fichas, sessão e combate foram preservados.

- Usar cura 4 PV, limitado ao máximo, e gasta uma carga; o anel não desaparece.
- Clique repetido/retry do mesmo comando não duplica cura nem consumo.
- Segunda utilização com carga zero é rejeitada.
- Inventários antigos sem metadados herdam também o ciclo de recarga no uso.
- O descanso concedido pelo Mestre recupera a carga. Caixão, reload e
  equipar/desequipar não recuperam a carga diária.
- Jogador não pode aumentar/reconfigurar cargas pela ação de ajuste manual.
  O Mestre mantém o ajuste administrativo; o jogador pode reduzir cargas já
  inicializadas. Isso não implementa calendário: a recarga segue `inn_rest`.

Backend reiniciado com backup SQLite consistente e cópia privada das
credenciais/configuração. A última inicialização atende em 8787, PID 15712.
Comparação confirmou preservação dos estados e dos valores de todos os tokens.
O inicializador reserializa o arquivo de credenciais e atualiza timestamps de
dois mapas oficiais; esses detalhes não são rotação de tokens ou mudança de mapa.
Tailscale não foi encerrado. Leituras autenticadas das fichas de Vezemir,
Morthak e Raziel retornaram 200 tanto localmente quanto pelo endereço público.
Essas leituras não certificam estabilidade de uma mesa em redes distintas.

## Evidências deste corte

- Backend: 648/648 testes, incluindo oito regressões do anel.
- Frontend: 245/245 testes; TypeScript e build passaram.
- Ensaio nativo dos quatro personagens: 65 cenários, 64 PASS e um
  EXPECTED_BLOCK (ataque ranged genérico de Morthak sem dano; Adaga de Osso
  tem cenário separado funcional). Não equivale a todas as passivas automáticas.
- Smokes seletivo e completo MCP stdio/API também passaram após a proteção
  de ajuste manual, verificando recibo idempotente e reconexão de outro
  servidor/cliente stdio. Evidência final privada em
  `%TEMP%/omnisvera-mcp-test-smoke-leegftq8/mcp-evidence.json`.
- Testes usaram banco descartável; produção recebeu somente a correção
  autorizada do cadastro e a ativação do código.
- Persistem warnings antigos de SQLite/lifespan nos testes e de chunk grande
  no build. Não foram ocultados nem justificaram refatoração ampla.

Os resultados antigos de FAIL do anel permanecem nos relatórios históricos.
Artefatos completos ficam privados em TEMP; não publicar banco, tokens ou logs.

## O que ainda impede afirmar “tudo automático e estável”

| Prioridade | Pendência | Natureza |
|---|---|---|
| 1 | Ensaio prolongado com Mestre e pelo menos dois jogadores em redes distintas, celular em segundo plano/retorno, combate e registro | Aceitação real ainda não comprovada; GET 200 e suíte verde não substituem isso |
| 2 | Forma da Noite: ficha de animal, restrições de ação e retorno a 0 PV com dano excedente | Troca visual existe, mas ciclo mecânico completo não está automatizado |
| 2 | Sentido do Sangue; fotossensibilidade, cura invertida e outras passivas | Há entradas PENDING/ASSISTED; faltam handlers/cobertura para automação integral |
| 2 | Fraqueza a fogo do esqueleto e categorias uniformes de dano/efeito | Ainda anotação/assistido; imunidades de Dorn dependem da classificação enviada |
| 3 | Matriz equipar/desequipar Essência, Página e outros itens, em todos os caminhos visuais e de combate | Cobertura parcial existe; não é ausência total de implementação |
| 3 | Limites dos ajustes manuais de PV/quantidade | Definir o que permanece manual antes de restringir; o bloqueio de recarga indevida já foi feito |
| 3 | Aceitação visual de todos os botões, mídia e grid no celular físico | Ensaios HTTP não provam UX ou alinhamento de toda imagem |

Progressão: Vezemir, Morthak, Raziel e Dorn estão no nível 5 no banco consultado.
Há nove rolagens de PV pendentes: Vezemir 4/5, Morthak 4/5, Dorn 4/5 e
Raziel 3/4/5. Vezemir ainda não escolheu especialização. São decisões/rolagens,
não autorização para escolher ou rolar por ele.

As rotinas principais de ataque, consumível, orçamento de turno, invocação
única, poderes de sangue aprovados e protocolos/reparo de Dorn têm cenários
nativos passando. Isso não cobre todas as combinações de itens/passivas.
A restauração de FOR do Toque e o avanço de turnos de exploração de Aterrorizar
continuam assistidos conforme seus contratos, sem converter duração por conta
própria. Novos poderes bloqueados por regra de campanha não devem ser ativados
silenciosamente.

## Melhorias futuras, não bugs da Sessão 7

Importação completa dos PDFs, sandbox de propostas em Cenas, fichas universais
de NPCs com ações, novas variantes espada/lança/escudo de sangue e Walls/LOS
são próximos produtos/cortes. Pulseira retornar Grisalma também é proposta;
não foi canonizada nesta correção. O MCP de ensaios por IA já existe, mas não
executa código arbitrário gerado pelo modelo nem aprova regras.

## Arquivos deste corte

- `backend/app/combat_consumables.py`: consumo persiste ciclo de recarga.
- `backend/app/character_play.py`: separa Caixão de recarga de itens e protege ajustes.
- `backend/test_runic_ring.py`: regressões determinísticas.
- `backend/scripts/runic_ring_contract.py`: reparação estritamente reconhecida.
- `backend/scripts/apply_runic_ring_fix.py`: manutenção autorizada via API, backup e preservação.
- `backend/scripts/all_actions_simulation.py`: ciclo completo do anel no ensaio existente.
- `backend/scripts/agent_test_mcp_smoke.py`: aceitação MCP seletiva/completa.
- `docs/RUNIC_RING_AND_SESSION7_CLOSURE_2026-10-12.md`: evidências e fila restante.
- `docs/CURRENT_COMPANION_CODE.md`, `docs/SHEET_TEST_VALIDATION_2026-10-12.md`,
  `docs/AI_TEST_TOOLS.md`: referências para o resultado corrigido.

O worktree misto preexistente foi preservado. Sem staging, commit ou push.
