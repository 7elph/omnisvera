# Ícones de ações na sessão e nos turnos

O registro usa o mesmo detalhe somente-leitura das fichas: ícone pequeno, nome clicável, imagem original e descrição. Abrir o card não executa ações nem gasta recursos.

O endpoint do ledger filtra autorização e registros anulados antes de resolver os cards. A projeção contém somente id, nome, descrição sanitizada e caminho da imagem da ação referenciada; não envia inventário completo, recursos, objetivos ou campos privados do Mestre. Mensagens livres e auditoria de estado não são reformatadas. Nomes reconhecidos usam a grafia cadastrada, preservando nomes próprios no restante da narrativa.

Armas confirmadas resolvem apenas o equipamento de papel `weapon`, não todos os itens passivos. Itens consumidos até zero continuam resolvíveis no histórico, sem voltar ao inventário. Imagens editadas são lidas do cadastro atual. Forma da Noite identifica o animal pelo anúncio histórico; registros sem animal usam a arte padrão de corvo.

Ativações de efeito feitas pelo jogador e magias/protocolos aprovados de Dorn ganham anúncio público idempotente na transação existente. Efeitos genéricos inseridos pelo Mestre continuam na auditoria privada. Os ícones junto dos nomes indicam **ações usadas no combate**, não efeitos persistentes. O marcador de início é preservado ao editar iniciativa e renovado no próximo combate; encerramento esconde os ícones, mas conserva o histórico.

Arquivos principais: `backend/app/action_cards.py`, `main.py`, `combat_effects.py`, `player_inventory.py`, `dorn_protocols.py`, `data/spell_images.json`; `frontend/src/components/SessionActionArt.tsx`, `CombatEncounterPanel.tsx`, `pages/SessionWorkspace.tsx`, `api.ts`, `styles.css`.

Verificação: 403 testes backend, 168 frontend, TypeScript e build; fixture React/CSS real desktop/mobile com ícones 22px e abertura dos dois detalhes. Consulta HTTP autenticada de Mestre, Raziel e Vezemir; os 38 registros públicos compartilhados entre os dois jogadores retornaram cards idênticos. Testes de projeção/privacidade/consumo até zero, deduplicação de anúncios, início de combate e escopo temporal. Não substitui sessão com Mestre e dois jogadores em dispositivos/redes diferentes. Combates iniciados numa versão anterior, sem marcador de início, não exibem ícones históricos nos turnos até o próximo combate, evitando associar ações antigas.
