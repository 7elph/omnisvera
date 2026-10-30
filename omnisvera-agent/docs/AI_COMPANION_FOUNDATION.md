# Base para propostas e testes por IA

Este documento mapeia o código existente; não é um novo formato de campanha.
Índice legível por IA: `AI_COMPONENT_MAP.json`, com arquivos, armazenamento,
contratos, rotas, permissões e extensões. Testes verificam que essas referências
existem. O backend e `/openapi.json` continuam sendo a autoridade dos contratos.

## Entrega atual

Concluir as lacunas de ações antes de criar um gerador de testes:

- Raziel: conectar Arma de Sangue, Garras Predatórias, Investida Predatória e
  Sangue Defensivo com valores explicitamente aprovados; d20 físico, preview,
  confirmação, custo, orçamento de ação e expiração nativos.
- Caixão: comando pessoal atômico, fora de combate; uso gasto só é recarregado
  pelo descanso do Mestre. Não há pedido de aprovação a cada uso nem cura com 0 PV.
- Dorn: Kit de Reparo consumível; cinco repostos conforme autorização.
  Texto antigo de override não deve prevalecer sobre o cadastro atual aprovado.
- Armas: adagas espectrais têm os dois modos já documentados; Vezemir usa sua
  adaga à distância e conserva Grisalma no corpo a corpo. Morthak usa Adaga de
  Osso, não um arremesso fictício de cajado. Modo sem fonte válida é indisponível.

O ensaio atual já lê fichas reais numa cópia, chama APIs nativas e exporta
ação/consequência/recibo. `test_sheet.ps1` agora prepara e executa esse ensaio
por seleção de personagem, começando por Raziel e Morthak, com relatório de
inventário completo e cobertura baseada no resultado de cada cenário. Uso:
`SHEET_TEST_RUNNER.md`. Continua usando adaptadores específicos, não é um executor
universal gerado por IA. Traços narrativos/passivas não estão todos automatizados.

O operador agora é um agente: `companion-tests` no OpenCode expõe discovery,
start e status via MCP local, com schemas estruturados, recibos persistidos,
limite de concorrência/timeout e saída privada. Contrato: `AI_TEST_TOOLS.md`.
Isso não publica ferramentas remotas nem autoriza alteração do estado real.

## Ordem dos próximos cortes

1. **Contrato de ação executável:** identificar alvo, origem da regra, comando,
   custo, timing, duração, confirmação e testes mínimos. Distinguir automático,
   assistido, passivo, bloqueado e indisponível. Não equiparar `structured` a pronto.
2. **Executor de teste por ficha:** usar esse contrato para criar casos numa cópia
   temporária. Mesmo pipeline de personagens, summons e tokens de NPC/monstro.
   Verificar acerto/erro, efeitos, custo insuficiente, limites de turno, retry,
   permissões, persistência e ficha física Mestre/proprietário.
3. **Cenas / Laboratório:** visão privada de propostas, histórico de versões,
   botão de ensaio isolado e resultado verificável. As cenas reais continuam
   acessíveis; nunca trocar toda a aba por conteúdo experimental de uma vez.
4. **Compêndio de PDFs:** importar em lotes pequenos com fonte, edição/página,
   regra normalizada, decisão de campanha, estado de aprovação e caso de teste.
   A biblioteca de regras deve abastecer a ficha e seus cards, não duplicá-los.
5. **NPCs e mapas ampliados:** ficha tática detalhada ligada ao NPC persistente;
   pontos de interesse ligados a cenas, NPCs e elementos já existentes.

## Cenas como sandbox, sem motor paralelo

Já existem `draft`, checklist, participantes, elementos, notas privadas,
publicação e abertura na mesa. Para uma proposta: `draft` e `visibility=gm`;
`SceneCreate` hoje tem visibilidade padrão `table`, portanto a IA deve declarar
`gm` explicitamente. Editar uma proposta não equivale a publicá-la ou iniciar combate.

Ensaio precisa usar banco/vault/token descartáveis: criar um mapa ou iniciar um
encontro na produção não vira seguro apenas por chamar a cena de “teste”. Um
futuro job guarda referência ao rascunho/versão e evidência de resultado; o
Mestre decide se aplica, revela ou inicia. Preservar rollback e auditoria nativa.

Não foi criada nesta entrega uma tela nova de laboratório, importador de PDFs,
executor universal ou integração automática de OpenCode. Primeiro corte é o
fechamento mecânico e o mapa de integração, não uma implementação incompleta
de todos esses sistemas ao mesmo tempo.

## Analisar sessões e roleplay

Usar relatos/transcrições e ledger como evidência, indicando fonte e contexto.
Separar fatos confirmados, relato de NPC, hipótese do Mestre e possibilidade
ainda aberta. `game_sessions` já admite narrativa, análise do Mestre e fontes;
NPCs já têm memórias com confiança e visibilidade.

A IA pode sugerir alternativas: negociar, investigar, ignorar, recuar, combater,
ou uma escolha inesperada. Cada alternativa descreve resposta do mundo,
informação disponível e consequências condicionais. Não gerar falas/ações de
Vezemir, Morthak ou Raziel, nem registrar previsão como evento ocorrido.
Preferências observadas de roleplay são contexto, não autorização para decidir.

## PDFs, itens e biblioteca

Não há compêndio completo de magias hoje: dados estão em catálogo de habilidades,
overrides e módulos de execução específicos. Bestiário SRD já tem catálogo
local com 255 entradas e atribuição/licença registrada; isso não prova que todas
as habilidades de todos os monstros têm executores automáticos.

A inspeção de nomes de arquivos no repositório não encontrou os PDFs de regras
da campanha (apenas PDFs de tutorial de assets). Para a etapa de compêndio será
necessário fornecer/indicar os livros. Não importar regras de memória nem
atribuir uma regra de campanha ao livro sem evidência. Preservar atribuição e
limites da licença; usar descrição própria quando reprodução não for permitida.

## Como uma IA trabalha aqui

Ler `AGENTS.md`, `CURRENT_COMPANION_CODE.md`, este índice e os arquivos do bloco
relevante. Inspecionar a branch/worktree; não substituir alterações de outro
agente. Usar APIs/contratos nativos, testes RED/GREEN e credenciais de fixture.
Propostas pendentes não habilitam novos valores no operacional.

OpenCode pode ser aberto manualmente por `start_opencode.ps1`. Não depende de
uma IA específica: o índice e os ensaios são arquivos do projeto. A integração
futura deve conceder acesso somente ao que foi autorizado; nunca entregar tokens
da mesa em prompts, artefatos, logs publicados ou commits.
