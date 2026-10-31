# Itens por família — primeiro corte executável

## Implementação

O catálogo continua sendo a fonte de identidade/preço. `app/item_families.py`
projeta seus números para o inventário e motores existentes, sem criar outro
sistema de itens. Os metadados são identificados por `family_schema: 1`.
São 71 entradas de armas (incluindo lançadores e casos especiais), 5 de
munição, 13 de armadura e 7 de escudo. Isso não significa 96 itens integralmente
automatizados: as limitações abaixo continuam válidas.

- Armas: dano numérico, modalidades, alcance, margem/multiplicador de crítico.
  Grisalma e exceções existentes continuam nos adaptadores nativos.
- Arcos/bestas: dano da munição compatível; prioridade determinística para
  munição normal antes da improvisada, depois pelo caminho do item.
  Um projétil por disparo, gasto ao confirmar, inclusive em erro.
  Retry da resolução/confirmação não gasta novamente. Sem munição não dispara.
- Bestas: recarga automática aprovada pelo Mestre; exige ainda não ter se
  movido e gasta todo o deslocamento do turno. Usa o orçamento nativo, inclusive
  na iniciativa antiga. Não permite agrupar dois disparos em uma única recarga.
  Fora de combate não há gasto de deslocamento de turno.
- Armaduras/escudos: encaixes corretos, CA, penalidade de deslocamento e teto
  do bônus de Destreza. As restrições explícitas das proteções Samurai usam
  o contexto de classe. Madu mantém o +1 CA expresso em seu cadastro.
- Uma referência defensiva é capturada no primeiro equipar/guardar intencional
  de proteção, para substituir equipamento incorporado à CA antiga sem somar
  duas vezes. Buffs temporários não viram base permanente. Não há migração
  automática de fichas; alterações posteriores de CA pelo Mestre são preservadas.
- Consumíveis: `on_use` estruturado do Vault usa o consumidor transacional
  existente: cura, restauração de recurso, PV temporários, condição simples.
  Mantém validações raciais, um consumível por turno, custos, auditoria e retry.
  Regras desconhecidas/condicionais não são interpretadas a partir da prosa.
- Inventário mantém ícones compactos. Munições mostram os projéteis restantes
  somando pacotes e não oferecem equipar; outros itens mantêm sua quantidade.

Os números básicos foram conferidos no PDF local **Old Dragon Aprimorada**,
pp. 54–55 e 58; as expansões conservam a atribuição já presente no catálogo.
Os campos fonte e `family_gaps` ficam disponíveis no registro/auditoria.
`runtime_support` informa projeção nativa básica; não certifica cada item.

## Limites explícitos

Não foi inventada uma terceira faixa de alcance: a prosa do livro fala em três
faixas, mas sua tabela fornece dois números. O alcance máximo é validado no
grid; penalidades por faixa continuam assistidas enquanto não houver decisão.
Mapas sem grid/posições preservam o comportamento assistido existente.

Continuam pendentes efeitos especiais sem contrato completo (rede, garrote,
dardos especiais, bloqueio direcional do escudo torre, ricochete do Vibranium),
escolha de tipo de dano em armas com tipos alternativos, recuperação física de
armas arremessadas e carga/encumbrância universal. Peso é metadado, não uma
certificação de carga automática. Condições simples por texto não equivalem
à automação de todas as durações mágicas. Não foram geradas novas artes.

Reparo mágico, revenda de objetos usados com condição e as demais famílias
continuam fora deste corte. A economia inteira do mundo não está certificada.

## Ensaios

Regressões em `backend/test_item_families.py` e
`frontend/tests/item-family-inventory.test.cjs`. O lote nativo
`--ui --ui-suite item_families`, com quatro atores, compra pelo jogador,
equipa proteções/arma, usa o consumível, dispara com munição, confirma retry,
recarrega e confere persistência. `inventory_summons` inclui também esse lote
após compra/venda/barganha/serviços e invocação em outro mapa.

Tudo usa `simulation.sqlite3` em TEMP, credenciais sintéticas e processos
pertencentes ao runner. Não autoriza mutações em fichas reais.
Resultados finais:

- Backend: **1.779 testes; zero falhas/erros; 1 ignorado**.
- Frontend: **491 testes; zero falhas**; typecheck e build padrão passaram.
  Uma execução no sandbox falhou por leitura ancestral negada ao esbuild;
  a execução canônica com essa leitura permitida passou.
- API dos quatro atores: PASS em `omni-item-families-v2` e `v3`.
- Compra/venda/barganha/serviços/esqueleto entre mapas: três lotes visuais PASS
  em `omni-item-families-v2`.
- Fluxo novo de famílias: PASS em `omni-item-families-v9`, compra e equipamento
  pela UI do jogador, cura pelo clique no card, disparo/munição por comando
  nativo, confirmação repetida e reload. O lote usa quatro atores na fixture;
  os cliques deste fluxo são de Vezemir. Não certifica individualmente cada ficha.
- Capturas mobile 390 da loja e equipamentos revisadas explicitamente, sem
  sobreposição ou overflow horizontal. Algumas imagens continuam como fallback
  genérico. A ficha NPC de Klhauss tem um espaçamento de título a revisar;
  o layout integral dos NPCs não foi certificado neste corte.
- O ensaio aciona o card, como na UI normal. O controle técnico interno fica
  oculto; tentativas iniciais do driver de clicar nesse botão falharam e foram
  corrigidas. Os FAIL anteriores permanecem nos artefatos.
- Sem prova de mesa real em redes independentes.

Backend ativado após backup SQLite e credenciais. Comparação antes/depois:
quatro fichas, atributos, CA, PV, recursos, moedas e inventário preservados;
hashes das tabelas protegidas e credenciais também preservados. Combate segue
inativo. Nenhuma ação de ensaio foi enviada ao banco operacional.

Publicação local e pública: PASS, incluindo privacidade Mestre/Jogador,
página inicial, bundle e mercado autenticado. O túnel inicialmente estava em
`NoState`, embora o perfil estivesse autenticado e marcado para conectar.
Após autorização, o Windows recusou o restart do serviço por falta de elevação.
A recuperação foi feita iniciando o cliente de usuário `tailscale-ipn.exe`, que
estava ausente; o estado passou a `Running`, com o mesmo domínio. O Funnel 443
foi confirmado para `127.0.0.1:8787`, preservando os demais encaminhamentos.

Fichas públicas somente leitura: Vezemir/Raziel/Morthak com acesso do proprietário
e Dorn com acesso do Mestre: HTTP 200, 95–184 ms nesta medição. OpenCode local
segue protegido com HTTP 401. Não houve mutação de ficha. Não certifica rede
independente ou persistência da conexão após novo reboot. É preciso manter o
cliente Tailscale ativo. Companion e OpenCode não foram fechados; o serviço
Tailscale não chegou a ser reiniciado.

## Arquivos deste corte

- Backend: `app/item_families.py`, `app/item_catalog.py`, `app/item_registry.py`,
  `app/map_commerce.py`, `app/player_inventory.py`, `app/character_play.py`,
  `app/critical_rules.py`, `app/combat.py`, `app/combat_consumables.py`, `app/main.py`.
- Regressões: `backend/test_item_families.py`,
  `backend/test_frontmatter_effect_rules.py`.
- Ensaios: `backend/scripts/item_family_fixture.py`,
  `backend/scripts/run_sheet_test.py`, `backend/scripts/companion_test_mcp.py`,
  `frontend/tests/item-families-smoke.cjs`,
  `frontend/tests/item-family-inventory.test.cjs`,
  `frontend/tests/currency-inventory.test.cjs`.
- UI: `frontend/src/components/InventoryItemIcon.tsx`,
  `frontend/src/pages/SessionWorkspace.tsx`, `frontend/src/api.ts`.
- Documentação: este arquivo e `docs/AI_TEST_TOOLS.md`.

Nenhum commit/staging/push executado por este trabalho. Outra atividade
consolidou o baseline durante o corte (`9710bf82` / `7741b3e6`); esse trabalho
e a extração de rotas encontrados no checkout foram preservados.
