# Cenas: sequência e contextos

As preparações existentes aparecem numa sequência horizontal compacta, respeitando
`order_index`, com filtros de sessão, estado e busca. A numeração indica a posição
na lista filtrada; nenhuma cena é reordenada ou ativada no banco ao navegar.

O visualizador oferece seis cards: Exploração, Combate, Conversa, Comércio,
Investigação e Viagem / descanso. Cada um organiza os elementos já vinculados à
preparação em grupos adequados ao contexto. O contexto é uma preferência local
da prévia e volta a Exploração ao reabrir. Não altera o estado da sessão.

O mapa fica num card com miniatura. Ao clicar, abre o visualizador com o grid,
névoa e pins nativos, zoom limitado e inspeção dos pins. É possível voltar do
detalhe de um pin ao mapa e fechar com Escape, restaurando o foco ao card.

“Biblioteca” abre todos os elementos numa gaveta lateral no desktop e acima
dos grupos no celular. Tipos não destacados por um contexto continuam na
biblioteca. Trocar contexto ou abrir a biblioteca mantém a seleção de publicação.
“Levar seleção à Mesa” conserva o comando nativo, a confirmação e a idempotência.
Inspecionar ou trocar o layout não publica, movimenta tokens nem inicia combate.

O contexto Comércio mostra NPCs, pins e objetos vinculados; não inventa estoque,
preços ou serviços. O atendimento comercial continua usando o cadastro nativo.
Objetivos, notas e elementos privados continuam sujeitos à projeção de visibilidade
existente. Cenas permanece uma área do Mestre.

## Validação

- `scene-context.test.cjs`: agrupamentos, ordem, privacidade e seleção preservada.
- `scene-preparation.test.cjs`: regressões de carregamento, projeção e grid nativo.
- `scene-context-smoke.cjs`: build real em fixture TEMP, 1440/390 px, seis contextos,
  mapa compacto, modal/zoom/pins, foco, biblioteca, cancelamento e reload, sem
  mutações de interface; acesso privado indisponível para jogador.
- `scene-preparation-smoke.cjs` acompanha a nova abertura do mapa por miniatura.

Capturas exigem inspeção explícita. Emulação de 390 px não comprova aparelho
físico nem redes externas. Este corte organiza Cenas; não adiciona regras ou
catálogos paralelos nem muda as fichas reais.

### Resultado deste corte

- Frontend: 433/433 testes; typecheck e build aprovados (aviso de chunks >500 kB existente).
- Smoke em 1440/390 px: PASS; capturas de sequência, Exploração, Combate,
  Conversa, biblioteca e mapa revisadas pelo agente. Cinco tabelas de fichas e
  inventários operacionais permaneceram iguais; nenhuma mutação de interface
  foi enviada durante o smoke.
- Backend: suíte completa executada, 1596 testes e 1 skip. A primeira execução
  teve 18 falhas e 1 erro de infraestrutura por disputa da trava de trabalho com
  o smoke visual. Com o smoke encerrado, os três módulos afetados
  (`test_memory_guard`, `test_seven_closure`, `test_sheet_runner_batches`)
  passaram integralmente: 60/60. Não houve mudança de backend neste corte;
  não se declara uma segunda execução integral sem falhas.
- A verificação antiga do tema foi atualizada para reconhecer somente a exceção
  já existente de CSS dos controles de Dissipar; continua rejeitando prioridades
  globais fora desse seletor específico.
- Sem staging, commit ou push. Artefatos/evidências locais ficam fora do código.
