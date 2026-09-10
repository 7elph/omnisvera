# Anotações de personagem e revisão do OpenCode — 2026-08-28

## Escopo e estado

Branch: `devin/create-omnisvera-class-standard`.
HEAD preservado: `0f75a3aafc28bd1b16e8ceddcb36f6aae975c69e`.
Worktree já continha alterações de Companion, Vault e mídia. Nenhuma delas foi revertida.

## Implementação entregue

Anotações persistentes por personagem, acessíveis ao dono e ao Mestre, em uma seção recolhível abaixo do inventário da Mesa. Salvamento explícito, limite de 12.000 caracteres e controle de versão contra sobrescrita entre dispositivos. Repetir o mesmo conteúdo salvo é idempotente. Falhas preservam o rascunho na tela. É necessário salvar antes de trocar de ficha; rascunhos não são armazenamento persistente.

As notas ficam em tabela SQLite própria. Não são copiadas ao chat, ledger, respostas públicas de ficha ou MCP. Os endpoints GET e PUT `/characters/{profile_id}/notes` usam a autorização existente e respostas privadas sem cache.

Arquivos adicionados:

- `backend/app/character_notes.py`
- `backend/test_character_notes.py`
- `frontend/src/components/CharacterNotes.tsx`
- `frontend/src/components/CharacterNotes.css`
- `frontend/tests/character-notes.test.cjs`
- Este relatório.

Arquivos existentes modificados pontualmente:

- `backend/app/main.py`: autorização e endpoints.
- `frontend/src/api.ts`: contrato e chamadas de notas.
- `frontend/src/pages/SessionWorkspace.tsx`: seção na ficha ativa.
- `frontend/src/pages/PlayableCharacterSheet.tsx`: componente compartilhado na ficha alternativa.

## Validação

- Backend, em `backend`: `.venv/Scripts/python.exe -m unittest discover -s . -p 'test_*.py'` — 84 testes aprovados, incluindo 10 de notas.
- Frontend: `node --test tests/dice-tray.test.cjs tests/character-notes.test.cjs` — 18 testes aprovados, incluindo 5 de notas.
- `npx --no-install tsc --noEmit` — aprovado.
- `npm run build` — aprovado.
- `git diff --check` — aprovado; avisos de conversão LF/CRLF em arquivos existentes.
- Aviso backend: depreciação de httpx no Starlette TestClient.
- Aviso Vite: chunk Three.js acima de 500 kB.

Testes verificaram ownership, autenticação, Mestre, isolamento entre personagens, persistência, versões conflitantes, repetição, tamanho e payload inválido. Testes de componente verificaram salvamento, duplo clique, erro e preservação de texto digitado durante a requisição.

Em cópia temporária do banco, a interface foi testada em viewport 390×844: salvar, recarregar e recuperar as notas. Isso não equivale a teste em aparelho físico. Nenhuma nota de ensaio foi inserida no banco da campanha.

O backend real respondeu ao GET novo e serviu o build `index-CSQSc87G.js`. Não foi necessário reiniciá-lo nesta etapa.

## Revisão das alterações recentes do OpenCode

A revisão se baseia no diff local e nos arquivos recentes, não em um commit exclusivo do OpenCode. Não é possível atribuir a ele todas as alterações antigas do worktree.

1. **Editor de nível/XP fora da tela ativa.** `PlayableCharacterSheet.tsx` ganhou editor/modal, mas `App.tsx` monta `SessionWorkspace` na Mesa do Mestre e do jogador. Portanto essa implementação não torna o editor disponível na Mesa atual.
2. **Salvamento rejeitado pelo backend.** `saveLevelAndExperience` envia `progression` em `updateDefinition`. `character_play.py` rejeita campos fora de `DEFINITION_FIELDS`, que não inclui `progression`. A chamada direta com o payload reproduziu `ValueError: Campos de definição não permitidos: progression` antes de qualquer escrita no banco. Mesmo se a ficha alternativa fosse aberta, o salvamento não funcionaria.

As alterações do OpenCode foram preservadas, não corrigidas neste corte de anotações/revisão.

## MCP: observação atual, não declaração de correção do 401

Na conversa de controle do ChatGPT, a chamada real `memory.search(query="Nimalis")` funcionou e retornou lista vazia. `system.health` também funcionou. Auditoria local correspondente:

- `2026-08-28T02:04:05.361556+00:00`: memory.search, success.
- `2026-08-28T02:04:10.070382+00:00`: system.health, success.

`memory.search` consulta memória operacional, não as notas do Vault. A lista vazia não significa ausência de lore sobre Nimalis.

O erro `tunnel_active_organization_required` relatado em outra conversa não foi reproduzido neste teste. Ainda é necessário o link da conversa que falha para comparar o mesmo caminho. Não houve rotação de chave, ampliação de permissões ou alteração do túnel nesta etapa. O MCP permanece read-only.

## Checkpoint

Snapshots antes/depois em `.assistant-runtime/checkpoints/player-notes-2026-08-27/`, fora do Git. Não contêm banco nem credenciais. O snapshot posterior de `PlayableCharacterSheet.tsx` também contém alterações concorrentes do OpenCode; não deve ser aplicado como rollback integral.

Nenhum commit novo: há sobreposição no mesmo arquivo com trabalho concorrente. Nenhum push.
