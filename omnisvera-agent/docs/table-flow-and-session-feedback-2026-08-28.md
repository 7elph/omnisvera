# Fluxos rápidos e feedback das três sessões

## Fonte e limites

Análise baseada no relato das três sessões fornecido pelo usuário nesta conversa, não em nova audição das gravações. Não transforma a dungeon tutorial em modelo obrigatório das próximas sessões. Worktree misto preservado; sem alterações canônicas ou nova arquitetura.

## Correções desta execução

- Cabeçalho: retrato e nome/descrição novamente lado a lado; nível na coluna livre à direita. Retirada a regra que fazia o nome ocupar uma linha inteira abaixo da foto.
- Anotações novamente recolhidas, mantendo textarea e salvamento explícito.
- Compositor do chat antes da lista de eventos do registro.
- Painel do Mestre: Combate abre os ataques da ficha selecionada; Itens e loot abre diretamente o editor de itens; Pedir rolagem abre o formulário já expandido, antes da rolagem livre e com personagem selecionado.
- Nenhum novo motor de combate, loot ou dados.

## Pedidos diretos versus fricção observada

| Evidência no relato | Natureza | Estado atual e intervenção útil |
| --- | --- | --- |
| S3: informação antiga perdida no chat; pedido de nota individual | Pedido direto | Notas persistentes já existem; agora recolhidas na ficha. Recuperar pistas antigas no registro é um problema diferente de guardar novas notas. |
| S3: drops com ícone e consulta rápida | Pedido direto | Inventário, editor, concessão e espólios existem. Atalho abre o editor; o Mestre ainda revisa/revela/distribui o espólio. |
| S3: mestre pede Carisma, jogador recebe e toca para rolar | Expectativa explícita e falha relatada | Fluxo persistente existe. Atalho direto e ensaio com dois clientes confirmados nesta execução. |
| S3: pins de monstros, selecionar alvo, Grisalma e modificadores | Pedido/ideia direta | Pins, seleção de alvo e resolução/confirmar ataque existem. Combate tem acesso direto; não equivale a automação de todas as ações narrativas. |
| S3: dois ataques resolvidos sobre um alvo | Pedido/ideia direta | O corte validado resolve um ataque. Multiataque não foi implementado aqui. |
| S1–S3: dificuldade de encontrar habilidades e poderes disponíveis | Fricção observada | Seções de atributos, recursos, ataques, magias e habilidades existem. Clareza do que está disponível agora ainda merece validação com jogadores; não há evidência aqui de que toda a dificuldade foi eliminada. |
| S2–S3: lembrar HP, veneno, turnos, recursos, golem/esqueleto | Fricção observada | Há estado de ficha/tokens; não foi comprovado um fluxo integrado completo de duração, regeneração ou invocações. Não acrescentado um motor de efeitos nesta tarefa. |
| S1: prazer de usar dados físicos | Fato de uso | Ataque aceita d20 físico; preservar modo híbrido, não impor animação digital. |
| S3: narrar finalização e decidir o que reportar sobre o golem | Fato narrativo | Preservar intervenção do Mestre. Relatório canônico automático seria inferência de produto, não pedido direto demonstrado. |

O pedido adicional de mais imagens aparece também no feedback posterior do usuário nesta conversa. É consistente com a necessidade de representação visual, mas não se presume que toda criatura precise de arte definitiva antes de entrar em jogo.

## Os três caminhos simples

1. Combate: ficha → ataque → alvo → resolver → conferir → confirmar. Backend calcula; confirmação aplica dano e ledger uma vez.
2. Drop: monstro zerado com tesouro → gerar → revisar → revelar → distribuir. Item criado manualmente usa o editor/concessão existente. Morte não distribui automaticamente.
3. Rolagem solicitada: painel Mestre → Pedir rolagem → jogador/teste → enviar. Jogador recebe aviso e confirma; Mestre recebe o resultado.

## Demora dos dados: evidência

Cinco repetições por HTTP real na cópia SQLite de ensaio em loopback:

- Rolagem livre: 14,5–41,5 ms.
- Criar solicitação: 90,9–348,3 ms.
- Consultar pendências: 7,6–9,1 ms.
- Concluir solicitação: 32,7–40,9 ms.
- Histórico do Mestre: 11,1–12,9 ms.

Esses números não medem 4G, Funnel ou o aparelho físico do jogador.

Na apresentação anterior, o tempo mobile era 1,65 + 2,35 = 4 segundos; o relógio somava delta limitado a 1/30 s. Reprodução determinística do algoritmo: a 15 FPS levava cerca de 8 s reais; a 10 FPS cerca de 12 s. O overlay saía após 5,2 s, podendo sumir antes de os dados assentarem.

Correção: relógio visual usa tempo real; física mantém delta limitado. Assentamento visual em 1,5 s e overlay em 2,5 s. Resultado numérico não depende mais do carregamento/inicialização do 3D. Isso não significa latência de rede zero. Polling de recuperação permanece em 3 s.

## Validação

- 88 testes backend aprovados.
- 22 testes frontend aprovados; novos testes de atalho GM, bloqueio do formulário GM para jogador, relógio a 60/30/15/10 FPS e resultado antes de physics-ready.
- TypeScript aprovado.
- Vite aprovado, com aviso preexistente de chunk Three.js acima de 500 kB.
- Starlette/httpx mantém aviso de depreciação; diff mantém avisos LF/CRLF.
- Viewport 390×844: retrato à esquerda, texto no meio, nível à direita; notas fechadas; compositor antes do histórico.
- Duas sessões no navegador, credenciais de ensaio: Mestre solicitou “Teste rápido de mesa”; jogador respondeu; resultado 4 + 1 = 5 apareceu no histórico do Mestre sem Atualizar.
- Link público retornou HTTP 200 com build index-D-UHa45l.js.

Não foi realizado teste em celular físico fora de casa nesta execução. O backend da campanha não recebeu rolagens de ensaio e não precisou ser reiniciado.

## Arquivos e checkpoint

Frontend: CharacterLevel.css, CharacterNotes.tsx, SessionWorkspace.tsx, styles.css, DiceTray.tsx, DiceRollOverlay.tsx, DicePhysicsCanvas.tsx, novo diceTiming.ts e testes associados.

Diagnóstico: backend/scripts/roll_latency_probe.py, restrito à cópia de ensaio loopback e credenciais não operacionais.

Checkpoint local: .assistant-runtime/checkpoints/table-flow-2026-08-28. Sem commit/push devido ao trabalho misturado.
