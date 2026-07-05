---
obsidianUIMode: preview
NoteIcon: race
NoteStatus: Active
type: race
status: Regra opcional
campaign_status: Em revisão
visibility: Mestre
spoiler_level: medium
gm_secret: true
name: Vampiro
aliases:
  - Vampiros
  - Condição Vampírica
origin: Desconhecida
territory:
region:
faction:
  - "[[Clã Sanguinallis]]"
religion:
level:
danger_level: Alto
hooks:
  - Sangue Antigo
  - Clã Sanguinallis
  - Linhagens vampíricas
rumors: []
thumbnail: zz_media/thumbnails/th_raziel.png
cover: zz_media/thumbnails/th_raziel.png
chapters: []
tags:
  - raca
  - race
  - vampiro
---

# Vampiro

> [!warning] Regra opcional de campanha
> Esta nota define **Vampiro** como raça/condição jogável de Omnisvera.
> Ela não reproduz texto de livros ou suplementos. Ajustes finais ficam com o Sage.

## Decisão Atual

Em Omnisvera, **Vampiro** deve ser tratado como raça, condição ou estado sobrenatural.

Isso separa três camadas:

| Camada | Função |
|---|---|
| [[Vampiro]] | raça/condição vampírica |
| [[Hemomante]] | classe que usa sangue como técnica e recurso |
| [[Vampiro Sanguinallis]] | linhagem, cultura e história vampírica |
| [[Sangue Antigo]] | camada única da campanha ligada a Raziel |

Regra simples:

```txt
Vampiro = o que o personagem é.
Hemomante = o que o personagem faz.
Sanguinallis = de onde ele vem.
Sangue Antigo = o que alterou ele.
```

## Conceito

Vampiros são mortos-vivos conscientes, ligados a sangue, memória, fome e sobrevivência antinatural.

Nem todo vampiro precisa ser vilão, nobre oculto ou predador sem controle. Em mesa, a condição vampírica deve criar custo, tensão e escolhas, não retirar agência do personagem.

## Traços Raciais Propostos

> [!note]
> Usar como base de mesa. Números e limites podem ser ajustados conforme equilíbrio do grupo.

### Não-Vida Consciente

- O vampiro não envelhece normalmente.
- Não precisa respirar como uma criatura viva comum, mas ainda pode ser afetado por magia, venenos, maldições e efeitos sobrenaturais conforme decisão do mestre.
- Cura comum, magia divina e efeitos de restauração podem funcionar de forma diferente nele. Em caso de dúvida, tratar como complicação de cena.

### Fome de Sangue

- O vampiro precisa se alimentar de sangue em intervalos definidos pelo mestre.
- Se negligenciar a fome por muito tempo, recebe uma complicação narrativa: sede, instinto predatório, tremores, perda de controle ou penalidade situacional.
- Alimentar-se não deve ser usado como desculpa para retirar controle do jogador sem aviso.

### Sentido do Sangue

- Pode perceber sangue recente, ferimentos graves ou presença de morte próxima quando isso for relevante para a cena.
- Em termos de jogo, isso pode conceder pista, bônus situacional ou permissão narrativa para detectar rastros.

### Corpo Predatório

- O vampiro possui presença, reflexos e resistência anormais.
- Pode justificar feitos físicos dramáticos, aparência perturbadora e intimidação sobrenatural.
- Bônus específicos devem ser definidos na ficha final.

### Fraquezas Vampíricas

Escolher ou confirmar com o Sage quais fraquezas são canônicas em Omnisvera:

- prata;
- fogo;
- luz solar direta;
- símbolos sagrados;
- água corrente;
- convite/limiar;
- fome prolongada;
- magia de contenção antiga.

Nem toda tradição precisa valer. Melhor escolher poucas fraquezas fortes do que muitas fraquezas esquecidas.

## Vampiro em Nível Baixo

Para personagens de nível 1, a condição vampírica deve ser contida:

- regeneração limitada;
- fome presente, mas administrável;
- poderes dramáticos com custo;
- fraquezas reais;
- nenhum domínio completo sobre a própria condição.

## Personagens Relacionados

```dataview
TABLE status, class, location, faction
FROM "Characters"
WHERE race = "Vampiro" OR contains(string(race), "Vampiro")
SORT file.name ASC
```

## Uso em Mesa

- **Como apresentar:** fome, memória antiga, autocontrole e ameaça contida.
- **O que os jogadores sabem:** vampiros existem, mas suas regras exatas podem variar por linhagem.
- **O que manter em aberto:** origem, limites e consequências profundas ficam no [[CAMPANHA/ESTADO_DA_CAMPANHA]] e nos dossiês do mestre.
- **Como entra em cena:** sangue, clãs, maldições, caçadas, ruínas, pactos e inimigos antigos.
- **Ganchos:** [[Clã Sanguinallis]], [[Vampiro Sanguinallis]], [[Sangue Antigo]], prata, fome e antigos juramentos.

## Pendências do Sage

- Confirmar fraquezas vampíricas canônicas.
- Definir se vampiros comuns existem fora dos Sanguinallis.
- Definir como cura, magia sagrada e descanso afetam vampiros.
- Confirmar quais traços são públicos para jogadores.
