# Inventário aditivo de ações nativas

`native_action_manifest.py` é uma projeção pura, não outro motor de combate.
Recebe a ficha efetiva já autorizada pelo caller, incluindo habilidades de nível,
especialização e overrides. Não lê banco, não importa `main`, não consome recursos
e não altera fichas. Nunca interpretar `mechanics_status=structured` como prova.

Cada entrada identifica ref, rótulo, origem, binding allowlisted, rota nativa,
disponibilidade local, limites e `certification=not_assessed`. Desconhecidas
continuam assistidas, sem endpoint inventado. Recurso esgotado mantém a entrada
no inventário. Pré-requisitos ausentes/desconhecidos não substituem autorização,
turno, posição, alvo e validações transacionais do handler.

## Quatro fichas

| Família | Delegação existente |
|---|---|
| Ataques, Mísseis, Adaga de Osso | resolve da ficha + confirmação nativa |
| Vezemir: buffs, Frenesi, Provocação | rota de técnicas/effect_command |
| Morthak: invocações, Toque, medo, Clonagem, Morte | técnicas e handlers especializados |
| Raziel: sangue, Mordida, regeneração | técnicas; confirmação preservada quando for ataque |
| Raziel: Forma/Caixão | ações persistidas da ficha, não novo descanso |
| Dorn: magias/protocolos/reparo | effect_command/técnica de Reparo |

Custos são consultados nos recursos efetivos (incluindo aliases legados), não
copiados de JSON antigo. Clonagem e Reparo conferem presença do componente no DTO;
não entregam itens. Toque/Aterrorizar com uso diário esgotado permanecem com
disponibilidade desconhecida porque há alternativa memorizada validada nativamente.
Não atesta automaticamente passivas narrativas, visão, portas, regras pendentes
ou efeitos que não tenham ensaio próprio. Pulseira continua item, não habilidade
artificial: utilizáveis aparecem a partir do inventário efetivo em entradas
`kind=item`, assistidas, sem binding/endpoint novo. `usable`, cargas, regras
`on_use` e os mesmos indícios de exibição da ficha selecionam essas entradas;
isso não interpreta dano, cura ou condições de texto. Equipamento passivo não
vira ação. Quantidade/cargas esgotadas ficam indisponíveis sem desaparecer.

## NPCs/monstros

Adapta `sheet.attacks/abilities` pelo action-map existente, mas usa a própria
função pura `monster_attack_definition` como autoridade final do ataque. Tipos
conhecidos diferentes de `monster` ficam bloqueados; DTO legado sem tipo mantém
compatibilidade. Só ataque com dado e bônus aceitos pelo executor recebe resolve
de token e confirmação nativos. Riders continuam
manuais; dano incompleto bloqueia sem inventar arma. Usáveis/conjurações extraídos
ficam assistidos e não chamam `action_library.execute_action` ou `spell_engine`.
Frequência textual não vira recurso; JP/dados extraídos não provam condições,
duração, área, hooks de PV ou retry seguro.

## Validação e alcance

Testes DTO sem banco cobrem os quatro atores, override desconhecido, owner errado,
recurso esgotado, alternativa memorizada, passiva, bloqueio explícito, arma sem
dano, componente ausente/presente, pureza/allowlist de saída, ataque de NPC com
rider manual, frequência textual e token sem identidade. RED inicial: módulo
ausente; GREEN após implementação. Integração HTTP/UI e ensaios ficam com o
coordenador; este módulo sozinho não migra o executor nem certifica a mesa.

Revisão final reproduziu falsos positivos (`1d6+2d4`, `21d6` e tipos não-criatura)
e os corrigiu por delegação ao validador nativo. Ataques de ficha usam os limites
do `parse_formula` existente. Toque Sombrio expõe confirmação nativa, e estado
ausente nunca declara disponibilidade confirmada. Testes focados finais:
**34/34 PASS** (20 manifest, sete main readonly, sete rotas de auditoria).
