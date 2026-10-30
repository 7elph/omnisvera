# Encerramento de efeitos e header — 10/10/2026

## Entrega

- Encerrar combate desativa efeitos com duração em rodadas, além das vinhas e da Guarda já tratadas. Efeitos de tempo ficcional, de cena, manuais e até descansar não são apagados apenas por sair do combate.
- Encerrar sessão desativa efeitos de rodadas, cena, próximo ataque, tempo ficcional e Guarda. Transformações manuais e efeitos até descansar permanecem; pausar preserva efeitos e turno.
- A limpeza ocorre na mesma transação do encerramento. Se ainda houver combate, restaura mapa/pins pela infraestrutura existente, sem curar ou recarregar recursos. Histórico de efeitos permanece no banco e auditoria técnica é privada do Mestre.
- Encerrar novamente uma sessão antiga não limpa efeitos de outra sessão ativa ou de outro encontro.
- O header usa uma faixa horizontal de ícones. A regra específica evita o `display: grid` herdado dos spans do seletor; não há quebra vertical e faixas maiores podem rolar horizontalmente.

## Arquivos desta etapa

- `backend/app/combat_effects.py`: encerramento de efeitos de rodadas e limpeza transacional da sessão.
- `backend/app/scene_play.py`: integrar limpeza ao status `completed`.
- `backend/test_effect_lifecycle.py`: nove regressões, incluindo pausa, repetição, isolamento entre sessões, preservação de PV/recursos/pins e rollback.
- `frontend/src/styles.css`: faixa horizontal no header.
- `frontend/tests/active-effect-header-visual.cjs`: renderizador real do header e componente de ícones com CSS completo.
- `docs/EFFECT_LIFECYCLE_2026-10-10.md`: este relatório.

As outras alterações já existentes no worktree foram preservadas. Não houve staging, commit ou push nesta etapa.

## Validação executada

- `.\.venv-observer\Scripts\python.exe -m unittest discover -s backend -p 'test_*.py'`: **452 testes, OK** (153,119 s na última execução).
- `node --test tests/*.test.cjs` em `frontend`: **206 testes, zero falhas**.
- `npx --no-install tsc --noEmit` em `frontend`: **exit 0**.
- `npm run build` em `frontend`: **exit 0**.
- `node tests/active-effect-header-visual.cjs` com Playwright/Edge: **celular 390×844 e desktop 1440×900 passaram**; três imagens carregadas na mesma linha, remoção da faixa após expiração e sem overflow da página.
- Smoke HTTP em cópia temporária de SQLite, servidor `127.0.0.1:8871` e acessos de teste: limpeza do estado legado da Sessão 7; projeções sem ícones para Vezemir, Raziel e Morthak; iniciar/aplicar/encerrar combate; persistência ao reler; Sessão 6 e estados dos personagens inalterados. Servidor temporário encerrado ao terminar.
- HTTP do servidor operacional `8787`: HTML e CSS reconstruído retornaram **200**, com a regra horizontal presente.
- `git diff --check` nos arquivos existentes editados: sem erros de whitespace.

Avisos existentes: ResourceWarnings de conexões SQLite nos testes e chunks Vite maiores que 500 kB; não impediram os checks. Testes locais não comprovam uma nova mesa multirrede.

## Estado salvo corrigido

Confirmado no banco operacional: Sessão 7 `completed`, encontro inativo, três efeitos ativos em Vezemir: Velocidade, Força Arcana e Escuridão.

Após validar em cópia, foi aplicado o helper nativo de encerramento em transação, conferindo os IDs e o contexto antes de escrever. Somente os três efeitos foram desativados; versão dos efeitos incrementada e auditoria privada registrada. A sessão, estados dos personagens e pins foram comparados integralmente antes/depois e permaneceram idênticos. Nova leitura confirmou **zero efeitos ativos em Vezemir**.

Backup SQLite consistente anterior à correção, fora do repositório:
`C:\Users\delib\AppData\Local\Temp\omnisvera-before-effect-cleanup-nguuvqg7\companion.sqlite3`.

## Ativação pendente

O servidor operacional não foi interrompido. O CSS novo já é servido e pode ser recebido com uma recarga da página. A regra automática dos próximos encerramentos requer reiniciar o backend para importar o código novo; foi solicitada autorização, ainda não recebida nesta etapa.

Após autorização, usar o inicializador existente preservando banco e acessos (`.\start_backend.ps1 -Port 8787`), sem rebuild do índice e sem nova geração de tokens. Não abrir um segundo processo sobre a porta ocupada.
