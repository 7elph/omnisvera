# Quatro fichas — fechamento por evidência

Escopo: verificar a superfície atual e corrigir lacunas comprovadas de auditoria,
sem mudar regras, conceder componentes ou executar ações na campanha operacional.
Branch `devin/create-omnisvera-class-standard`, base `1a07a84`; alterações anteriores
preservadas. Este corte não certifica toda a ficha nem mesa física.

## Matriz inicial

| Ficha | Executado com sucesso no ensaio geral inicial | Limite / próximo fechamento |
|---|---|---|
| Vezemir | Grisalma/melee, Força Arcana, Velocidade, Frenesi manual/expiração, Provocação, Vinhas, poção + ataque | Ranged genérico sem arma é bloqueio correto. Provar separadamente maestria, gatilho automático/−10 e raciais; visão/portas dependem de sistemas e arbitragem, não de um botão de ataque. |
| Morthak | Melee, Adaga de Osso, Mísseis, duas modalidades de invocação e ataque do invocado, Toque, Aterrorizar, Magia da Morte | Clonagem bloqueada por falta de Fragmento de Cristal Arcano na cópia; ranged genérico sem arma não invalida Adaga. Traços raciais e Afastar Mortos-Vivos não ganham automação por estarem descritos no catálogo. |
| Raziel | Ataques de item, Mordida, Regeneração, Marca, três formas animais/retorno, Caixão condicionado ao descanso | O roteiro geral anterior só conhecia poderes antigos. Acrescentados nove comandos únicos das cinco armas; passivas têm regressões próprias, não ganham PASS por herdar o sucesso de uma ativa. Fotossensibilidade/cura invertida continuam exigindo tratamento explícito. |
| Dorn | Ataques, Reparo conforme estoque, pacote de magias, Guarda/Vanguarda, consumo/turno | Detalhar provas por traço de constructo, imunidade/JP e cada caminho de UI. Levitação, Escuridão e Diagnóstico removidos da ficha atual continuam apenas como legado auditável. |

“Executado” comprova os cenários citados, não cada combinação, custo, alcance,
duração ou percurso visual possível. Falta de teste não prova defeito mecânico.

## Correções deste corte

- `sheet_action_inventory.py`: projeção pura para auditoria a partir do DTO
  privado autorizado. Reconhece nove comandos únicos de Hemomancia (quatro
  armas com básico/especial + Escudo/Bastião compartilhado) e cinco passivas.
  Não duplica os dois cards do escudo como duas ações e não concede habilidades
  quando o pacote privado está ausente ou em revisão incompatível.
- Manifesto GM fornece rota nativa, revisão e estimativa de custo, incluindo
  arma ativa sem nova invocação. Handler nativo continua autoridade final.
- Relatório mantém os comandos legados e marca `visible_on_sheet=false`;
  eles não viram falsos gaps dos cards atuais. Não apaga falhas de cenário.
- Reserva, custos e expiração de Marca/Regeneração e armas entram nas obrigações
  corretas. Passivas sem prova deixam de ser rotuladas como arbitragem manual.
- Ensaio geral ganha nove cenários de Hemomancia com prévia/confirm, retry,
  custo, alcance e expiração. Nenhum executor de regras paralelo foi criado.
- Cópia de mídia inclui imagens do catálogo das quatro fichas presentes, dentro
  dos mesmos limites e validações de caminho; não lê texto de notas nem gera arte.
- Importação CLI do processo pai e child alinhada ao backend do checkout.
  Duas falhas de integração do teste ficaram registradas; não são falhas de magia.

## Validação

Inicial: 79 cenários API PASS, zero FAIL e três EXPECTED_BLOCK (dois ranged sem
arma, Clonagem sem cristal). UI dessa tentativa não executou por erro de importação;
não conta como aceitação visual. RED/GREEN específicos da auditoria, mídia e
importação reproduziram os problemas antes dos patches.

- Backend amplo: 1.084 testes OK, um skip de symlink sem privilégio no Windows
  (701,8 s). O ajuste final de visibilidade do Diagnóstico e o teste explícito
  do bootstrap pai/child são posteriores e foram repetidos em oito testes focados,
  todos PASS; a contagem ampla não é apresentada como nova execução pós-ajuste.
- Frontend: 336 PASS; typecheck e build PASS, warning pré-existente de chunks.
- Regressões focadas intermediárias: 95 PASS (conjuntos sobrepostos, não somar).
- Ensaio final `2_ini6cr`: 88 cenários API PASS, zero FAIL e três EXPECTED_BLOCK.
  Inclui os nove comandos novos, com custo, retry, alcance e expiração comprovados.
  Readiness: seis contextos Mestre/jogador, 360/390/1440 px, PASS em 120,946 s.
  Capturas das quatro fichas abertas/revisadas: estrutura e cards legíveis,
  mas alguns itens/ícone de dados faltam na fixture e texto alternativo aparece
  na CA. Aceitação visual parcial; não certifica mídia operacional completa.
- Roteiro de dez ações pela UI: INCONCLUSIVE por timeout do script em 306,067 s;
  somente sua árvore de processos foi parada. O lote geral terminou exit 2.
  Não se aumentou timeout, não se retiraram casos e o resultado não virou PASS.
  API verde e readiness verde não certificam essa navegação nem as quatro fichas.
- Mídia de teste: 94 referências copiadas, zero ausências nesse conjunto;
  dois caminhos `companion-assets/` ficam fora da cópia de Vault por desenho e
  são servidos pelo mount estático existente. Isso não prova todos os ícones
  derivados dinamicamente do inventário/catálogos.
- Backend de auditoria ativado com backup e combate inativo: servidor 218476,
  launcher 235796. As 27 tabelas protegidas mantiveram seus dados; somente
  `session_workspace_maps.updated_at` mudou no startup. Configurações e tokens
  iguais, quatro fichas e endereço público HTTP 200. Manifesto novo confirmou
  nove comandos, cinco passivas e legado preservado. Jogadores negados no
  endpoint GM (401); pacote privado de Raziel continua restrito ao proprietário.
  Nenhum cast, estoque, nível ou PV foi alterado para validação operacional.

## Pendências reais preservadas

- Componente de Clonagem: não reposto automaticamente na campanha.
- Provas individuais de todas as passivas, raciais, itens e combinações de turno.
- Decisões de regra ainda ausentes não são preenchidas por interpretação de texto.
- Mídia dinâmica completa, celular físico e Mestre/jogadores em redes distintas.
- Completar o roteiro UI inconclusivo em lotes fixos menores, mantendo os dez
  casos e limites, antes de chamar as quatro fichas de prontas.
- Importação do acervo, geração de Cenas por IA, modelos/imagens e walls fora deste corte.

## Arquivos

`backend/app/sheet_action_inventory.py`, `backend/app/native_action_manifest.py`,
`backend/scripts/sheet_rehearsal.py`, `backend/scripts/all_actions_simulation.py`,
`backend/scripts/fixture_media.py`, `backend/test_current_sheet_inventory.py`,
`backend/test_fixture_media.py`, `backend/test_sheet_runtime_imports.py`, este resumo,
`CURRENT_COMPANION_CODE.md` e `AI_TEST_TOOLS.md`.
Sem staging, commit ou push.
