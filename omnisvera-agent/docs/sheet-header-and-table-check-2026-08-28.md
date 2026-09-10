# Cabeçalho e verificação rápida da mesa — 2026-08-28

## Entrega

- Removido ATIVO de PERSONAGEM na ficha da Mesa.
- Nível à direita do retrato, número em cima e legenda embaixo. Componente compartilhado entre Mesa e ficha alternativa; 48 px contra 18,88 px do HP medidos na Mesa mobile.
- Anotações abertas imediatamente abaixo do cabeçalho e antes da vida: textarea e Salvar alterações. Removidos textos explicativos, contador e timestamp. Erros e recarregar aparecem somente em caso de falha.
- Botão Editar nível e XP exclusivo do Mestre, com formulário e bloqueio de envio duplicado. Endpoint GM existente reutilizado; experience agora é uma sobrescrita validada e persistida, não um objeto progression arbitrário.
- Nenhuma alteração de XP da campanha no teste; a edição 2/1250 foi feita em banco temporário.

## Acesso

Configuração observada: Tailscale Serve na porta 8787 privado e Funnel já ativo em HTTPS/443 para o mesmo Companion.

- Público: https://desktop-p30ui0j.taildecf09.ts.net
- Privado: https://desktop-p30ui0j.taildecf09.ts.net:8787

O público respondeu HTTP 200. O privado exige acesso Tailscale autorizado. O token individual do Companion continua necessário em ambos. Não foi criada ou ampliada exposição de rede; o Funnel já existia. Não houve teste no dispositivo da outra pessoa.

## Pins

GET autenticado com cada um dos quatro perfis: todos recebem um pin próprio e cinco pins no total na Dungeon Part 1. Nimalis, Nimalia e Earthropo retornam zero pins tanto ao Mestre quanto aos jogadores: os pins não estão cadastrados nesses mapas. Não foram inventadas posições nem duplicados pins entre mapas.

A visibilidade continua respeitando mapa e fog; esta consulta não prova visibilidade em toda configuração futura de fog.

## Combate e drops

Testes existentes de combate e loot aprovados. Adicionado teste integrado: resolução sem alterar HP, confirmação 8 → 0, repetição sem novo dano, geração de espólio, ocultação antes da revelação, revelação e distribuição com retries sem itens ou eventos duplicados.

O fluxo atual exige ações do Mestre para gerar, revisar, revelar e distribuir. Não existe distribuição automática apenas por o monstro morrer. Esta foi uma verificação rápida e automatizada, não certificação de todas as regras de combate, itens ou criaturas.

## Validações

- Backend: 88 testes aprovados com unittest discover.
- Frontend: 18 testes aprovados (DiceTray + notas).
- TypeScript: npx --no-install tsc --noEmit aprovado.
- Vite: npm run build aprovado; primeira tentativa bloqueada pelo sandbox e repetida com autorização.
- Avisos existentes: Starlette/httpx obsoleto, chunk Three.js acima de 500 kB e conversão LF/CRLF.
- Navegador em viewport 390×844: posição de retrato/nível, número maior que 2× HP, notas antes de vida, botão ausente para jogador, edição GM e reabertura com XP salvo.
- Teste integrado novo inicialmente usou request_id curto; fixture corrigida para o contrato existente, sem alterar combate.

## Arquivos

- backend/app/character_play.py
- backend/test_character_progression.py (novo)
- backend/test_combat_loot_circuit.py (novo)
- frontend/src/components/CharacterLevel.tsx (novo)
- frontend/src/components/CharacterLevel.css (novo)
- frontend/src/components/CharacterNotes.tsx
- frontend/src/components/CharacterNotes.css
- frontend/src/pages/SessionWorkspace.tsx
- frontend/src/pages/PlayableCharacterSheet.tsx
- frontend/tests/character-notes.test.cjs
- Este relatório.

Snapshot anterior em .assistant-runtime/checkpoints/sheet-header-2026-08-28/before. Worktree misto preservado; sem commit ou push.
