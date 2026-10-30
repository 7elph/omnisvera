# Especializações, Mapas e cola de NPCs — 12/10/2026

## Uso

- **Mestre → NPCs do Mestre**, ou a aba **NPCs**: consulta do diretório nativo,
  fichas reservadas (incluindo Dorn e Varkh) e pins de criaturas de todos os mapas.
- Buscar NPCs do diretório e buscar fichas/pins têm campos identificados separados.
  Atualização é explícita, sem polling adicional do catálogo inteiro.
- Abrir um NPC mostra descrição, estado, relações, memórias, encontros e notas do
  Mestre. **Voltar para a lista de NPCs** retorna à consulta. Fichas reservadas têm
  **Voltar para NPCs**. Há também retorno à Mesa e acesso a Mapas.
- Pins usam a ficha modal existente. **Abrir mapa deste NPC** usa a troca nativa
  do mapa; fica bloqueado durante combate. Pins de outros mapas são consultados
  sem editar PV ou usar invocações fora da arena atual.
- **NPCs → Criar, editar ou revelar pins no mapa atual** mantém os controles
  existentes, recolhidos para não encobrir a consulta.
- **Mapas → Locais · criar e pinar rapidamente**: a ferramenta foi movida,
  não duplicada. O seletor rápido de mapa ativo da Mesa foi preservado.
- Especializações são filtradas no backend por classe e reserva de personagem.
  Vezemir: Guerreiro de Arma, Bárbaro e Paladino (requisitos continuam validados).
  Necromante aparece apenas para Morthak. Nenhuma escolha foi aplicada nesta entrega.

## Implementação e privacidade

Reutiliza `/npcs`, fichas persistidas e `session_workspace_tokens`/`sheet_json`.
Novo GET exclusivo do Mestre `/gm/workspace/npc-tokens` lista pins existentes,
sem copiar, revelar ou reposicionar. `/gm/companions` identifica fichas GM também
quando elas não constam dos acessos ativos dos jogadores. Não há novo banco,
subsistema de NPCs, canal realtime ou alteração de regras de combate.
O diretório embutido oferece retorno explícito, controles no padrão da UI,
coluna única e proteção contra respostas tardias de detalhes após seleção/saída.

## Arquivos desta alteração

- `backend/app/main.py`
- `backend/test_npc_reference.py`
- `frontend/src/api.ts`
- `frontend/src/pages/SessionWorkspace.tsx`
- `frontend/src/pages/NpcDirectory.tsx`
- `frontend/src/components/MasterNpcLibrary.tsx`
- `frontend/src/components/CompanionAllySheet.tsx`
- `frontend/src/styles.css`
- `frontend/tests/npc-reference.test.cjs`
- `frontend/tests/npc-reference-smoke.cjs`
- Este documento.

Outros diffs preexistentes foram preservados; o diff desses arquivos também
contém trabalho anterior. Nenhum staging, commit ou push nesta entrega.

## Validação

- Backend: 553 testes PASS (`unittest discover -s backend -p test_*.py`).
- Frontend: 229 testes PASS (`node --test tests/*.test.cjs`).
- `npx --no-install tsc --noEmit`: PASS.
- `npm run build`: PASS; aviso não bloqueante de chunks acima de 500 kB.
- `git diff --check` nos arquivos alterados: PASS.
- Playwright/Edge no backend isolado 8871: separação da classe, abertura pelo
  botão do Mestre, diretório, fichas reservadas, pins, retorno, consulta sem mudar
  visibilidade/posição e Locais restrito a Mapas. Desktop 1440 e mobile 390:
  lista e detalhe sem overflow horizontal; capturas inspecionadas.
  O último NPC da lista também foi aberto com sucesso nas duas larguras,
  verificando acesso por rolagem do painel. Servidor isolado encerrado ao final.
- Fixture de mídia incompleta: erros de imagens ausentes não certificam a mídia
  operacional. Não houve ensaio de mesa simultânea em redes diferentes.

## Ativação

Backup íntegro em
`C:/Users/delib/AppData/Local/Temp/omnisvera-before-npc-reference-e7bb588b6e0545e08dea6b58cd5cbe13`.
Backend reiniciado pelo lançador oficial (PID 14080), Tailscale preservado.
Comparação confirmou fichas, inventários, notas, cenas, sessões, combate e
credenciais preservados. Health e domínio público: HTTP 200.
GM runtime: 12 pins de NPCs, fichas GM `dorn7,varkh`, opções de Vezemir somente
Guerreiro de Arma/Bárbaro/Paladino. Pelo domínio público, Vezemir, Morthak e
Raziel mantêm acesso owner e nível 5. Frontend servido: `index-CkG_H6CO.js`.
