# Fechamento do pacote de hoje — 23/10

Escopo: seis blocos de preparação para **Vezemir, Raziel e Dorn do Mestre**.
Não significa fechamento da biblioteca inteira ou certificação de mesa remota.
Branch `devin/create-omnisvera-class-standard`, HEAD `1a07a84`, sem commit/push.

Continuação: [conferência final dos quatro pedidos](TODAY_FINAL_CHECK_2026-10-23.md)
registra a recompensa aprovada, o encontro específico e as imagens/conexões atuais.

## Condução pronta para consultar

[Cola completa](preparation/TODAY_GM_PLAYBOOK.md): reunião → compras opcionais →
pesquisa opcional → cais → negociação/combate opcional → documentos/decisão.
Há também **Cola rápida · condução de hoje** dentro de cada uma das seis cenas,
com falas sugeridas, pistas, alternativas, limites das regras e encerramento.
O percurso curto é 23 → 26 → 28; não é obrigatório jogar os seis blocos.

## Pendências da preparação resolvidas

- Seis checklists **17/17**, com aceitação visual do agente registrada após
  revisar 12 capturas do visualizador privado em desktop/390 px. Cenas ainda
  privadas/rascunho, nenhuma sessão iniciada. Iniciar a sessão real é ação do
  Mestre quando a mesa começar, não um teste feito em produção.
- Morthak saiu do elenco ativo das seis preparações e seus pins ficaram ocultos
  nos cinco mapas usados hoje. Ficha, recursos, posições e histórico preservados.
- Lich antigo morto e esqueleto antigo vivo ficaram ocultos na arena, sem
  apagar, matar ou dispensar. Não os incluir na nova iniciativa.
- Dorn visível em Nimalis; imagens vinculadas aos quatro pins táticos que
  mostravam apenas o ícone genérico no visualizador de Cenas.
- Retrato real de Thoradin no cadastro/pin; símbolo anterior preservado.
- Dois cargos de conversa vinculados aos registros privados 20/21, com retratos
  **provisórios**. Não fixam nomes nem identificam Cassian retroativamente;
  não foram inventadas estatísticas de combate para esses NPCs.
- Teren era cadastrado como **humano**, mas tinha retrato de elfo. Corrigidos
  apenas retrato e vínculo do pin; raça, descrição e identidade preservadas.
  Não é identificação do pesquisador meio-elfo não nomeado da transcrição.
- Quatro POIs da arena ganharam ícones específicos: documentos, carroça,
  encaixe e saída. São marcadores, não novas regras de interação/walls.
- Confirmado no ensaio: **Abrir cena preparada na Mesa** já disponibiliza e
  seleciona o mapa vinculado. Portanto, escritório reservado antes da chegada
  é intencional, não falta de configuração. Capa ilustrada e mapa esquemático
  continuam separados. Não foram antecipadas pistas nem revelados inimigos.
- Laboratório atualizado com elenco, montagem, arte e limites atuais; evidência
  nativa vinculada à proposta 1, versão 6. Proposta continua rascunho, não cânone
  aprovado/executado pelo simples fato de possuir uma evidência de teste.

Quatro retratos foram gerados pela ferramenta integrada de imagens e salvos
em `frontend/public/companion-assets/preparations/`: `friday-thoradin-v1.png`,
`friday-military-role-v1.png`, `friday-conclave-role-v1.png` e
`friday-teren-human-v1.png`. Quatro ícones `poi-*-v1.svg` são código vetorial
do projeto, não fotografias geradas. Prompts/metadados/caminhos em
[FRIDAY_ASSETS.json](preparation/FRIDAY_ASSETS.json). Nenhum arquivo do Vault
ou arte anterior foi substituído/removido.

## Testes e ativação

- Backend: **1260 testes OK, 1 ignorado** no ambiente observer instalado.
  A primeira tentativa no ambiente de aplicação não tinha o SDK MCP; não
  foi apresentada como PASS. A seleção focal correta teve **42 testes OK**.
- Frontend: **396 testes PASS**; mais 25 testes focais reexecutados após as
  últimas referências de arte. Estes 25 são subconjunto, não 25 extras.
  Typecheck e build PASS; aviso conhecido de bundle >500 kB permanece.
- Teste RED reproduziu a rejeição de `ui_suite=friday` no leitor de evidências;
  correção de uma linha permite o lote já existente. Teste GREEN mantém
  rejeição de status inconclusivo, lote divergente/desconhecido e não concede
  certificação de toda ficha/proposta. Nenhum handler de combate mudou.
- Backend 8787 reiniciado pelo par Python verificado, preservando ambiente e
  acessos, sem reiniciar OpenCode/Tailscale. Conteúdo das **21 tabelas protegidas
  preservado**; inicialização atualizou só `updated_at` de Earthropo/Nimalia.
  Não houve restauração de banco por cima do estado atual.
- MCP `test-6f0496ec2d9b454ca44d955449654104`: **COMPLETED/PASS**, UI **7/7**:
  preparações, loja/carteira, duas metades de ações, passivas, turnos de invocações
  e descanso. API foi seleção focal da poção de Vezemir: **1 PASS**, não 91 casos.
- O smoke de preparações agora guarda cada cena nas duas larguras e verifica
  imagens carregadas. Na fixture, seis aberturas nativas selecionaram/revelaram
  o mapa correto ao jogador, publicaram a abertura no registro e aceitaram
  retry sem duplicar publicação. Inspeção anterior à abertura continua sem
  escrever/publicar/mover nada. Sessão criada pelo teste existe só em TEMP.
- **Limites:** abertura foi pelo endpoint nativo, não clique no botão de abertura
  da UI. A arena da fixture foi alterada pelo caso API antes das capturas e
  contém Hobgoblins de QA/posições de ensaio, não a montagem operacional. As
  posições e filtragem reais foram conferidas separadamente pela API. Ajustes
  posteriores de retrato Teren e pins Dorn/POIs foram conferidos por arquivos e
  URLs, sem recapturar as telas. `certification_ready=false`; celular físico,
  estabilidade prolongada e Mestre/jogadores em redes distintas inconclusivos.
- Último inventário de mídia: **105 arquivos distintos**, todos carregando e
  com formato válido; inclui os pins dos cinco mapas. Nenhum desses pins ficou
  sem imagem vinculada após o fechamento. Texto/pistas usam ícones, não arte
  exclusiva para cada parágrafo. A biblioteca inteira não foi ilustrada.

Recibos privados, sem credenciais:

- Preparação: `TEMP/omni-today-preparation-cx67_82x/`.
- Colas/laboratório: `TEMP/omni-today-notes-w4l71v2_/`.
- Aceitação/imagens/evidência: `TEMP/omni-today-visual-acceptance-0e7lcvoi/`.
- Restart: `TEMP/omni-evidence-restart-4x7hgn6g/`.
- Ensaio: `TEMP/omni-postreboot-readiness-hkx6osts/result.json`.
- Auditoria de mídia: `TEMP/omni-content-today-uslv1_ls/report.json`.

## Decisões e backlog que não devem virar promessa na mesa

**100 PO ao grupo:** aprovados pelo Mestre na continuação deste fechamento,
mediante registro ou informação verificável, mesmo sem combate. A condição
já pode ser oferecida no briefing. Cola privada e proposta de laboratório
atualizadas; nenhum valor foi creditado antecipadamente. Pagamento após conclusão.
Thoradin é loja de equipamentos com 37 ofertas/187 peças, **sem serviços**;
não se inventou reparo mágico, hospedagem ou preço para preencher uma aba.

Biblioteca geral: 10 NPCs sem retrato e 108/255 monstros sem imagem continuam
fora deste fechamento. Itens com fallback não equivalem a arte exclusiva.
Centenas de magias e todos os especiais do bestiário não foram automatizados.
Encontro de hoje tem quatro perfis básicos, não chefe certificado para nível 5.
Cronologia integral das sete transcrições e grandes respostas de lore continuam
fora do pacote. Não declarar que a campanha inteira está sem pendências.

## Arquivos tocados neste corte

- App: `backend/app/test_run_evidence.py` (allowlist do lote existente).
- Regressão: `backend/test_test_run_evidence.py`;
  `frontend/tests/friday-readiness.test.cjs` e `scene-preparation-smoke.cjs`.
- Conteúdo/documentação: este relatório, `TODAY_READINESS_2026-10-23.md`,
  `SESSION_CONTENT_AUDIT_2026-10-23.md`, `preparation/TODAY_GM_PLAYBOOK.md`,
  `FRIDAY_TABLE_SETUP.json`, `FRIDAY_ASSETS.json` e complemento em `FRIDAY_BLOCKS.md`.
- Oito assets novos mencionados acima. Operadores finitos privados em
  `.autonomy/runtime/`; bancos/recibos/credenciais não entram no Git.

Worktree misto anterior preservado. Sem staging, commit, push, processos
genéricos encerrados, novos modelos locais ou automações iniciadas.
