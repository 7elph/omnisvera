# Cenas — biblioteca visual de preparações

O administrativo abre numa galeria dos rascunhos e cenas existentes, com capa,
local, estado, sessão, elenco e contagem de elementos. Busca e filtros são locais.
Não há novo armazenamento, catálogo ou formato de mapa. As seis preparações de
sexta aparecem a partir dos registros já importados, sem IDs fixos no frontend.

Selecionar um card abre o visualizador privado. Imagens, abertura, objetivo,
notas, personagens, NPCs, criaturas, elementos e pins têm cards inspecionáveis.
O diálogo mostra imagem e descrição completas; Escape fecha e restaura o foco.
As imagens dos participantes usam ficha/biblioteca ou seu pin vinculado, aceitando
os vínculos legados `monster:...` e `map-token:...`. Sem arte, há ícone substituto.

A prévia do mapa reutiliza a imagem, grid lógico, posições e fog atuais. Grid,
fog e pins são camadas, não coordenadas novas. Zoom fica limitado ao viewport;
clique num pin só inspeciona. Para mover, pintar fog ou lutar, usar Mapas/Mesa.
O mapa ativo não muda quando se abre uma preparação. Resposta atrasada ou mapa
de fallback não substituem o mapa da cena escolhida. Falha de leitura tem retry.

“Conteúdo público” filtra informações reservadas e não apresenta rascunho como
publicado. É uma projeção conservadora, não login de jogador nem prova de acesso
externo. Notas privadas e ficha interna dos pins não entram nessa projeção.
O backend continua sendo a autoridade de permissões; a galeria só monta no
administrativo do Mestre. Editar, revelar e publicar permanecem ferramentas
explícitas, recolhidas; inspecionar um card não dispara esses comandos.
O editor mantém uma opção explícita de disponibilidade da cena. Bloco privado
não se torna público apenas porque recebeu um card ou foi selecionado.

Cenas deixa de montar o SessionWorkspace vivo ao lado da preparação. Os controles
nativos continuam em Mapas/Mesa e o editor antigo segue acessível em “Editar
preparação e ferramentas”. Oficina e laboratório existentes são preservados;
nenhum provedor de IA ou worker é iniciado ao abrir a galeria. Novos blocos do
administrativo nascem privados. Nova sessão é uma ação separada.

## Escopo e validação

Sem mudanças no backend, banco operacional, mídias, canon, fichas ou regras.
Não altera nem aprova automaticamente checklists de preparação ou propostas.
Testes de projeção, interação e concorrência usam fixtures em memória, sem
credenciais da mesa. O build e as suítes são verificados separadamente; resultados
de API/unidade não certificam renderização em celular físico ou mesa multirrede.

## Resultado deste corte

- Frontend: **383/383**, execução sequencial. Inclui 17 casos de projeção,
  privacidade, interação, retry, descarte de resposta atrasada, unmount e
  renderização estática do grid/pins. O ensaio começou RED antes da implementação.
- `npx --no-install tsc --noEmit`: PASS.
- `npm run build -- --outDir ../.autonomy/runtime/scene-gallery-dist-20261022`:
  PASS (15,76 s). Aviso preexistente de chunks acima de 500 kB permanece.
- Backend completo executado: 1232 testes, 25 erros de ambiente e 2 skips.
  Erros: lock em LOCALAPPDATA bloqueado pelo sandbox e dependência MCP ausente
  na venv do backend. Os seis módulos envolvidos foram reexecutados na
  `.venv-observer` já instalada, com permissão para o lock: **115/115 PASS**.
  Não houve instalação, remoção de lock ou nova execução integral limpa;
  não apresentar o primeiro resultado como 1232 PASS.
- `git diff --check` dos arquivos deste corte: PASS.
- Build ativado sem restart, preservando chunks antigos e trocando o índice
  somente depois da cópia/conferência dos novos arquivos. Backup do índice:
  `.autonomy/runtime/scene-gallery-publish-6f68f2a3c07f4f41984c535c408673ac/previous-index.html`.
- HTTP local: índice e assets `index-ZPwfNbF4.js` / `index-DjeBv-Pn.css` retornam
  200; hashes conferem com o build. HTTPS público existente: 200, mesmo índice.
  A leitura HTTPS precisou da permissão de execução fora do sandbox; não se
  alteraram túnel, certificados, tokens ou serviços.
- Sem navegador iniciado: a margem medida foi 400 MB, abaixo da admissão dos
  ensaios visuais. **Mobile físico/aceitação visual e mesa multirrede:
  INCONCLUSIVE**. A renderização estática não aprova o checklist visual das cenas.

## Arquivos

- `frontend/src/components/ScenePreparationGallery.tsx` e `scenePreparation.css`:
  galeria, prévia, diálogo e layout responsivo.
- `frontend/src/scenePreparation.ts`: projeção de dados, filtros e visibilidade.
- `frontend/src/pages/ScenePanel.tsx` e `frontend/src/App.tsx`: integração,
  leitura do mapa selecionado e preservação das ferramentas nativas.
- `frontend/tests/scene-preparation.test.cjs`, `campaign-memory.test.cjs`,
  `new-session.test.cjs`, `scene-workshop.test.cjs`: cobertura e contratos atuais.
- Este documento e `docs/CURRENT_COMPANION_CODE.md`.

Helpers e logs locais em `.autonomy/runtime/` são privados/ignorados. Nenhuma
alteração anterior do worktree foi revertida. Sem staging, commit ou push.
