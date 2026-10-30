# Ficha compacta, mapas e descanso

## Entregue em código

- Zoom mobile cresce dentro de um viewport rolável limitado; não aumenta sua
  altura nem captura a navegação inteira. Jogador pode rolar o mapa ampliado.
- Magias, grupos de habilidades, especialização/passivas e traços de constructo
  começam recolhidos. Grupos com ações abrem ao entrar em combate; fechamento
  manual continua possível. Ataques permanecem visíveis.
- Inventário compacto, nomes/quantidade/ações essenciais, borda de equipado.
  A meta é reduzir altura sem reduzir os alvos de toque a tamanhos inutilizáveis;
  não é uma escala de 50% aplicada ao texto ou à tela inteira.
- JP é um botão de escudo/JP; dados usam só seu ícone, ambos com nome acessível.
- Equipamentos abaixo dos dados: projeção somente dos itens/slots persistidos.
  Slots vazios não concedem itens nem criam bônus. Cinto/bolsa personalizados
  já cadastrados são preservados. Não há nova regra de mãos/empunhadura.
- Ícones de efeitos da ficha estão na área de Status; o header compacto mantém
  os seus ícones. Removida a lista duplicada de efeitos de Dorn e seus enums.
- Diagnóstico removido da ficha, mantendo compatibilidade dos endpoints antigos.
- Maestria informa +1 no ataque e +1 no dano com Grisalma equipada. Sem mudar BA.
- Jogadores veem somente os valores das quatro moedas, na ordem platina, ouro,
  prata, cobre. Mestre mantém edição; comércio existente continua separado.
- Biblioteca de mapas tem miniaturas e grupos a partir do nome: mundos/cidades,
  `S7`/`Sessão 7` etc., outros. Isto não é inferência de sessões jogadas. Nenhum
  mapa, imagem, grid, fog ou pin foi apagado ou convertido compulsoriamente.
- Teia continua armazenada no mapa de origem, mas pins antigos de um mapa
  inativo não aplicam penalidades globais na ficha. O armazenamento da área
  no conjurador não é mostrado como se ele estivesse preso nela. Ocupantes reais
  da área recebem o efeito quando aquele mapa é usado.
- Descanso geral usa a limpeza completa já implementada e atualiza imediatamente
  o snapshot de efeitos no cliente. Não executa descanso na mesa como teste.

## Limites mecânicos deliberados

Descanso do Mestre encerra efeitos temporários e recupera recursos conforme o
cadastro. Não remove passivas raciais ou bônus de equipamento, não distribui
itens e não mata invocações permanentes por inferência. Efeitos pessoais seguem
suas durações; duração ficcional pode sobreviver ao combate. Área e efeito pessoal
não são a mesma coisa: não prender toda magia pessoal a uma imagem de mapa.

Não foi imposto “um uso diário” a todas as habilidades. Foram preservados usos,
custos, círculos, recargas e exceções aprovadas. Efeitos por vários descansos e
preparação de dias/semanas precisam de regras explícitas, não botões novos na ficha.
As ações diretas atuais não ganharam uma etapa extra de preparação.

Arsenal novo de Raziel permanece na proposta `RAZIEL_HEMOMANCY_PIPELINE_PROPOSAL.md`,
sem substituir o conjunto aprovado por inferência de aprovação dos números.

Comércio já usa mercadores com local e estoque individuais, pechincha e transações
nativas. Vincular cada NPC/ponto do mapa a serviços e abrir compra autônoma para
jogadores ainda exige um corte de autorização/visibilidade/transação: não foi
criado um endpoint público de estoque privado nem inventadas lojas/serviços.

## Arquivos deste corte

Backend: `app/action_cards.py`, `app/character_play.py`, `app/dorn_spell_pack.py`,
`scripts/run_sheet_test.py`, `test_effect_map_scope.py`, `test_vezemir_sheet.py`.

Frontend: `components/SheetSection.tsx`, `EquipmentLoadout.tsx`,
`CurrencyCounters.tsx`, `DornConstructDetails.tsx`, `DornProtocolControls.tsx`,
`WorkspaceMapLibrary.tsx`, `mapManagement.css`, `pages/SessionWorkspace.tsx`,
`companionTheme.css`; testes `compact-sheet.test.cjs`, `compact-sheet-smoke.cjs`,
`currency-counters.test.cjs`, `session7-preparation.test.cjs`,
`morthak-new-spell-art-smoke.cjs`, `design-system-smoke.cjs`,
`approved-spells-smoke.cjs`, `map-toolbar-rest-smoke.cjs`.

Documentação: este documento, `AI_TEST_TOOLS.md`, `CURRENT_COMPANION_CODE.md`.
Worktree misto preservado; sem staging, commit ou push.

## Verificação

Testes RED reproduziram área aplicada em outro mapa e ícone indevido no conjurador.
Após a correção: backend completo 801 testes OK; frontend completo 287 testes OK;
typecheck e build padrão OK. Warnings preexistentes de SQLite/chunks grandes
continuam presentes. Evidência visual e ativação registradas abaixo após conclusão.

Ensaio final `test-37c19066ed78468bb72f6fd628543991`: COMPLETED/PASS,
quatro cenários de API selecionados e **9/9 scripts visuais PASS**, após as
correções abaixo. Inclui alternância repetida sem cards duplicados, fichas nas
quatro identidades, detalhes de magias, equipamentos, descanso e drag/reload.
Zoom mobile de aproximadamente 210% manteve a altura do canvas, criou scroll
interno sem ampliar a largura do documento e permitiu navegar para Mestre/Mesa.
Captura `map-390.png` inspecionada. É emulação de viewport/toque, não teste
no aparelho físico nem em redes distintas. A fixture não certifica toda mídia.

### Falhas encontradas e corrigidas no ensaio

- `test-4635f672cdad4b17af26ee2a52afd735`: 79 cenários de API PASS, três
  bloqueios esperados (armas/componentes ausentes). UI FAIL: chaves React repetidas
  entre notas, carteira e o novo grupo de magias podiam duplicar cards. Corrigido
  com namespaces de chave, teste RED/GREEN e alternância repetida das quatro fichas.
- `test-1762eaa037b645fcb8310eb4036edd24`: os quatro ataques e os cinco primeiros
  scripts visuais passaram, incluindo alternância sem duplicação e Relâmpago.
  O script design-system falhou ao iterar locators de grupos fechados enquanto os
  abria (lista mudava durante a iteração). Corrigido o driver para usar lista
  estável e verificar cada estado. Esta falha não foi apagada ou chamada de PASS.

### Ativação

Backend reiniciado pelo lançador oficial, de PID 78724 para 123788. Health
autenticado e frontend público: HTTP 200. Tokens preservados por comparação
do conteúdo JSON. Banco, fichas, recursos, sessão, combate, inventário, pins,
grids e posições preservados por comparação das tabelas. Nos três mapas oficiais
(Nimalis, Nimalia, Earthropo), a inicialização só renovou `updated_at`; IDs, imagens,
visibilidade e demais dados não mudaram. Nenhum mapa adicionado/removido.

Backup privado: `backend/data/backups/pre-compact-activation-20261015-051226`.
Não foi acionado descanso nem ataque no operacional. Os efeitos antigos só serão
limpos quando o Mestre conceder descanso; não foi simulado descanso em produção.
Mesa física/redes distintas continuam não comprovadas.
