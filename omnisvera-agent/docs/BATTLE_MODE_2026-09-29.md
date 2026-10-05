# Exploração ↔ Combate — primeiro corte

## Uso

1. Abra a Mesa e seu mapa de exploração.
2. No painel do Mestre, abra Combate. Escolha um mapa já disponibilizado aos jogadores.
3. Preencha iniciativas somente dos participantes. As criaturas/aliados precisam ter pins preparados; os personagens recebem um pin temporário se necessário.
4. Inicie. Os selecionados são posicionados na arena e ficam visíveis. Os outros pins não aparecem na superfície de batalha. A névoa e os demais habitantes ocultos não são revelados.
5. No turno indicado, selecione alvo e ataque. A linha tracejada indica intenção, não acerto. Confirme a prévia para aplicar dano, depois conclua e passe o turno.
6. Encerre. Mapa, posições e visibilidade anteriores são restaurados. Vida, recursos e consequências não são revertidos. Pins temporários de personagens são removidos, sem apagar fichas.

## Garantias e limites

- Transporte e retorno dos pins são transacionais, junto ao estado do encontro.
- Mapas privados são recusados; a preparação informa explicitamente que os participantes serão expostos aos jogadores.
- Backend confere turno, alvo participante e ação de ataque já confirmada. Confirmações repetidas não duplicam dano. Multiataques configurados continuam agrupados na mesma resolução.
- Alteração de composição durante a arena exige encerrar e preparar novamente; reordenação dos mesmos participantes continua disponível.
- Jogadores não podem descansar/restaurar recursos pelo endpoint da ficha durante a batalha; demais alterações de ficha ficam restritas ao próprio turno. Mestre mantém ferramentas de adjudicação.
- Esta versão não formaliza a economia de **todas** as habilidades adaptadas. Usos manuais de poderes, reações, distâncias e duração ainda exigem adjudicação; não foram inventadas regras.
- Linha de alvo é local ao cliente que seleciona. Não há transmissão da intenção para todos os aparelhos nem alerta sonoro nesta etapa.
- Combates antigos sem `battle_mode` preservam o comportamento anterior. O novo início pela UI ativa o modo batalha.
- A sinalização automática de turno é visual. Não houve redesign das fichas nem das barras de vida.

## Validação

- Backend: 205 testes PASS; frontend: 83 testes PASS; TypeScript PASS; build isolado PASS; diff check PASS. Aviso de chunks grandes permanece.
- Testes novos cobrem transporte/retorno, conservação de dano, rejeição de mapa privado, segunda ação e ataque fora do turno, além das coordenadas do tracejado.
- Navegador real, somente na cópia temporária: Mestre mudou Earthropo S5 → Dungeon Part 1, iniciou Aranha/Vezemir, selecionou alvo e passou turno. Jogador entrou automaticamente, viu a aranha e o tracejado, resolveu ataque 13+2 contra CA14, confirmou dano7 (PV13→6) e passou turno. Depois da confirmação, atacar deixou de estar disponível.
- Evidência visual local: `.autonomy/runtime/battle-target-player.png`.
- Produção, Vault e fichas reais não foram usados para ensaios de escrita. O build servido pela campanha não foi substituído. Instância descartável: `http://127.0.0.1:8893/`.
- Pendente: ensaio com Mestre e jogadores em redes diferentes; revisão mobile; publicação coordenada de backend/frontend.

## Arquivos deste corte

Backend: `app/battle_mode.py`, `app/combat.py`, `app/combat_effects.py`, `app/character_play.py`, `app/session_workspace.py`, `app/main.py`, `test_battle_mode.py`.

Frontend: `src/App.tsx`, `src/api.ts`, `src/pages/SessionWorkspace.tsx`, `src/components/CombatEncounterPanel.tsx`, `src/components/MonsterAttackPanel.tsx`, `src/components/AttackTargetLine.tsx`, `src/styles.css`, `tests/combat-controls.test.cjs`.

Alterações anteriores nesses arquivos foram preservadas. Nenhum commit, push ou merge.
