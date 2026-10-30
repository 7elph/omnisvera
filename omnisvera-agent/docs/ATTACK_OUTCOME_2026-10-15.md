# Resultado sem janela pós-ataque

Pedido: eliminar o fechamento obrigatório da resolução após o ataque aplicado.

- Recibo confirmado mostra resumo inline, não abre diálogo nem pede “Concluído”.
- “Ver resultado” é leitura opcional, tanto no resumo como no registro da sessão.
- Registro mantém dados/cálculo, consumo e drenagem; detalhamento fica recolhido.
- Resumo distingue dano calculado de PV efetivamente removidos, usando os valores
  recebidos do backend. Não inventa uma rolagem de acerto para acerto automático.
- Confirmação automática não exibe prévia transitória. Falha preserva o recibo
  pendente para recuperação: não rerrola nem perde a confirmação idempotente.
- Não remove a confirmação prévia do alvo, nem o resgate de ações físicas/legadas
  ainda pendentes. Não altera regras, permissões ou endpoints.

## Verificação deste corte

- Backend completo: 799 testes, OK; frontend completo: 282 testes, OK.
- Typecheck e build padrão: OK; warnings de chunks grandes e conexões SQLite
  preexistentes continuam presentes.
- Ensaio MCP isolado `test-b2ee02c49c094735bafb32aa1e0d4c0b`, quatro atores,
  `ui:true`, cenários de API selecionados: quatro ataques melee, todos PASS.
  Resultado final: COMPLETED/PASS, oito de oito scripts visuais PASS.
- `grid-action-flow`: PASS nos quatro atores, clique no card → alvo → Sim →
  aplicação sem diálogo final, detalhes opcionais, custo e persistência/reload.
  Capturas desktop 1440 e mobile 390 inspecionadas. Mídias faltantes da fixture
  não certificam o catálogo de imagens operacional.
- Frontend novo servido localmente e pelo endereço público (HTTP 200, asset
  `index-DtgHSWwV.js`). Sem reinício: nenhuma regra/rota backend foi editada.
- Não foi feita mesa física em redes diferentes nem certificação integral das
  fichas. Não foram alterados recursos, itens ou dados operacionais para o ensaio.

## Arquivos deste corte

- `frontend/src/attackOutcome.ts`
- `frontend/src/components/AttackOutcome.tsx`
- `frontend/src/components/SpellResolution.tsx`
- `frontend/src/pages/SessionWorkspace.tsx`
- `frontend/src/companionTheme.css`
- `frontend/tests/attack-outcome.test.cjs`
- `frontend/tests/grid-action-flow-smoke.cjs`
- `docs/RAZIEL_HEMOMANCY_PIPELINE_PROPOSAL.md`
- `docs/RAZIEL_BLOOD_WEAPONS_PROPOSAL.md`
- `docs/CURRENT_COMPANION_CODE.md`
- este documento.

Worktree misto preservado. Sem staging, commit ou push. A proposta de Raziel
contém alternativas para aprovação, não implementação mecânica.
