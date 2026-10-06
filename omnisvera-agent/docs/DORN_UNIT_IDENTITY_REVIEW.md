# DORN-7 — corte de identidade da ficha, 2026-10-05

## A. Estado inicial

HEAD `eb20a2c4e6f396032d7a89f778e2ab1d509713de`, branch `devin/create-omnisvera-class-standard`. Worktree já suja, com mudanças anteriores de combate, invocações, Raziel e outras áreas. Nenhum reset, commit, push ou limpeza. Este corte não altera backend, Vault, seeds, banco ou credenciais.

## B. Auditoria antes da implementação

| Necessidade | Suporte atual | Reutilizável | Mudança mínima |
|---|---|---|---|
| Traços de Constructo | `definition.abilities.racial`, preenchido pela ficha aprovada | Sim | Seção recolhível com cláusulas legíveis e aviso de adjudicação |
| Sistemas da Unidade | PV/condições e inventário | Sim, parcialmente | Projeção dos dados; comunicação/protocolo sem estado formal continuam desconhecidos |
| Ações/Protocolos | `session_abilities`, grupos e handlers existentes | Sim | Categoria de apresentação; nenhum protocolo novo concedido |
| Magias | Preparações e catálogo atual, efeitos registrados | Sim | Navegação ao catálogo original e painel dos efeitos da ficha |
| Inventário | Itens e diálogo de inspeção | Sim | Identificação de componentes/ferramentas e abertura do item existente |
| Combate | Ataques, magias, turnos, entrada incremental e autoridade GM | Sim | Nenhuma alteração |

Fontes lidas: `backend/app/data/dorn7_mage2.json`, `backend/app/dorn_mage.py`, `backend/app/companion_promotion.py`, projeção da ficha em `main.py`/`character_play.py`, avanço de nível, componentes de ficha e testes. Referência de contrato: `CAMPANHA/DORN_7_MAGO_2_APROVADO.md`; lore lido para contexto, não copiado para estado ou UI.

Achado crítico: Punho/Proteger pertencem à versão substituída, não cumulativa. Não restaurar por estética. O arquivo de aprovação atual descreve imunidades/JP condicionais/reparo assistidos: texto de regra não comprova execução automática.

## C. Implementação

- Dorn permanece na ficha padrão dos jogadores, controlado pelo Mestre.
- Componente de apresentação GM-only com cinco seções recolhíveis: traços, sistemas, ações/protocolos, componentes/ferramentas e efeitos registrados.
- Traços vêm do texto racial existente, sem nova regra ou bônus.
- Integridade usa PV reais e condição `desativado`, quando existente. Núcleo e memória são identificados no inventário atual. Comunicação e protocolo ativo mostram explicitamente ausência de registro formal.
- Categoria de protocolos reutiliza `session_abilities` com grupo `Ações / Protocolos`. Catálogo vazio não cria ações fictícias.
- Operar núcleo navega às Magias existentes, sem gastar recurso. Inspecionar abre o diálogo existente do item, sem revelar informação inventada.
- Núcleo: sistema integrado/grimório; Kit: ferramenta sem cura instantânea; Cristal: componente narrativo; Compartimento: equipamento com capacidade não definida. Não criar conteúdo/armazenamento novo.
- Efeitos exibem somente registros cujo alvo é a ficha de Dorn, com duração e modificadores legíveis. Preparação gasta não cria ou comprova efeito. Efeitos aplicados apenas a um pin, e não à ficha, não entram nessa projeção.

## D. Fora do corte

Nenhum aumento de PV, CA, atributos, dano, ataques, preparações ou resistências. Nenhuma mudança em permissões, iniciativa, magias, progressão ou combate. Nenhum sistema de memória/núcleo/reparo, nem novos protocolos mecânicos. Origem e segredos não são inferidos do lore. Campos desconhecidos não recebem “Estável”, “Operacional” ou “Fragmentada” inventados.

## E. Arquivos deste corte

- `frontend/src/components/DornUnitIdentity.tsx`: projeção e classificação contextual dos itens existentes.
- `frontend/src/pages/SessionWorkspace.tsx`: montagem na ficha padrão e callbacks de inspeção/navegação; preservar diffs anteriores.
- `frontend/src/styles.css`: estilos restritos a `.dorn-unit-identity`, compactos e responsivos.
- `frontend/tests/dorn-unit-identity.test.cjs`: privacidade GM-only, dados ausentes, valores derivados, callbacks sem mutação e efeitos filtrados.
- `frontend/tests/dorn-unit-visual.cjs`: ensaio isolado do componente real com CSS real; sem APIs/tokens/banco.
- Este relatório.

## F. Checks efetivamente executados

- `.venv-observer\Scripts\python.exe -B -m unittest discover -s backend -p 'test_*.py'`: 289/289 PASS.
- `node --test tests/*.test.cjs`: 120/120 PASS.
- `npx --no-install tsc --noEmit`: PASS.
- `npm run build -- --outDir "$env:TEMP\companion-dorn-identity-build"`: PASS; dist operacional não substituído.
- `git diff --check -- backend frontend docs`: PASS.
- QA visual: `OMNISVERA_QA_MODULES` apontando ao Playwright já instalado; `node tests/dorn-unit-visual.cjs`: mobile 390×844 e desktop 1440×900 PASS, sem overflow horizontal.

Avisos existentes: ResourceWarning de conexões SQLite nos testes e tamanho dos chunks Vite. Não foram ocultados nem tratados como falha.

## G. Evidência visual e limites

Capturas locais finais em `%TEMP%\companion-dorn-visual-urniPt`: mobile/desktop, recolhidos/expandidos. Componente real renderizado em Edge headless com fixture baseada na ficha aprovada e CSS real. Sem autenticação ou dados reais. Isso comprova a composição isolada; não comprova a ficha inteira integrada, funcionamento dos callbacks no app ou mesa multicliente. Os callbacks foram cobertos por teste de componente.

Por padrão há cinco títulos compactos. Ao expandir, texto e listas quebram em linhas, componentes oferecem inspeção e sistemas mostram dados/ausências. Não usar a captura desktop como prova da distribuição completa do workspace: ela mostra apenas a coluna do componente.

## H. Revisão de Sage

Definir quais protocolos concretos serão autorizados e suas ações/custos/alvos/duração. Formalizar estados de comunicação/protocolo/memória/núcleo se desejar além dos dados atuais. Reparo e automatização dos traços aprovados continuam uma decisão e um corte separados; não solicitar novamente aprovação das imunidades já registradas na ficha, somente como automatizá-las. Escudo em turnos de exploração não deve virar duração em rodadas por conveniência.

Parado para revisão. Sem deploy, reinício, commit ou push neste corte. Versão online permanece intacta.
