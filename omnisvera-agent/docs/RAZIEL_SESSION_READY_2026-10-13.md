# Raziel — ativação para a mesa (13/10/2026)

## O que está ativo

- Nível 5; Mordida usa 1d6, conforme progressão racial existente.
- PV preservados em 22/22. O nível 3 foi reconhecido como já incluído no ajuste manual, sem rolagem, ganho ou cura. Restam os dados dos níveis 4 e 5.
- Hemomancia reúne os seletores de armas equipadas e poderes de sangue. Adagas de Espectro Fantasma continuam sendo item equipado, não uma conjuração.
- Arma equipada pode receber +1d4 por ponto de sangue, até a reserva disponível. Preview não gasta; confirmação gasta inclusive no erro. Retry não duplica custo/dano/cura. A cura das adagas é limitada aos PV efetivamente drenados.
- Lâminas de Sangue permitem declarar até toda a reserva atual, sem o antigo teto de cinco.
- Forma da Noite: as três formas usam provisoriamente a base aprovada de Morcego (1 PV, CA 14, JP 4, voo 9 m). Ataques e poderes humanoides são bloqueados; ações estruturadas de fala são bloqueadas. Conversa livre não é filtrada.
- PV animais separados dos normais. Ao atingir zero, retorna automaticamente e o dano excedente passa ao corpo normal. Troca de animal não recarrega PV temporários. Imagens das formas ficam no seletor expansível, não no título permanente.

## Uso rápido

1. Atualize a página uma vez; abra a ficha de Raziel.
2. No card Hemomancia, escolha arma equipada ou poder. Para arma equipada, selecione o reforço opcional, alvo e ataque; confirme a resolução.
3. Para transformar, abra o seletor de animal, escolha uma forma e ative. Desativar retorna ao corpo normal; zero PV animal também retorna automaticamente.
4. Não role novamente os PV do nível 3. Os níveis 4 e 5 continuam pendentes para a mesa.

## Validação e publicação

- Backend: 662 testes passaram.
- Frontend: 247 testes passaram. Duas expectativas antigas dos testes foram atualizadas para a reserva de dez e o seletor unificado.
- Typecheck e build passaram. Build mantém aviso de bundles grandes.
- Smoke real de navegador em viewport mobile, conta proprietária e banco descartável: card único, dez pontos de reforço, preview sem débito, confirmação única, seletor fechado sem imagem, ficha animal, bloqueio de poder, dano excedente e reload passaram.
- Backend operacional reiniciado com backup SQLite e credenciais em TEMP. Comparação confirmou preservação de fichas, inventário, tokens, cenas, sessão, combate e grid. Só depois foi reconhecido o PV manual do nível 3 pela rota nativa do Mestre.
- URL externa respondeu 200 para a ficha com acesso de Raziel. Ficha de outro personagem permanece pública sem estado/inventário privados; notas de outro personagem retornam 403.
- A primeira execução do runner MCP completo não iniciou porque 8871 já estava ocupada: resultado INCONCLUSIVE, não sucesso. Nova execução isolada em 8873 passou em 72 cenários, com zero falhas e um bloqueio esperado (Morthak não tem arma equipada para ataque genérico à distância). Passaram também a checagem visual de seis combinações Mestre/proprietário/desktop/mobile e os botões físicos de combate (Toque Sombrio, lâminas, três poderes de sangue, Sangue Defensivo, Caixão, kit consumível de Dorn + ataque), atualização entre clientes locais e reload.
- Nenhum commit/push. Alterações preexistentes do worktree misto foram preservadas.

## Limites

- Corpo Predatório, Técnica de Predador e Marca Rubra aprimorada continuam sem nova regra aprovada; este corte não inventou nem ativou mecânicas para eles.
- Medo, fotossensibilidade, imunidades e cura invertida não receberam automação nova neste corte.
- Perfil animal é provisório; diferenças entre as três formas e atributos ausentes não foram inventados.
- O fixture não certifica toda a mídia; não houve teste de endurance com jogadores reais em redes distintas.
- O servidor descartável registrou imagens indisponíveis em previews de edição sem assets copiados; a aprovação acima certifica comandos e layout, não essa biblioteca de mídia.

## Arquivos deste corte

Backend: `app/night_form.py`, `app/vampire_powers.py`, `app/combat_effects.py`, `app/character_play.py`, `app/combat.py`, `app/main.py`, `app/scene_play.py`, `app/schemas.py`, `app/level_recalculation.py`, `app/level_routes.py`, `app/data/raziel_vampire_powers.json`.

Testes backend: `test_raziel_night_hp.py`, `test_raziel_sheet.py`, `test_spectral_dagger_drain.py`, `test_level_recalculation.py`.

Frontend: `src/components/HemomancyCard.tsx`, `src/components/NightFormSelector.tsx`, `src/pages/SessionWorkspace.tsx`, `src/api.ts`, `src/styles.css`.

Testes frontend: `tests/night-form-selector.test.cjs`, `tests/raziel-vampire-powers.test.cjs`, `tests/raziel-blood-resource.test.cjs`, `tests/combat-simulation-physical-smoke.cjs`, `tests/raziel-ready-smoke.cjs`.

Os arquivos acima podem conter também trabalho preexistente; não foram revertidos ou staged integralmente.
