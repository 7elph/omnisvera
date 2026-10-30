# Recuperação da mesa — 10/10/2026

## Escopo e evidências

Melhorias dirigidas aos incidentes relatados na conversa: falha ao carregar
personagens, carregamento indefinido, refresh frequente, combate e registro.
A transcrição da mesa ainda não foi fornecida; não se atribui uma causa única
a todos os sintomas nem se considera cada recusa do servidor um defeito.

O log `omnisvera-catalog-final-out.log` contém 47.171 respostas 200,
16 respostas 409 e 26 respostas 400. Há conflitos em comandos de combate e
recusas de confirmação de ataque. Os códigos, sozinhos, não distinguem
turno expirado, alvo alterado, proteção legítima e falha de interface.
Não se incluem tokens, conteúdo privado, banco ou logs neste relatório.

## Correções desta entrega

- Consultas de efeitos e ledger em banco inicializado agora são apenas
  leituras. Antes, cada consulta disputava locks de escrita para inicializar
  schema; o ledger ainda recriava triggers e refazia o backfill do histórico.
  Migração/inicialização continuam no startup e fallback de bancos novos;
  efeitos são lidos em uma única transação consistente, sem cache de estado.
- GETs simultâneos idênticos compartilham apenas a requisição em andamento,
  separados pelas credenciais. Cada consumidor recebe sua própria cópia.
  Não se armazena HP, turno ou recursos depois de terminar a requisição.
- Entrada, combate e mapas têm prazo de leitura de 10 segundos, inclusive
  para resposta cujo corpo não termina. Leituras podem voltar a funcionar
  na tentativa seguinte; mutações não são repetidas automaticamente.
- Entrada com acesso salvo recupera falhas temporárias, em intervalos de
  10 segundos ou quando a conexão/foco retorna. 401/403 não são repetidos.
  Respostas de um token antigo não podem autenticar outro acesso.
- Polling de combate, prévias, campanha e estado da sessão não se sobrepõe
  dentro de cada painel. Respostas de combate antigas não substituem uma
  versão mais nova confirmada.
- Reconexão realtime busca o estado atual, mesmo sem novo evento. Ticket
  parado tem prazo; socket sem pong por mais de 35 segundos é reconectado.
- Conflito 409 no painel de combate provoca uma leitura atualizada e orienta
  conferir o turno, sem passar turno ou atacar novamente automaticamente.
- Confirmação de ataque bem-sucedida seguida por falha de atualização é
  apresentada como aplicada, não como ataque recusado.
- Ataque de criatura/aliado pendente pode ser descartado explicitamente na
  interface para escolher outro. Descartar não aplica dano nem cria ataque.
- O atalho “Minha ficha” abre a ficha do proprietário sem depender de sessão
  ativa, aproveitando a vista de ficha já presente no worktree.

Autenticação, separação Mestre/Jogador, budget de ações, versionamento e
idempotência do backend permanecem intactos. Não houve alteração de regras,
fichas, valores persistidos, sessão 7, Vault, Godot ou mídia nesta entrega.

## Validação

- Backend: 443 testes passaram com `.venv-observer/Scripts/python.exe`.
  Há ResourceWarnings de conexões SQLite não fechadas em testes existentes;
  não foram ocultados nem corrigidos por uma refatoração nesta entrega.
- Frontend: 206 testes passaram, incluindo startup, timeout, concorrência,
  reconexão, respostas atrasadas e confirmação seguida de refresh falho.
- Typecheck passou; build passou. Vite ainda avisa sobre chunks >500 kB.
- `table_reliability_probe.py`: PASS por HTTP real, Mestre + Vezemir/Raziel,
  combate, ataque, confirmação idempotente, privacidade de efeitos/loot,
  distribuição e um único registro por ação.
- `cf01_probe.py probe`: PASS com resposta TCP descartada, reconexão,
  conclusão idempotente e um único registro.
- Primeiro ensaio HTTP encontrou efeitos reais já ativos na cópia do banco.
  Apenas a cópia temporária foi limpa via API antes da repetição bem-sucedida.
- Navegador Edge headless, build real: PASS, Mestre + Vezemir/Raziel/Morthak
  em contextos separados, jogadores em viewport 390×844. Falha na primeira
  conexão recuperada; fichas próprias carregadas; queda simulada manteve HP;
  mensagem perdida recuperada sem navegação/reload; combate visível aos três;
  passagem de turno do jogador refletida no próximo jogador. Sem pageerrors.
  A fixture não copia mídia do Vault: isto não é um aceite visual das artes.
- Carga: o primeiro ensaio de 80 GETs, 16 simultâneos e ledger de 500 entradas,
  teve 10 timeouts de 10 segundos. Depois da correção das consultas de banco,
  duas repetições passaram com 80/80; última: máximo 1,333 s, p95 1,303 s.
  O cenário de 150 entradas também passou antes da correção (máximo 2,043 s).
  Estes números são observações locais, não benchmark de rede pública.

Os ensaios usam somente uma cópia SQLite em diretório temporário, vault
temporário, tokens de fixture e localhost:8871. O banco da mesa não é escrito.

## Arquivos desta entrega

Código: `frontend/src/readJson.ts`, `frontend/src/api.ts`,
`frontend/src/App.tsx`, `frontend/src/pages/SessionWorkspace.tsx`,
`frontend/src/pages/CampaignMemoryPage.tsx`,
`frontend/src/components/CombatEncounterPanel.tsx`,
`frontend/src/components/MonsterAttackPanel.tsx`.

Backend: `backend/app/combat_effects.py`, `backend/app/session_ledger.py`,
`backend/test_table_read_only.py`, `backend/scripts/table_read_load_probe.py`.
Os testes novos reproduziram escrita de schema e bloqueio por outra conexão
antes da correção; agora passam, junto com bancos novos/legados e estado fresco.

Testes: `frontend/tests/access-recovery.test.cjs`,
`frontend/tests/combat-sync-recovery.test.cjs`,
`frontend/tests/realtime-recovery.test.cjs`,
`frontend/tests/table-recovery-smoke.cjs`,
`frontend/tests/workspace-read-timeout.test.cjs`,
`frontend/tests/combat-controls.test.cjs`,
`frontend/tests/campaign-memory.test.cjs`.

Documentação: este arquivo. Build local em `frontend/dist`, não versionado.
O worktree já continha outras alterações; elas foram preservadas, sem staging,
commit ou push nesta entrega.

## Limites e próximo aceite

Código/testes passando não prova estabilidade numa mesa real. Ainda é preciso
Mestre + pelo menos dois jogadores em redes diferentes, com celulares em
segundo plano, retorno, combate e registro por tempo prolongado. Também falta
cruzar a transcrição com rejeições e ações específicas.

Não se certifica aqui toda habilidade/magia, todos os clientes externos ou a
disponibilidade do Funnel. Na verificação desta entrega não havia backend
local respondendo em 127.0.0.1:8787; o serviço de túnel ainda tinha listeners.
Nenhum backend operacional foi reiniciado nem colocado online por este trabalho.

Somente o servidor de ensaio em 8871 foi reiniciado para carregar o backend
corrigido e encerrado ao final. Correções operacionais carregam no próximo
startup do backend existente; não se troca banco nem credenciais.

Para usar o build novo, inicie o Companion pelo launcher existente. Quem já
estiver com a versão anterior aberta precisa reabrir/atualizar uma vez para
carregar o código novo; os cenários testados de recuperação posterior não
dependem de refresh manual.
