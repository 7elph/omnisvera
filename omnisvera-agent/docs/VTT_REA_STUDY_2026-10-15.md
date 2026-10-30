# Estudo VTT com REA: mapa e ações configuráveis

## Resultado e fronteira

Estudo estático concluído para recortes de dois projetos abertos. **Nenhum código
externo foi incorporado ao produto.** Não há novo motor, importador, migração de
fichas, regra aprovada automaticamente ou recurso novo ativado por este documento.
O próximo corte recomendado é tornar explícito o contrato das ações existentes,
começando por Relâmpago de Dorn, sem reescrever seu handler.

Base local: branch `devin/create-omnisvera-class-standard`, HEAD
`1a07a84d3f753b277b8b3542baeb27a3df411077`, worktree misto preservado.
O OpenCode trabalha em testes separados; este estudo não altera esses arquivos.

## Fontes e licença

| Referência fixada | Recorte e razão |
| --- | --- |
| [PlanarAlly b17ed248](https://github.com/Kruptein/PlanarAlly/tree/b17ed248c35be73440c2499af57b41f70ddd6306) | Grid/snap, câmera/zoom, auras e comunicação; frontend Vue, não React |
| [dnd5e e90321f0](https://github.com/foundryvtt/dnd5e/tree/e90321f06274d8bd7274c1151b1c732b2bcb7f7d) | Sistema de jogo aberto para Foundry: atividades, consumo, alcance, alvos e ciclo de uso; **não é o core proprietário do Foundry** |

PlanarAlly: [MIT](https://github.com/Kruptein/PlanarAlly/blob/b17ed248c35be73440c2499af57b41f70ddd6306/LICENSE).
dnd5e: [software MIT](https://github.com/foundryvtt/dnd5e/blob/e90321f06274d8bd7274c1151b1c732b2bcb7f7d/LICENSE.txt);
o [README](https://github.com/foundryvtt/dnd5e/blob/e90321f06274d8bd7274c1151b1c732b2bcb7f7d/README.md)
separa software, SRDs e imagens com termos próprios. Reutilização futura exige
conferir o arquivo e dependências e preservar os avisos aplicáveis. Não foram
importados compêndios D&D, imagens, binários ou APIs internas do core Foundry.
As mecânicas D&D não substituem Old Dragon/Omnisvera.

REA `rea-agents@6.5.0`, temporário via npm com `--ignore-scripts`, executou
`analyze-javascript-application`. Nenhum bootstrap dos apps foi executado e suas
dependências não foram instaladas. Relatórios locais no TEMP:

- `omni-vtt-study-92e69f21/rea-planarally.json`: quatro arquivos parseados, zero
  falhas; 340 fontes inventariadas ficaram fora da seleção. Recorte:
  `client/src/core/grid/index.ts`, `game/systems/position/index.ts`,
  `game/systems/auras/index.ts`, `game/api/socket.ts`.
- `omni-vtt-study-92e69f21/rea-dnd5e.json`: seis arquivos parseados, zero falhas.
  Foram baixados somente esses seis módulos, LICENSE e README, não o repositório
  inteiro: `module/data/activity/{base-activity,save-data}.mjs`,
  `module/data/activity/fields/consumption-targets-field.mjs`,
  `module/data/shared/{range-field,target-field}.mjs`,
  `module/documents/activity/mixin.mjs`.

Ambos os grafos semânticos são **parciais e truncados por limites explícitos**;
imports externos não foram resolvidos integralmente. Os 132/100 findings são
observações, não contagens de bugs. A leitura direta complementou o REA, inclusive
`PlanarAlly/client/src/core/{conversions.ts,systems/README.md,socket.ts}`.
Não houve benchmark, teste dos apps externos, execução de Foundry ou prova mobile.

## 1. Mapa: adaptar padrões, preservar a autoridade atual

| Padrão observado | Companion atual / adaptação recomendada |
| --- | --- |
| Conversões mundo ↔ tela isoladas e snap considerando footprint (`core/grid`, `core/conversions`) | `spatialGrid.ts` já projeta célula ↔ percentual e `LogicalGrid.tsx` renderiza. Manter células autoritativas, origem/escala por mapa e conversão percentual legada; não substituir por pixels do PlanarAlly |
| Zoom preserva a âncora (`PositionSystem.updateZoom`) | `SessionWorkspace.changeMapZoom` **já faz isso** por scroll relativo e requestAnimationFrame. Extrair/testar a matemática apenas num corte localizado; não anunciar como função ausente |
| Separação de dados de cena e estado reativo da seleção (`core/systems/README.md`) | Separar câmera/gestos e seleção transitória do snapshot persistido. Não tornar todos os pins/efeitos reativos a cada pointermove; medir renders antes de trocar DOM/SVG por canvas |
| Auras pertencem à entidade e têm conversão de estado de servidor (`AuraSystem`) | Generalizar o overlay existente, não criar outro catálogo de tokens. Separar alcance de seleção, área afetada e efeito persistente: desenhar aura não aplica dano |
| Comunicação agrupada e eventos temporários descritos em ARCHITECTURE | Reutilizar `session_realtime.py`, watcher do ledger e recibos. Não importar socket.io, outro WebSocket ou confiar em posição transmitida sem validação |

Camadas preservadas: **imagem → grid → fog → alcance/área visível → pins**.
O fog limita o que o jogador pode saber, inclusive lista de alvos e metadados;
um overlay não pode revelar pin oculto. O backend revalida tudo na confirmação.
`TargetingOverlay.tsx` hoje desenha elegibilidade Chebyshev/Manhattan e contorno
circular de referência: círculo visual não muda a política provisória do grid.
Alcance de lançamento não é tamanho da área de efeito.

Estados de interação recomendados: `idle → targeting → confirming → submitting
→ resolved`, com cancelamento antes de submitting e falha incerta conservando
o mesmo request_id. Usar `cardActivation.ts`, `gridTargetSelection.ts`,
`TargetConfirmation.tsx` e `confirmGridMove` atuais; não adicionar mais botões.
No mobile, rolagem pertence ao viewport limitado, drag ao pin; pointercancel,
mudança de mapa e resposta antiga não podem concluir outra ação.

Walls/LOS/iluminação permanecem fora deste corte. Futuras paredes serão segmentos
independentes da imagem e do grid, consultados pelo validador nativo.

## 2. Habilidades: definição explícita + componentes reutilizáveis

No dnd5e, `BaseActivityData` separa ativação, consumo, duração, efeitos, alcance,
alvos e usos. `TargetField` distingue template espacial de quem é afetado;
`SaveActivityData` distingue JP, dano e resultado da resistência. O mixin de uso
separa configuração, consumo, concentração, resultado e ações subsequentes.
Esses são padrões úteis; as classes dependem de `foundry.*`, `CONFIG`, `Hooks`,
documentos e interface Foundry. **Não funcionam por copiar/colar no FastAPI/React.**
Não importar sua economia de ações, preparação, slots, CD/atributos ou sequência
de aplicação como regras da campanha. Tampouco importar hooks/scripts arbitrários.

### O que já existe e o que realmente falta

- `action_library.py` já descreve `ref/name/kind/owner/blocks/costs/executable/execute`
  e despacha algumas ações para os motores atuais. Técnicas são descritas mas
  continuam nos handlers próprios; `costs` frequentemente é vazio.
- `spell_engine.py::derive_spell_mechanic` infere JP, primeiro dado e primeiro
  alcance a partir de texto. Isso não é um contrato confiável para todo o catálogo.
- Experimento **sintético, sem banco**: descrição “Dura 1d4 rodadas. Causa 2d6
  pontos de dano.”, alcance “9 metros + 3 metros por nivel”, JPD/metade produziu
  dano `1d4` e alcance `9`. Demonstra o limite do parser, não uma nova regra nem
  prova de que todas as magias cadastradas têm esse defeito.
- As rotas genéricas `/gm/actions/execute` e de compêndio são Mestre-only. Seus
  schemas atuais não carregam request_id; não usá-las como executor universal de
  jogador sem estender autorização/recibo. Os comandos específicos continuam
  sendo a referência, não devem ser substituídos por esse caminho mais permissivo.
- `ActionCard.tsx` é um card genérico legado com dropdown; não é o padrão desejado
  para fichas. Reutilizar o fluxo compacto **card → grid → confirmação → resumo**.

### Contrato aditivo proposto para a biblioteca existente

Não criar outra biblioteca/formato de campanha. Versionar e enriquecer a descrição
de ação atual, mantendo adaptadores para catálogos e handlers já existentes:

| Informação | Contrato necessário |
| --- | --- |
| Identidade/origem | `ref` atual, revisão da definição, fonte/edição/página quando verificadas, decisão de campanha e aprovação; texto extraído é apenas candidato |
| Executor | Binding interno permitido a handler nativo; nunca URL, Python/JS ou caminho SQL escolhido pelo cliente/IA |
| Alvo | self/ally/enemy/corpse conforme ação, contagem mínima/máxima e deduplicação da entidade mesmo com dois pins |
| Alcance/área | Toque em células ou alcance em metros resolvido pelo servidor; área em campo distinto. Fórmulas por nível limitadas a operadores/contextos permitidos, sem eval |
| Custo/recuperação | Recursos atuais `uses.resource_key`, inventário/componentes e orçamento nativo. Recarga por regra aprovada, sem transformar toda habilidade em 1/dia ou recriar preparação |
| Resolução | Blocos tipados de ataque, JP, dano, cura, condição/modificador. Dano compartilhado vs por alvo explícito; dados/resultados guardados no recibo |
| Duração | Unidade e gatilho explícitos: turno do alvo/invocador, rodada, tempo ficcional, fim do combate ou descanso. Não converter turno de exploração em rodada |
| Escopo | Referência a mapa/combate/sessão quando aplicável, separada de duração. Trocar mapa não decide sozinho apagar ou perpetuar um efeito; descanso geral usa a limpeza nativa |
| Disponibilidade | Automático, assistido, passivo, bloqueado por regra ou indisponível por cadastro; `structured`/`executable` isolados não certificam toda a consequência |

Pipeline alvo, dentro da infraestrutura atual:

**definição aprovada → descrição/alcance resolvidos no backend → seleção no grid
→ comando idempotente → revalidação → rolagem/custo/efeito/ledger na mesma
transação → realtime existente → resumo com “Ver resultado”.**

Preview/seleção/cancelamento não rolam nem gastam. Comando carrega identidade da
ação, atores/alvos, escolhas permitidas, request_id e versões/revisão relevantes,
não dano/custo/alcance autoritativos do cliente. Retry encontra o recibo antes de
recalcular com atributos já alterados; intenção diferente com mesmo ID conflita.
Erro em um alvo reverte a operação inteira, salvo regra explicitamente diferente.

Passivas e gatilhos futuros devem reutilizar `combat_effects`/ciclo atual, com
eventos tipados, ordem determinística, deduplicação por evento e limites de
encadeamento. Frenesi, Guarda, invocações e formas permanecem adapters especiais
até existir equivalência comprovada; não tentar encaixar tudo em dano + JP.

## Primeiro corte recomendado, sem reescrever o produto

1. **Piloto: Relâmpago de Dorn.** Descrever pelo contrato enriquecido os valores
   que `dorn_spells.command`/handler atual já calcula: alcance `40 + 10 × nível` m,
   até três alvos únicos, uma JPD por alvo, uma rolagem `min(10, nível)d6`
   compartilhada, metade ao resistir, recurso `dorn_relampago` e ação atual.
   É a exceção aprovada da campanha, não importar a área em linha D&D.
2. Consumir a mesma descrição no preview de alcance/card, retirando duplicações
   desse piloto sem mudar endpoint, custo, dado, turnos ou ledger. Não realizar
   outra rolagem ou cobrar no adaptador: o handler nativo ainda executa uma vez.
3. Comparar contrato e resultado nativo em modo de teste, depois pela UI isolada.
   Validar 1–3 alvos, JP integral/metade, nível diferente, mapa/escala diferentes,
   dois pins da mesma entidade, cancelamento, mudança de mapa/resposta atrasada,
   custo insuficiente, retry simultâneo, rollback, reload e dois clientes locais.
4. Só depois extrair o executor comum **JP + dano + custo**, mantendo adapters.
   Próxima prova: segunda ação simples com regra explícita; depois buffs e
   expiração. Clonagem/Frenesi/Guarda não são o primeiro piloto genérico.
5. IA passa a preencher propostas de campos aprováveis e casos de teste; revisão
   e cobertura precedem habilitação. Catálogo textual não vira centenas de
   habilidades automáticas de uma vez. Raziel continua sem rebalanceamento aqui.

Aceitação do piloto: igualdade de resultado/custo/recibo antes/depois, mesmas
permissões e cards compactos; nenhuma ação do Mestre real usada como QA.
Consultar `AI_TEST_TOOLS.md` e a matriz das três fichas. Fixture isolada,
quatro atores na regressão visual; PASS seletivo não certifica tudo nem redes
diferentes. Nenhum benchmark ou smoke operacional foi executado neste estudo.

## Entrega e checks

Arquivo novo deste estudo: este documento. Relatórios/cópias externas ficaram
no TEMP. Sem alterações no runtime, banco, tokens, regras, Vault ou testes do
OpenCode; sem restart, staging, commit ou push.

Checks do checkout: **838 backend PASS**, **300 frontend PASS**, typecheck e
build PASS, `git diff --check` PASS; 14 referências locais conferidas e nenhuma
linha com espaços finais neste documento. O build manteve os mesmos nomes/hash
dos bundles de entrada já existentes. Avisos de SQLite não fechado e chunks
acima de 500 kB permanecem. São checks do worktree atual (incluindo trabalho
concomitante), não prova de implementação das propostas ou mesa real. O limite
do parser demonstrado acima continua sem patch neste corte documental.
