# Consulta de ações e histórico — 12/10/2026

## Como usar

1. **Mestre → Cola de ações**: selecionar Vezemir, Morthak, Raziel, Dorn ou
   outra ficha disponível. Buscar por nome/trecho e filtrar por tipo.
2. Clicar no nome/ícone para abrir o mesmo card de descrição das fichas,
   com imagem e regras cadastradas. Fechar pelo ×, Escape ou fundo.
3. **Atualizar consulta** recarrega a ficha. Recursos/cargas são explicitamente
   uma fotografia do momento da consulta, não um novo contador autoritativo.
4. **Registro da sessão / registro do mapa**: filtrar por personagem,
   escolher **Só ações e rolagens** e buscar nome ou resultado.
5. O nome/ícone no registro abre as regras já associadas à ação.
   **Ver resultado** abre a narrativa e resultado registrado, mesmo quando
   não existe imagem ou card vinculado. **Limpar filtros** restaura a conversa.

Tudo funciona fora e dentro do combate. A consulta não executa ataques,
magias ou consumíveis, não gasta usos e não revela fichas a jogadores.
O Mestre consulta o catálogo; jogadores continuam usando suas próprias fichas
e podem filtrar o registro autorizado que já recebem.

## Escopo real

- Projeção da ficha atual: `session_abilities`, `attacks`, `abilities`, itens
  usáveis e efeitos de equipamento equipado. Evita duplicar magia/ataque.
- Usa `getPlayableCharacter` com leitura já limitada por timeout; uma ficha
  por seleção/atualização, sem carregar todas em paralelo ou criar polling.
  Ao trocar/fechar, respostas antigas não substituem a seleção atual.
- Usa o ledger/realtime existente, sem segundo histórico ou novo endpoint.
  Os filtros operam sobre os registros carregados, não todo o banco.
- Uma ação histórica não vira efeito ativo. Não altera a duração/execução
  de habilidades; regras parciais/bloqueios continuam sinalizados.
- Não consegue inferir ações apenas faladas na mesa ou recuperar registros
  que nunca foram salvos. Elas precisam ser anotadas no registro existente.
- A cola cobre conteúdo da ficha, não uma extração automática de todas as
  magias mencionadas livremente nas notas. Descrições ausentes são indicadas.

## Arquivos

- `frontend/src/actionReference.ts`
- `frontend/src/components/CharacterActionReference.tsx`
- `frontend/src/pages/SessionWorkspace.tsx`
- `frontend/src/styles.css`
- `frontend/tests/action-reference.test.cjs`
- `frontend/tests/action-reference-smoke.cjs`
- `frontend/tests/table-controls.test.cjs` (expectativa do novo painel)
- Este documento.

Alterações anteriores preservadas. Sem staging, commit ou push.

## Validação

- Backend: 553 testes PASS; nenhum código backend foi alterado neste corte.
- Frontend: 234 testes PASS na suíte completa.
- TypeScript e build PASS; aviso não bloqueante de chunks acima de 500 kB.
- Edge/Playwright isolado 8871: consulta Morthak/Vezemir, troca sem manter
  cards do personagem anterior, busca sem acentos, detalhe e fechamento,
  filtro de ações/resultados, limpar filtros e ausência de comandos de jogo.
- Desktop 1440 e mobile 390: catálogo sem overflow; detalhe dentro da tela.
  Capturas inspecionadas. A fixture tem imagens ausentes: não certifica todas
  as imagens reais. Não prova mesa simultânea em redes diferentes.
- Domínio público HTTP 200 confirmou a entrega do novo bundle; não foi
  necessário interromper/reiniciar o backend para alterações só de frontend.
  Bundle final: `index-BJD0osY_.js`. Backend operacional mantido no PID 14080.
