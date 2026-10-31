# Itens: efeitos especiais — 31/10/2026

## Implementado neste corte

- **Madu:** dano 1d8, mantendo o +1 de CA equipado e crítico 19–20/x2.
- **Armas de tipos mistos:** escolha explícita de corte, impacto ou perfuração na confirmação do alvo, limitada aos tipos cadastrados da arma. O tipo integra o perfil de dano, o registro e a identidade do retry. Nenhum tipo é escolhido silenciosamente.
- **Rede:** item concreto de 20 PO; ataque de toque adjacente contra 10 + modificador de DES, sem dano de PV. O acerto cria Constrito no armazenamento de efeitos existente: −2 em ataques, JP, iniciativa e testes; retira o bônus positivo de DES da CA, respeitando o teto da armadura. Uma mesma rede não pode prender dois alvos ao mesmo tempo. Libertação pelo controle de efeitos do Mestre; não foi inventado teste de escape. Não permite converter esse ataque sem dano em dano por reforço de sangue.
- **Zarabatana:** dardo comum próprio, pacote de 20 por 10 PO, dano 1d6; alcance 15/30 m e crítico x3. Confirmação consome um dardo pelo mecanismo de munição existente, sem consumir virotes de besta. Dardos especiais continuam sem aplicação automática até existir regra completa.
- **Garrote:** acerto adjacente, sem dano inicial; requer vítima Pequena/Média, posição lógica e JP cadastrada. No início do turno da vítima, JP de DES antes de 1d4; escapar evita esse dano. Impede componentes verbais enquanto preso. Guardar a arma, morrer ou se afastar encerra o aperto, inclusive se o percurso sair e voltar à adjacência. O relógio, as condições e o ledger são nativos; repetição do comando não repete JP/dano.
- **Escudo torre:** zero bônus fixo de CA; direção protegida declarada na confirmação do alvo. Cada acerto elegível rola 25% de bloqueio uma única vez. Bloqueio também impede efeitos por acerto. O 20 natural de jogador permanece inevitável. Direção não é inferida de uma orientação inexistente no mapa.
- **Vibranium:** +3 CA, teto de DES +3; arremesso provisório da campanha de 1d6 + FOR e 9 m. Usa o seletor de arma do ataque à distância. Acerto retorna; erro retira o exemplar equipado e cria pin de local com espólio recuperável pelo Mestre. A queda é provisoriamente na célula do alvo. Recuperação preserva referência, ferrugem e cargas e não equipa automaticamente. Protetor recebe um segundo arremesso contra outro alvo no mesmo turno, sem gastar outro ataque normal; erro no primeiro impede o segundo. Um arremesso por confirmação permite escolher cada alvo e preserva ataques extras de outras fontes.

Associação, pins, espólio, permissões, resolução, confirmação, orçamento de ação, ledger e realtime usam os sistemas atuais. Mapas privados e seus espólios continuam privados. Os estoques e as fichas operacionais não são preparados pelo ensaio.

## Fontes e limites

- Livro Básico Aprimorado de Old Dragon 1: p.60 (Rede, peso, preço e efeitos), pp.72–73 (CA de toque). A implementação é independente, com fatos estruturados e resumo próprio.
- [Expansão de Itens, de Caio Mouriz](https://pt.scribd.com/document/655216129/Expansao-de-Itens-Old-Dragon), T02-01/T02-02; atribuição CC-BY-SA 4.0 preservada nos registros. Nenhum código externo reutilizado.
- O ataque da Rede exige DES cadastrada no alvo; não presume DES 10 para monstros sem esse dado. Não implementa regras adicionais de tamanho, imobilização, incorporeidade ou escape ausentes da descrição consultada.
- A Rede usa o tempo/descanso de efeitos existente; sua retirada manual não destrói o item. Recuperação física e transferência de uma rede presa continuam sob controle do Mestre.
- Alcance máximo da Zarabatana é validado no grid. O campo de alcance curto é preservado; este corte não cria outra tabela de penalidades de longo alcance.
- JP do Garrote no início do turno, declaração de lado do escudo torre e dano/alcance provisórios do Vibranium foram aprovados pelo Mestre neste chat. FOR ausente impede o arremesso; não deve impedir a leitura da ficha.
- Espólio de queda usa a distribuição existente. Exemplares com cargas/condições diferentes não são fundidos silenciosamente; a recuperação precisa de um inventário sem exemplar incompatível. Não foi definido novo custo de ação para recolher o item.
- O bônus do arremesso usa a ficha e os modificadores aplicáveis ao escudo, sem herdar contribuição exclusiva da outra arma do seletor. O teste de regressão reproduziu 15 em vez de 8 antes da correção e passou depois.

## Regras ainda pendentes

- Vibranium: ricochetes em paredes/superfícies dependem da futura geometria autoritativa; este corte cobre o segundo alvo do Protetor. Fora de iniciativa, arremessos continuam ações comuns sem contador de turno.
- Garrote: dano furtivo específico de classe e exceções anatômicas/respiratórias não foram inventados. A cobertura deste corte é para portadores com inventário de personagem e vítimas normais Pequenas/Médias.
- Bagh Naja: significado de 1d6/1d4 não definido na tabela consultada.
- Oito dardos especiais: faltam JP e parâmetros específicos dos efeitos. A duração de 1d4 turnos da expansão não foi convertida silenciosamente em rodadas.
- Arte: alguns itens ainda usam imagem genérica; Garrote, Vibranium e Zarabatana precisam de artes próprias e a arte associada ao Madu merece revisão. Não foi certificada a mídia de todo o catálogo.

## Validação

- Backend: **1.807 casos, zero falhas/erros, 1.806 aprovados e 1 ignorado**. O caso ignorado exige criar symlinks, privilégio indisponível no Windows atual. Os 27 testes específicos deste corte estão incluídos nesse total.
- Frontend: **495 aprovados**; TypeScript e build passaram. Build validado inicialmente em TEMP; o runner rejeita `OMNISVERA_FRONTEND_DIST` fora de TEMP.
- Ensaio nativo final: `TEMP/omni-item-specials-v7`, quatro atores e `ui:true`. Quatro ataques básicos por API passaram; `item-families-smoke.cjs` e `item-specials-smoke.cjs` passaram. Sete capturas inspecionadas explicitamente, incluindo 390 px para jogador e 1440 px para Mestre. Estoque exibido atualiza após compra; outro cliente recebeu o Garrote sem reload manual.
- Cobertura adicional: JP antes do dano, tick letal e passagem de turno, guardar/afastar/morrer, direção explícita, bloqueio/retry/20 natural, retorno/queda/recuperação sem clone, ferrugem/cargas, alcance e compatibilidade com escudo legado sem slot.
- Runtime: backend encontrado sem listener local e restabelecido em processo oculto independente do terminal. Backup em `C:/Users/delib/OmnisveraBackups/item-specials-20261031-053348`. Não foi necessário encerrar backend ativo, OpenCode ou Tailscale.
- Imediatamente após a reativação, hashes das 15 tabelas protegidas e dos arquivos de tokens/configuração coincidiram. As projeções das quatro fichas também coincidiram com o início do trabalho. Health autenticado, quatro fichas locais, catálogo mecânico e separação Mestre/Jogador passaram. Site, bundle novo e fichas autenticadas de Vezemir, Raziel e Morthak responderam 200 pelo endereço público.
- Dois contextos de navegador no mesmo computador e uma consulta ao endereço público não certificam uma mesa real em redes móveis distintas. O catálogo inteiro e todas as ações de todas as fichas não estão certificados por este lote.

## Auditoria posterior à reativação

Depois da comparação inicial aprovada, a auditoria encontrou mudança somente nas coordenadas percentuais dos pins de Dorn e Raziel em Nimalis, às 08:41:28/30 UTC de 31/10. Esses pins são legados sem posição lógica naquela localização; não é correto chamar essa diferença de normalização de células. Fichas, inventários, recursos e demais dados protegidos continuaram iguais na comparação. Em 31/10, o Mestre confirmou neste chat que moveu os dois pins no mapa: a ressalva sobre a origem dos movimentos está encerrada por essa confirmação. A rota legada continua sem autoria no ledger, portanto isso não constitui atribuição automática pelo sistema. Nenhuma restauração de posições foi feita.

## Arquivos deste corte

- Backend: `app/item_specials.py`, `item_grapple.py`, `item_defense.py`, `item_throwing.py` (novos); `character_play.py`, `combat.py`, `combat_effects.py`, `dice_rolls.py`, `dorn_spells.py`, `hemomancy.py`, `item_catalog.py`, `item_families.py`, `loot.py`, `main.py`, `monster_conditions.py`, `schemas.py`, `spatial_grid.py`, `spell_engine.py`.
- Ensaios backend: `test_item_specials.py`, `test_item_specials_advanced.py` (novos); `test_item_families.py`, `test_catalog_readiness.py`, `test_hp_potion_pipeline.py`, `test_fixture_environment.py`, `scripts/cf01_probe.py`, `fixture_media.py`, `run_sheet_test.py`.
- Frontend: `WeaponDamageChoice.tsx`, `AttackDirectionChoice.tsx` (novos); `MonsterAttackPanel.tsx`, `combatActionAvailability.ts`, `SessionWorkspace.tsx`, `api.ts`.
- Ensaios frontend: `item-specials.test.cjs`, `item-specials-smoke.cjs` (novos); `combat-integrity.test.cjs`, `item-families-smoke.cjs`.
- Documentação: este documento e `AI_TEST_TOOLS.md`.

Alterações anteriores em `main.py`, documentação de famílias e arquivos de arquitetura foram preservadas. Na conclusão original da implementação não houve staging, commit ou push. A publicação posterior, solicitada pelo Mestre em 31/10, inclui este corte; consulte `CURRENT_COMPANION_CODE.md`.
