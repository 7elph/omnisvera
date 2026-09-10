# Controles da mesa, combate e pins — 28/08/2026

## Uso

1. No resumo do mestre, escolha **Digital** ou **Física**. O backend exige esse modo nos ataques; o jogador não escolhe outro modo na ficha. Teste usa rolagem digital.
2. **Combate** abre preparação e acompanhamento, não uma ficha. Preencha a iniciativa dos participantes (vazio deixa fora), posicione criaturas em **Mapa e criaturas** e inicie o combate. A ordem fica persistida; empates seguem a ordem da lista.
3. Em **Efeitos e multiataque**, o mestre define a quantidade base autorizada de ataques e aplica/edita/remove efeitos. Modificadores suportados: ataque, dano, CA, ataques adicionais e PV por rodada. Durações: rodadas, próxima ação de ataque, cena, descanso ou remoção manual.
4. O jogador seleciona alvo e quantidade de golpes. Na mesa física informa um d20 bruto por golpe, por exemplo `15 1`. Na digital o backend rola. **Conferir ataque / Rolar e conferir ataque** calcula acerto e dano, mas não altera HP. **Confirmar e aplicar** altera HP e registra a ação uma única vez. O dano continua sendo rolado/calculado pelo backend, inclusive quando o d20 é físico.
5. O jogador pode abrir **Combate · iniciativa e efeitos** e usar **Ir ao mapa do combate**, sem perder a possibilidade de explorar outros mapas.
6. Monstro a zero: use o fluxo existente de **Gerar espólio**. **Itens e loot** reúne revisão, revelação, distribuição e criação/edição de itens. Nada é distribuído automaticamente ao morrer: o mestre mantém a decisão. O fluxo existente de d100 não foi substituído.
7. A criação de item tem etapas: identificação, imagem opcional, regras opcionais e conferência. É possível criar só com nome; dar/retirar/destruir continuam ações distintas.
8. **Mapas → Controle de ícones e pins → Locais** reutiliza os ícones prontos e os locais cadastrados quando disponíveis. Nome, imagem, descrição, posição e visibilidade são editáveis. O catálogo também tem uma ação que realmente cria um pin oculto, em vez de apenas copiar a imagem para outro formulário.

## Correções e fronteiras

- Novos pins procuram uma posição central livre em vez de todos nascerem sobrepostos. Pins antigos não foram movidos automaticamente.
- Local é um tipo de pin, sem HP/CA e fora dos alvos de combate. A migração SQLite preserva os pins existentes.
- Criar um pin oculto não publica seu nome no chat. Jogadores não podem atacar um token oculto pelo novo fluxo.
- Ataques confirmados aparecem no registro com golpes, bônus, CA, dano e HP antes/depois. O registro existente de uso de magia/habilidade foi reutilizado e observado no navegador do mestre.
- A ficha dentro de **Edição do Mestre** começa recolhida. Nenhum CSS foi alterado neste corte.
- Multiataque usa uma arma/ataque e um alvo por resolução. O mestre autoriza de 1 a 10 golpes; o jogador não pode aumentar o limite pelo request.
- Efeitos são adjudicados explicitamente pelo mestre, não inferidos de texto de magia. Condições sem modificador são narrativas. Não há automação universal de resistências, imunidades, todas as magias, invocações ou bloqueio de turno.
- **Encerrar rodada** aplica PV periódico e reduz durações atomicamente. Encerrar efeitos de cena é explícito. Descanso existente encerra efeitos com duração de descanso. Efeito de próxima ação é consumido somente na confirmação, uma vez por ação completa.
- Alteração de efeitos/iniciativa invalida uma resolução pendente para impedir aplicação com bônus antigos. Confirmação já aplicada permanece idempotente.

## Evidência

Testes de navegador usaram uma cópia SQLite isolada na porta 8873, com sessões separadas de mestre e Varkh. Nenhum ataque, item, efeito ou pin de teste foi criado na campanha operacional.

| Cenário | Resultado |
|---|---|
| Botão Combate abre controles, não ficha | PASS no navegador |
| Iniciativa Varkh 15 / goblin 8, combate persistido | PASS no navegador |
| Dois d20 físicos 15 e 1, bônus +5, CA 10 | Um acerto e um erro |
| Antes de confirmar | Goblin manteve 10 PV |
| Confirmar | Dano 4; HP 10 → 6 |
| Reenviar confirmação | HP continuou 6, um único evento |
| Mestre sem recarregar | Viu HP e resolução no registro |
| Magia Manipulação de Elementos | Uso novo registrado em 28/08, distinto do registro antigo de 21/08 |
| Item simples pelo checklist | Criado com nome e descrição, sem regras/imagem |
| Edição da ficha recolhida | PASS no navegador |
| Local do catálogo, oculto → revelar | Pin persistiu e apareceu ao jogador |
| Jogador em outro mapa → seguir combate | PASS no navegador |
| Tela estreita | Inspeção visual em Chrome, largura efetiva 488px; sem overflow horizontal. Não equivale a teste em celular físico |
| Ataque → morte → loot → distribuição/replay | PASS no teste backend existente |

## Validação

- Backend: `.venv/Scripts/python.exe -m unittest discover -s . -p 'test_*.py' -q` — **100 testes aprovados**, incluindo 12 novos de multiataque/efeitos/pins/controle de combate.
- Frontend: `node --test tests/*.test.cjs` — **26 testes aprovados**, incluindo 4 de controles/pins/mapa.
- TypeScript: `npx --no-install tsc --noEmit` — aprovado.
- Build: `npm run build` — aprovado; versão final `index-B6ULTCP7.js`, CSS preservado `index-DxxyMSU4.css`.
- Warnings conhecidos: Starlette depreca o uso de httpx no TestClient; bundle Three.js excede 500 kB. Git avisa sobre conversão LF/CRLF. Não houve erro de whitespace no diff.
- Durante a implementação, TypeScript detectou dois campos opcionais não tipados corretamente; corrigidos antes da entrega. O teste de navegador encontrou e corrigiu o fechamento prematuro da primeira etapa do checklist. Algumas operações do controle do navegador tiveram timeout; o estado foi conferido antes de repetir.

## Arquivos deste corte

Backend: `app/combat.py`, `app/combat_effects.py` (novo), `app/character_play.py`, `app/main.py`, `app/schemas.py`, `app/session_workspace.py`, `test_multiattack_effects.py` (novo).

Frontend: `src/api.ts`, `src/pages/SessionWorkspace.tsx`, `src/components/CombatEncounterPanel.tsx`, `CombatEffectsPanel.tsx`, `LocationQuickPin.tsx`, `pinPlacement.ts` (novos), `tests/table-controls.test.cjs` (novo).

Endpoints novos: `GET /combat/effects`, `POST /gm/combat/effects`. Endpoints existentes de ataque, confirmação, edição de ficha e pins foram estendidos; loot e uso de magia reutilizados.

## Operação e recuperação

- Base Git: `devin/create-omnisvera-class-standard`, `0f75a3aafc28bd1b16e8ceddcb36f6aae975c69e`.
- Worktree já misturado antes do trabalho. Não houve reset, checkout, push nem commit que incorporasse alterações anteriores.
- Checkpoint limitado aos arquivos deste corte: `.assistant-runtime/checkpoints/multiattack-effects-locations-2026-08-28/{before,after}`. Não usar esses arquivos para sobrescrever trabalho posterior sem comparar.
- Backup operacional antes da migração/reinício: `.assistant-runtime/backups/companion-before-table-controls-20260828T192850.sqlite3`; `PRAGMA integrity_check` retornou `ok`.
- Somente o Companion foi reiniciado pelo iniciador existente, preservando credenciais. MCP/túnel/PC não reiniciados.
- Saúde, workspace e endpoint de efeitos responderam HTTP 200 após reinício. Link público e localhost serviram o frontend atualizado.
- Comparação do banco operacional com o backup: pins e estados de personagens preservados integralmente; integridade `ok` após a migração.
- Banco de teste e backup não entram no Git. O checkpoint não equivale a um commit isolado: os arquivos modificados também continham trabalho preexistente, preservado.
