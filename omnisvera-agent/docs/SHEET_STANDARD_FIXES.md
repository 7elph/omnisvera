# Ajustes das fichas — 2026-10-08

Branch `devin/create-omnisvera-class-standard`, HEAD `8f6444c13cbb55603d9e97699d47b0cbd0ba2a4d`. Worktree já continha mudanças extensas de Companion, Vault e mídia; preservadas. Sem commit, push ou reset.

## Correções

- Lâmina de Sangue não exibe mais o contador compartilhado como contador próprio. A Reserva continua sendo a autoridade de consumo no backend. Nenhuma mudança de custo, limites ou regras.
- Cards de habilidades têm título em linha inteira e controles abaixo, como inventário. A regra se aplica também a títulos longos, não apenas à Forma da Noite.
- Ícones de armas não são copiados para outro ataque por constarem no breakdown de bônus globais. Itens de apoio sem dano continuam visíveis. O bônus não foi alterado; a correção é da lista de fontes visuais. Seleções antigas de arma só podem resolver candidatos compatíveis com o slot; ataques próprios preservam a busca normal.
- Dorn usa cards compartilhados para traços e efeitos. Removidos painéis de apresentação duplicados de Integridade e Componentes: PV, Recursos e Inventário continuam nas seções comuns. Protocolos e seus comandos existentes preservados.

## Arquivos alterados

- `backend/app/character_play.py`
- `backend/test_equipment_updates.py`
- `frontend/src/pages/SessionWorkspace.tsx`
- `frontend/src/styles.css`
- `frontend/src/components/DornConstructDetails.tsx`
- `frontend/tests/sheet-standard.test.cjs`
- `frontend/tests/sheet-standard-visual.cjs`
- `frontend/tests/shared-attack-target.test.cjs`
- `frontend/tests/raziel-vampire-powers.test.cjs`
- Este relatório.

## Verificação

Backend 392/392. Frontend 158/158; expectativas de CSS atualizadas para o layout aprovado com controles abaixo. TypeScript, builds e `git diff --check` passaram; aviso de chunks grandes no build.

QA desktop 1440×900 e mobile 390×844: renderizador real de habilidades extraído do workspace, Lâmina sem contador duplicado, título com largura inteira, controles abaixo, descrição abre/fecha, sem overflow. Fixture hidratada de Dorn: protocolos Vanguarda/Diagnóstico e pendência de PV funcionam contra API simulada; cards de traços sem overflow. Estes checks não representam uma sessão completa multicliente em redes distintas.

Aplicado no Companion atual: frontend compilado e backend reiniciado pelo launcher oficial em janela oculta persistente. Consulta autenticada do Raziel real mostra as adagas equipadas à distância: apenas `ranged` contém o ícone; `melee` não. Não foi alterado o equipamento real para testar o slot inverso, coberto pelo teste backend.
