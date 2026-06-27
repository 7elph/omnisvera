> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# RPG VAULT OPERATING MODEL

Este documento define o modelo operacional de um vault de RPG de mesa inspirado na arquitetura técnica funcional do Disgraceland.

Escopo: modelo conceitual/técnico. Não compara com Omnisvera e não aplica mudanças em nenhum vault.

## 1. O que um vault de RPG precisa fazer

Um vault de RPG precisa funcionar em dois ritmos diferentes:

1. Preparação fora da mesa.
2. Consulta rápida durante a sessão.

Disgraceland já demonstra uma arquitetura útil para isso: notas com frontmatter previsível, dashboards com Dataview/DataCards, tags visuais, mídia centralizada, mapa Leaflet e calendário diegético. Para RPG, essa arquitetura precisa ser reinterpretada para decisões de mestre, jogadores, sessão e revelação progressiva.

## 2. Consulta rápida durante sessão

Durante a mesa, o mestre precisa encontrar informação em segundos:

- quem é o NPC;
- onde ele está;
- qual facção controla o local;
- o que os jogadores já sabem;
- qual pista pode ser entregue;
- qual imagem/retrato pode ser mostrada;
- qual segredo deve permanecer oculto;
- qual mapa/local deve ser aberto.

Funções herdáveis do Disgraceland:

- DataCards para cards visuais de personagens, locais e facções;
- Dataview para listas filtradas;
- Home/dashboard como entrada;
- Supercharged Links para cor/agrupamento visual;
- Leaflet para navegação espacial;
- Calendarium para data em jogo;
- `thumbnail`, `cover` e embeds para reconhecimento visual rápido.

Reinterpretação necessária:

- `chapters` vira ou convive com `sessions`, `arcs` e `appearances`;
- tags de facção passam a indicar grupos de campanha;
- `story` passa a representar sessão, capítulo jogado ou registro de campanha;
- `status` precisa separar estado narrativo de estado mecânico.

## 3. Preparação de sessão

O vault deve permitir preparar:

- cenas;
- encontros;
- NPCs envolvidos;
- locais visitáveis;
- rumores disponíveis;
- pistas a revelar;
- consequências prováveis;
- handouts;
- mapas;
- calendário/data em jogo;
- checklist pós-sessão.

O modelo ideal usa notas de `Sessão/Capítulo` como pivô. Cada sessão puxa personagens, locais, facções, quests, rumores e handouts por tags ou campos.

## 4. Controle de NPCs

NPCs precisam ser divididos por função operacional:

- NPC importante;
- NPC menor;
- antagonista;
- aliado;
- contato;
- vendedor;
- informante;
- figura pública;
- morto/desaparecido.

Campos essenciais para consulta:

- `type`
- `subtype`
- `life_status`
- `location`
- `territory`
- `faction`
- `role`
- `visibility`
- `player_known`
- `thumbnail`
- `portrait`
- `sessions`
- `hooks`
- `rumors`

## 5. Controle de personagens jogadores

Personagens jogadores precisam de contrato próprio. Eles compartilham parte da estrutura de personagem, mas exigem campos mecânicos e de jogador:

- jogador responsável;
- raça;
- classe;
- nível;
- religião;
- facção;
- origem;
- status;
- sessões;
- vínculos;
- itens relevantes.

O vault deve separar ficha mecânica detalhada de resumo narrativo operacional. O dashboard precisa mostrar o que importa durante sessão, não substituir a ficha completa.

## 6. Controle de facções

Facções são hubs de rede:

- membros;
- líderes;
- territórios;
- relações;
- objetivos;
- status;
- nível de ameaça;
- rumores;
- quests ligadas;
- reputação com o grupo.

Disgraceland usa tags de facção como infraestrutura visual e DataCards. Em RPG, isso continua útil, mas as tags precisam ser planejadas como API visual, não só como classificação narrativa.

## 7. Regiões e locais

O vault precisa distinguir escala:

- continente;
- reino;
- região;
- território;
- cidade/vila/assentamento;
- bairro/distrito;
- local;
- dungeon;
- sala/área.

Disgraceland já separa `Territories` e `Locations`. Para RPG, o modelo deve permitir mapas e consultas por hierarquia: região contém assentamentos, assentamento contém locais, dungeon contém áreas.

## 8. Mapas

Mapas precisam servir a três usos:

- navegação do mestre;
- orientação dos jogadores;
- indexação de notas por marcador.

Requisitos:

- mapas de mundo/continente/reino/região/cidade/dungeon;
- Leaflet com marcadores linkando notas;
- controle de mapa público vs mapa do mestre;
- camadas por tipo de marcador;
- risco explícito para renomeação de notas.

## 9. Calendário

O calendário deve controlar:

- data em jogo;
- sessões jogadas;
- eventos históricos;
- eventos futuros;
- feriados;
- eventos religiosos;
- prazos de quests;
- consequências temporais.

O modelo de Disgraceland com Calendarium é diretamente útil, mas precisa ser expandido para `session_date`, `in_game_date`, `deadline`, `revealed_in` e `historical_date`.

## 10. Pistas e revelações

RPG exige uma camada que Disgraceland não precisava explicitar tanto:

- pista não descoberta;
- pista disponível;
- pista descoberta;
- segredo do mestre;
- revelação futura;
- spoiler pesado;
- handout liberado;
- rumor falso.

Isso exige campos de visibilidade e status de revelação.

## 11. Informações públicas e secretas

Toda nota relevante deve poder responder:

- isso pode ser mostrado ao jogador?
- isso já foi revelado?
- isso é segredo do mestre?
- isso é mecânico ou narrativo?
- isso depende de uma sessão específica?

O modelo deve evitar duplicar o vault inteiro em “mestre” e “jogador”; em vez disso, deve usar campos de visibilidade e dashboards filtrados.

## 12. Handouts

Handouts são objetos de entrega aos jogadores:

- imagem;
- carta;
- mapa parcial;
- símbolo;
- retrato;
- documento;
- rumor impresso;
- pista visual.

Cada handout precisa saber:

- se foi liberado;
- quando foi liberado;
- para quem;
- arquivo de mídia;
- nota associada;
- segredo relacionado.

## 13. Imagens e retratos

Disgraceland usa `thumbnail`, `cover`, banners e embeds. Em RPG, esses campos devem ser especializados:

- `thumbnail`: card pequeno.
- `cover`: capa de nota/card grande.
- `portrait`: retrato de personagem/NPC.
- `token_image`: token de combate/mesa virtual.
- `map_image`: imagem de mapa.
- `handout_image`: imagem entregável.

## 14. Aparições por sessão/capítulo

O padrão `chapters` de Disgraceland é útil, mas em RPG deve evoluir para:

- `sessions`: sessões em que apareceu;
- `arcs`: arcos associados;
- `appears_in`: índice genérico;
- `revealed_in`: quando uma informação foi revelada.

Regra: não remover `chapters` numa migração futura sem uma camada compatível.

## 15. Dashboard do mestre

O dashboard do mestre deve priorizar operação:

- sessão atual;
- data em jogo;
- local atual;
- PCs;
- NPCs em cena;
- facções ativas;
- quests abertas;
- rumores disponíveis;
- pistas não reveladas;
- handouts prontos;
- mapas usados;
- últimas notas modificadas.

O padrão Home do Disgraceland é útil como base, mas precisa ser reinterpretado como painel de mesa, não como vitrine narrativa.

## 16. Navegação mobile

Durante sessão, navegação mobile precisa:

- cards compactos;
- poucas colunas;
- imagens pequenas;
- consultas rápidas;
- links de volta;
- dashboards por contexto;
- evitar tabelas largas demais.

DataCards e Dataview precisam ser usados com cuidado para não criar painéis ilegíveis em tela pequena.

## 17. Uso durante mesa

O modelo precisa reduzir fricção:

- um clique para abrir mapa;
- um clique para NPC;
- um clique para handout;
- filtros por sessão/local/facção;
- informações secretas protegidas por `visibility` e `spoiler_level`;
- imagens separadas entre públicas e secretas;
- pós-sessão fácil: atualizar `sessions`, `player_known`, `revealed_in`, status de quests e rumores.

## 18. Funções do Disgraceland úteis para RPG

Diretamente úteis:

- frontmatter como API;
- DataCards;
- Dataview;
- Supercharged Links;
- Style Settings;
- snippets de callout;
- `thumbnail` e `cover`;
- Home/dashboard;
- Leaflet;
- Calendarium;
- mídia centralizada em `zz_media`;
- tags visuais.

Precisam ser reinterpretadas:

- capítulos como sessões/arcos;
- facções narrativas como facções jogáveis;
- territórios como hierarquia geográfica;
- lore como conhecimento público/segredo/revelação;
- Home como dashboard de mestre;
- notícias como boletim, recap ou registro de sessão.

Não devem ser copiadas cegamente:

- tags específicas de Disgraceland;
- nomes de lugares/facções;
- conteúdo narrativo;
- estética urbana/pós-apocalíptica;
- campos sem análise de uso.
