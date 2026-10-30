# Descanso completo e controles do mapa

- Descanso geral continua usando as ações nativas das fichas ativas. Cada pedido
  possui chave idempotente; o descanso completo encerra todos os efeitos ativos
  do personagem, não somente os de duração `rest`.
- Condições, PV temporários, recursos, recarga diária e retorno da Forma da Noite
  seguem o fluxo existente. Efeitos encerrados permanecem na auditoria técnica.
- Clonagem encerrada pelo descanso remove seus clones pelo cleanup nativo.
  Não remove NPCs, invocações permanentes, itens equipados ou passivas de classe/raça.
- O Caixão pessoal mantém suas restrições existentes; não ganha a capacidade
  de conceder descanso geral. Jogador não pode conceder `rest_at_inn`.
- Zoom fica horizontal, inclusive no celular. Seletor, setas e a seção
  **Mover no grid** foram retirados a pedido do Mestre. Movimento é direto pelo
  pin, com mouse/toque; retry só aparece quando há comando de resultado incerto.
- O painel de mapa usa faixas de ferramentas de altura própria, sem atribuir
  a altura do canvas ao seletor. Grid, fog, escala e posições não foram alterados.

Arquivos deste corte:
`backend/app/{character_play,combat_effects}.py`,
`backend/test_complete_rest_effects.py`, `backend/scripts/run_sheet_test.py`,
`frontend/src/{companionTheme.css,pages/SessionWorkspace.tsx}`,
`frontend/tests/{map-toolbar-rest.test.cjs,map-toolbar-rest-smoke.cjs}`,
`docs/AI_TEST_TOOLS.md` e este documento.

Validação: regressões inicialmente RED; correção GREEN. Backend completo:
783 testes PASS. Frontend: 277 testes PASS. Typecheck e build PASS; build mantém
o aviso existente de chunks maiores que 500 kB.

O primeiro pedido MCP usou filtros incorretos e terminou INCONCLUSIVE
(`test-ee6eb7863741414eae0848757841ab41`); não certificou nenhuma interface.
O ensaio seguinte usa todos os cenários e todos os atores em fixture isolada.
Resultado visual e ativação são registrados abaixo após conclusão.

MCP `test-a692f9145070492ab305e123a296cb38`: 70 cenários API PASS, dois
EXPECTED_BLOCK, sete scripts visuais PASS. O novo smoke encontrou overflow ao
expandir movimento: FAIL real preservado. Correção localizada: seletor em linha
própria, quatro setas em grid, texto com quebra e largura mínima zero.

Após mudança das permissões do ambiente, a repetição frontend teve 271 PASS e
seis testes bloqueados pelo esbuild (`Acesso negado` ao consultar diretório ancestral).
Não é PASS da suíte final inteira. Typecheck PASS. Build final PASS usando o
carregador nativo já disponível: `npm run build -- --configLoader native`.

Nenhum descanso executado na mesa real para teste; nenhuma credencial exposta,
nenhum commit ou push. Viewport móvel local não prova celulares em redes externas.

## Resultado final

MCP `test-5989e375bec04a7ea7d7a565333d267b`: quatro cenários API e os oito
scripts visuais PASS no relatório privado. O controlador final classificou
INCONCLUSIVE por timeout no encerramento da fixture; não apresentar como MCP PASS.
Repetição independente do smoke específico em fixture TEMP/porta 8872:
PASS e exit 0, com encerramento concluído. Capturas de mapa fechado/expandido
em 390 px foram inspecionadas: zoom horizontal, quatro setas alinhadas,
sem overflow. Não houve alteração da geometria dos tokens.

Backup final no diretório ignorado `backend/data/backups/pre-rest-toolbar-20261014-223423`.
O ambiente passou a negar encerramento do PID operacional 78724 (`Acesso negado`).
Não foi tentado contornar essa restrição: backend antigo permaneceu ativo.
Assim, a correção backend do descanso está testada, mas **ainda não ativada**;
o frontend final está compilado. Reinício operacional permanece pendente.
Health local/público: 200; ambos servem o bundle final `index-BqerIGRp.js`.
Nove tabelas principais e valores dos acessos iguais ao backup após a tentativa
de reinício negada. Nenhum descanso foi aplicado automaticamente à mesa.

Correção posterior solicitada: não recolher as setas, mas removê-las. Removidos
JSX, estado de seleção usado só por essa ferramenta e CSS correspondente.
Handlers nativos de pointer/drag, snap, validação backend e retry foram preservados.
O smoke atualizado exige ausência completa desses controles e movimento direto
por mouse/toque com posição persistida após reload. Nenhuma alteração backend.

Validação dessa remoção: sete testes focados frontend PASS, typecheck PASS e
build nativo PASS (`index-CCa_wmf6.js`). Smoke real isolado PASS: mouse desktop,
toque em viewport móvel, ausência dos controles e persistência após reload.
Captura móvel inspecionada. Suíte frontend final: 271 PASS, seis bloqueados pelo
mesmo erro ambiental de acesso do esbuild. Um teste antigo ainda exigia as setas;
foi atualizado para exigir sua ausência e preservar os handlers pointer/movimento.
Essa falha intermediária não foi contabilizada como PASS.
Frontend novo confirmado local e publicamente (bundle HTTP 200), sem reinício
nem alterações no banco operacional. Checks e arquivos incluem também
`frontend/tests/spatial-grid.test.cjs`. O reinício pendente do descanso continua
separado desta alteração exclusivamente visual.
Backend reexecutado após a remoção: 783 testes PASS (320,728 s).
