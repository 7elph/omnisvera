# Monstros: escolhas de encontro e ataques sem dano

O Mestre aprovou equipamentos e repertórios padrão editáveis, identificados
como escolhas da campanha. Nenhum monstro/pin salvo ou ficha real foi migrado.

## Configuração

`backend/app/data/monster_encounter_defaults.json` contém 29 equipamentos e
16 repertórios. `monster_encounters.encounter_defaults()` resolve IDs dos
catálogos atuais, preservando o registro SRD original. A API do bestiário
entrega ambos; **Carregar no formulário** usa a configuração de encontro.
Armas e magias continuam editáveis nos campos nativos antes de criar o pin.

Os dados das armas vêm do catálogo OD1 já usado na campanha. O BA e o bônus
fixo de dano permanecem os do monstro OD2: `Arma +6` com machado 2d6 vira
`2d6+6`, sem somar +6 ao BA. Não se trata de equipamento obrigatório da SRD.

A Serpente recebe a variante de encontro **não venenosa**, com Mordida 1d3.
A alternativa venenosa e sua descrição continuam intactas na fonte. O Mestre
pode editar o encontro para usar `1d3 + Veneno` com a habilidade original.

Repertórios arcanos usam Dardos Místicos e Toque Chocante; conjuradores de
nível 5 ou maior também recebem Bola de Fogo. Repertórios divinos usam Dardo
de Brasa. São seleções iniciais da campanha, não a totalidade de magias que
esses conjuradores poderiam conhecer. Nível vem da descrição, não dos DV.
O parser agora reconhece Clérigo e Clérigo Xamã com acentuação.

Os handlers existentes recebem três adaptações literais:

- Toque Chocante: 1d8 + nível.
- Dardos Místicos: 1 dardo no nível 1, +1 a cada dois níveis, máximo 5;
  cada um causa 1d4+1.
- Dardo de Brasa: 1 dardo no nível 1, +1 nos níveis 4/7/10 etc.; cada um
  causa 1d4 + nível, com bônus máximo +5.

Neste modo, todos os dardos vão para um único alvo. Seleções com mais de um
alvo são rejeitadas antes de mutação; não se duplica a quantidade por alvo.
Distribuição de projéteis, cobertura/linha de visão, preparação diária e todos
os efeitos ambientais de Bola de Fogo não foram certificados neste corte.
As magias continuam respeitando o turno/orçamento de ação nativo em combate.

## Cegueira e paralisia

Cuspe da Cobra Cuspidora e Tentáculos do Verme da Carcaça não recebem dados
fictícios de dano. O pipeline nativo resolve acerto, confirmação idempotente,
JP e condição; os PV não mudam por esses ataques. Duração literal:

- Cegueira: JPD evita, 1d6 rodadas.
- Paralisia: JPC evita, 2d4 turnos de exploração, sem converter para rodadas.

Paralisia bloqueia ação e movimento; condições usam o relógio/ledger/realtime
existentes. Cegueira recebe status/duração e o bônus já existente contra alvo
cego. Não foi criada uma regra de alcance ausente para o Cuspe.

## Quatro especiais: contratos próprios

- **Esfera da Aniquilação:** perigo sem PV/iniciativa normal. O Mestre confirma
  contato adjacente no grid; desintegra sem ataque/JP, inclusive contra PV
  temporários, Forma da Noite e sobrevivência de Frenesi. O pin deixa de ser
  corpo reanimável. Não foi criada ficha de combate fictícia para a esfera.
- **Flagelo da Podridão:** regra **provisória da campanha**, aprovada pelo
  Mestre: contato por ataque exige JPC; falha infesta sem acumular/renovar.
  Causa 1d4 no início dos próximos três turnos da vítima. A própria ficha
  permite remover o parasita usando a ação principal, com recibo idempotente.
  Não é transcrição de uma regra SRD ausente. Não converte turnos em rodadas
  globais. Dano vai ao ledger; o status informa quantos turnos faltam.
- **Ferrugem:** contato seleciona item equipado da instância de inventário.
  Material, magia e os componentes separados de encantamento são confirmados
  explicitamente pelo Mestre; não se presume que FOR/BA/classe sejam magia.
  10% por bônus para resistir; falha reduz um ponto. +1 chega a +0 sem destruir;
  novo contato em +0 destrói uma unidade e desequipa. Estado fica na extensão
  `inventory_item_conditions`, não no Vault nem como efeito temporário.
  Ataque corpo a corpo contra Ferrugem também corrói a arma quando o material
  já está identificado; desconhecidos e projéteis geram pendência legível.
  Ataques pendentes não podem confirmar BA/CA anteriores à corrosão.
- **Morcego:** dez pins individuais, vivos e em voo, sobrepostos ao alvo no
  grid aplicam −2 nos testes. Movimento/morte/menos de dez removem o estado
  na mesma transação. Raziel transformado não conta como pin do bestiário.
  Sobreposição horizontal é a interpretação espacial explícita deste corte:
  altura não existe. Afastar os morcegos não tem JP/sucesso definidos na fonte;
  a arbitragem dessa exceção permanece do Mestre. Nenhuma duração inventada.

O inventário distingue ataques roláveis, contatos e passivas. Com os
29 equipamentos, Serpente não venenosa e seis adaptações de condição/especial,
os **36 casos iniciais têm um tratamento identificado**. Isso não certifica
semântica integral de toda habilidade do bestiário: Ferrugem com metadados
insuficientes permanece assistida; armaduras com CA base fixa na ficha não
recebem uma nova CA inventada quando destruídas. Equipamento mágico empilhado
precisa de unidade separada. Preparação diária e distribuição de projéteis
continuam fora desta certificação.

Fonte original conserva 30 danos sem fórmula numérica e 16 conjuradores sem
repertório nomeado. A prontidão de encontro aplica os contratos e escolhas
aprovadas: zero ataques sem tratamento e zero conjuradores sem lista inicial.

## Ensaios

`ui_suite: monster_defaults`, quatro atores, `ui: true`, usa exclusivamente a
fixture TEMP do MCP. O script fixo valida os 29 equipamentos e a Serpente por
HTTP nativo (resolver/confirmar/retry), uma conjuração por repertório, dois
ataques sem dano e a UI das quatro fichas em desktop/390 px. A captura visual
precisa de inspeção explícita.

Primeiro corte ativado: 1533 testes backend (1 skip), 422 frontend, typecheck e
build passaram; ensaio `test-b842ecc7f84948679fe6c3d2d9dab5f6` PASS com capturas
390/1440 inspecionadas. Backup `monster-defaults-activation-20261027-020542`;
21 tabelas protegidas e tokens preservados; fichas conferidas por hash.

O segundo lote acrescenta `monster-specials-scenarios.cjs` ao mesmo ensaio
nativo: comandos HTTP dos quatro especiais, retry, turnos, persistência e
remoção. Validação final do segundo lote:

- Backend completo: **1578 testes OK, 1 skip**; após os últimos ajustes,
  **212 testes focados PASS**, incluindo os casos novos de Reflexos/Guarda.
- Frontend: **426/426 PASS**; typecheck e build PASS. Permanece o aviso
  preexistente de bundle maior que 500 kB.
- O primeiro ensaio visual identificou uma colisão de keys que repetia o
  componente de comércio no modal. Key separada e asserção de componente
  único corrigiram a duplicação; a evidência de falha foi preservada.
- Ensaio final `test-0da255d4b07246f5bbebcecd52762a40`: **PASS**. Quatro atores,
  HTTP dos especiais, retry, persistência, dano/turnos e modais em 390/1440 px.
  Capturas de Esfera, Ferrugem e identidade inspecionadas explicitamente.
- Evidências TEMP: `omni-monster-defaults-LTtu43`; JSONs HTTP e visual registram
  `production_modified:false`. Não prova celular físico nem redes distintas.
- Ativado às 06:29 de 27/10, backup
  `monster-specials-activation-20261027-062900`; 21 tabelas protegidas e tokens
  preservados. Apenas `updated_at` de mapas mudou; demais campos idênticos.
  Fichas, inventários e notas conferidos contra o backup anterior, sem mudança.
- HTML/JS/CSS públicos HTTP200; Vezemir/Raziel/Morthak acessam a própria ficha
  como owner, nível5; Dorn continua controlado pelo Mestre. OpenCode saudável,
  `companion-tests` conectado; os outros conectores não mudaram.

Portal/Desejo para neutralizar a Esfera não foi implementado. Ferrugem respeita
Reflexos e Guarda; alvo protegido exige nova confirmação em Dorn com outro
item/alcance, antes de rolar ou gastar ação.

OpenCode recebeu a auditoria textual limitada, sem ferramentas ou edição.
O modelo gratuito recusou por cota; a delegação é **INCONCLUSIVE**, não PASS.
As correções e a revisão foram realizadas localmente, sem trocar seu modelo
global nem executar sugestões de IA.

Fontes preservadas: catálogo SRD OD2, CC BY-SA 4.0, e IDs das armas/magias já
presentes na campanha. Referências públicas verificadas em 27/10:
[Goblin](https://olddragon.com.br/monstros/goblin),
[Dragão Dourado](https://olddragon.com.br/monstros/dragao-dourado),
[Flagelo da Podridão](https://olddragon.com.br/monstros/flagelo-da-podridao).

## Ajuste visual solicitado

Raça/classe/especialização têm texto maior e apenas uma moldura compacta.
Retratos dos detalhes de identidade ficam limitados a 128 px. PV/moedas
mantêm um par −/+; os spinners internos do navegador ficam ocultos e a
confirmação usa ✓ em SVG, com nome acessível. Não muda regras ou saldos.

## Arquivos do complemento e checkpoint

Núcleo: `monster_contacts.py`, `monster_parasites.py`, `monster_rust.py`,
`inventory_conditions.py`, `bat_swarm.py`; integrações localizadas no combate,
inventário, grid, workspace, catálogo e API existentes. Frontend: controles
`ParasiteControl`, `RustContactOptions`, `MonsterAttackPanel`,
`TargetConfirmation`, `CompanionAllySheet`, `api.ts` e `SessionWorkspace`.
Testes próprios e os módulos de smoke HTTP/visual estendem a suíte nativa.

Branch preservada: `devin/create-omnisvera-class-standard`, HEAD `1a07a84`.
Worktree misto preservado; sem staging, commit ou push neste complemento.
