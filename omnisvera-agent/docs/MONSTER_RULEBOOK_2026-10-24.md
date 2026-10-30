# Bestiário: texto integral e regras estruturadas

`monster_rules.compile_monster_rules` adapta os **255 registros OD2** existentes.
Não substitui o catálogo, fichas ou motor de combate. A rota existente
`GET /gm/compendium/monsters/{id}/actions` acrescenta `rulebook`, somente Mestre.

- `source_record`: cópia integral de todos os campos, inclusive futuros.
- `source`, `revision`: edição, URL, licença das regras e SHA-256 do registro.
- `rules`: ataques e habilidades com ID, texto completo, ponteiro de origem,
  cláusulas com offsets, categorias e parâmetros. Nenhuma descrição é truncada.
- `execution`: distingue ataque nativo de regra assistida; dados extraídos
  não certificam aplicação de imunidade, regeneração ou outro efeito.
- Movimento reutiliza o parser atual; não inventa velocidades.
- `art` separa atribuição/licença da imagem e das regras. Vínculo externo não
  comprova arquivo, upload do Mestre ou retrato exclusivo. Só Goblin foi
  confirmado pelo Mestre como upload; o dragão do Vault é referência.

O compêndio apresenta cards recolhidos com parâmetros e texto integral sob
demanda. Não anuncia passivas como automaticamente ligadas. Seleção de outra
criatura limpa a anterior; respostas atrasadas continuam descartadas.

## Segurança do executor existente

`monster_actions` só sugere dano quando o dado está explicitamente ligado a
dano. Dados de sono, imagens, chance e duração não viram dano. O adaptador
de baforadas detalha 15 habilidades de 14 criaturas, sem omitir Quimera ou
Sacrifício do Drakold. Área, frequência e efeitos especiais ainda exigem vínculo
com execução validada; `specification_complete` não significa executável.

`spell_engine` agora usa `combat_effects.change_hp`, inclusive quando o alvo é
o pin de um personagem: PV temporário, ficha, pin e regras nativas de PV deixam
de ser desviados por SQL próprio. Seleção duplicada ficha/pin é rejeitada;
falha em qualquer alvo reverte a transação. Não há novo turno ou WebSocket.

## Limites

O texto foi preservado e organizado; **não está tudo automatizado**. Imunidades,
regenerações, condições e conjuração sem repertório exigem adaptadores e testes.
O executor genérico ainda precisa de recibo idempotente e validação completa de
geometria/custos/recarga antes de habilitação em massa. O parser genérico de
magias ainda não resolve toda progressão por nível. Nenhuma ficha real foi
reposta ou usada para atacar durante este corte.

Próximo corte: vincular as baforadas completas ao grid, frequência/descanso e
comando idempotente nativo; depois passivas por família de efeito.

## Validação e ativação

- Backend completo: 1.338 testes, OK, 1 ignorado. Avisos de conexões SQLite
  em fixtures antigas continuam aparecendo; não são certificação de estabilidade.
- Frontend: 409 testes PASS; 3 testes focais de renderização repetidos após
  o ajuste visual; TypeScript e build PASS. Vite ainda avisa sobre bundles grandes.
- Ensaio HTTP nativo com os quatro atores: 89 PASS, 2 EXPECTED_BLOCK, 0 FAIL.
  Evidência: TEMP `omnisvera-sheet-test-de6xksfy`.
- Repetição focal: TEMP `omnisvera-sheet-test-69ugy6jh`, UI `oct24` PASS,
  incluindo os novos cards em 1440/390 px e sete capturas revisadas.
  O ensaio foi corrigido para esperar o desbloqueio após sincronização; a
  autenticação existente do Mestre nega jogadores com 401. Dorn é controlado
  pelo Mestre na fixture; Raziel, Vezemir, Morthak e Varkh são perfis de jogador.
- Aceitação visual explícita: `codex-visual-review.json` nesse TEMP. O agregador
  antigo de `oct24` deixa `action_coverage` vazio; esse campo não foi preenchido
  artificialmente nem usado para certificar toda ficha.
- Backend ativado com backup SQLite: 21 tabelas protegidas comparadas, fichas
  e tokens preservados; somente timestamps dos mapas oficiais mudaram no startup.
  Recibo privado: `.autonomy/runtime/monster-rules-activation-result.txt`.
- Verificação após ativar: página pública 200, referências aos assets do build
  atual, fichas próprias de Vezemir/Raziel/Morthak via HTTPS 200 e OpenCode
  autenticado saudável. 147 vínculos de arte apontam para 118 arquivos locais
  distintos, com reutilizações; não são 147 uploads nem retratos exclusivos.

Somente loopback/emulação: não prova celular físico ou mesa em redes distintas.
Arquivos: `monster_rules.py`, `monster_actions.py`, `monster_action_specs.py`,
`spell_engine.py`, rota de ações em `main.py`; `MonsterRules.tsx`,
`MonsterActionMap.tsx`, DTO em `api.ts` e CSS; respectivos testes e este documento.
Sem staging, commit ou push; preservado o restante do checkout misto.
