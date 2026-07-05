---
obsidianUIMode: preview
NoteIcon: class
NoteStatus: Draft
type: class
status: Regra opcional
rules_status: Autorais / adaptação de mesa
campaign_status: Em revisão
visibility: Mestre
spoiler_level: medium
gm_secret: true
created_by: Sage
name: Hemomante
aliases:
  - Hemomancia
system: Old Dragon / regra autoral de Omnisvera
class_group: Sobrenatural
primary_attribute:
level:
danger_level: Alto
thumbnail: zz_media/thumbnails/th_raziel.png
cover: zz_media/thumbnails/th_raziel.png
chapters:
  - 00 - As Crônicas de Névoa de Sangue
tags:
  - classe
  - hemomante
  - hemomancia
  - sangue
  - regra-opcional
  - raziel
  - class
---

# Hemomante

> [!warning] Regra autoral em revisão
> Hemomante é a classe usada para representar a técnica de sangue de Raziel e outros possíveis manipuladores de sangue em Omnisvera.
> Esta nota não copia regras de livros ou suplementos; é uma estrutura própria para mesa.

## Conceito

Hemomantes usam sangue como recurso, arma, rastro e linguagem arcana.

A classe não precisa ser exclusiva de vampiros, mas combina naturalmente com personagens que lidam com fome, feridas, linhagem, maldição ou pactos antigos.

Em [[Raziel]], a hemomancia é a técnica principal. A raça/condição dele é [[Vampiro]], sua linhagem é [[Vampiro Sanguinallis]] e a camada excepcional é [[Sangue Antigo]].

## Decisão Atual

Hemomante é a classe autoral de Raziel.

Separação oficial:

| Camada | Nota | Função |
|---|---|---|
| Raça/condição | [[Vampiro]] | o que Raziel é |
| Classe | [[Hemomante]] | o que Raziel faz mecanicamente |
| Linhagem | [[Vampiro Sanguinallis]] | de onde Raziel vem |
| Camada especial | [[Sangue Antigo]] | o que alterou Raziel na campanha |

Não usar Vampiro como classe ativa. A antiga nota de classe foi removida; a referência correta é [[Vampiro]] como raça/condição.

## Papel no Grupo

- Controlar campo por medo, névoa, marcas e sangue.
- Sobreviver a ferimentos com custo.
- Investigar rastros de sangue, morte e violência.
- Transformar dano recebido em oportunidade narrativa.
- Criar tensão moral: poder forte, custo visível.

## Recurso Principal — Reserva de Sangue

> [!note]
> Valores finais devem ser testados em mesa. Começar conservador.

**Reserva de Sangue** representa energia vital acumulada, autocontrole e sangue disponível para técnicas.

Sugestão inicial:

- Reserva máxima: `2 + nível`.
- Começa cada sessão com reserva baixa ou média, conforme alimentação e cena anterior.
- Pode recuperar 1 ponto de reserva ao:
  - causar ferimento significativo em combate;
  - alimentar-se de forma controlada;
  - gastar tempo extraindo sangue de uma cena;
  - sofrer dano voluntário, se o mestre permitir.

Regra de segurança:

- a reserva nunca deve justificar abuso gratuito sobre NPCs indefesos sem consequência;
- alimentação em cena deve gerar custo social, moral ou narrativo quando fizer sentido.

## Técnicas de Nível 1

Escolher poucas para começar. Raziel não precisa ter tudo no nível 1.

### Lâmina de Sangue

O hemomante reforça uma arma, garra ou lâmina com sangue.

- **Custo sugerido:** 1 Reserva de Sangue.
- **Efeito:** a próxima ação ofensiva recebe impacto narrativo sobrenatural ou pequeno bônus definido pelo mestre.
- **Uso:** tornar o golpe memorável, afetar criatura resistente ou marcar um inimigo.

### Névoa Carmesim

O hemomante transforma sangue em névoa escura ou avermelhada.

- **Custo sugerido:** 1 Reserva de Sangue.
- **Efeito:** criar cobertura curta, distração, fuga ou vantagem narrativa em furtividade.
- **Limite:** não deve substituir magia de invisibilidade perfeita.

### Estancar

O hemomante fecha feridas com força sobrenatural.

- **Custo sugerido:** 1 Reserva de Sangue.
- **Efeito:** estabilizar uma criatura, conter sangramento ou justificar recuperação limitada.
- **Custo narrativo:** a cura pode deixar marcas, dor ou sede.

### Marca Rubra

O hemomante marca uma criatura ferida.

- **Custo sugerido:** 1 Reserva de Sangue.
- **Efeito:** rastrear a presença recente da criatura por um curto período ou reconhecer seu sangue depois.
- **Uso:** investigação, perseguição e horror.

## Técnicas Avançadas em Revisão

Estas não devem ser liberadas automaticamente no nível 1:

- Asas Escarlates;
- armas sólidas de sangue;
- controle de sangue alheio;
- regeneração dramática;
- drenagem vital intensa;
- manipulação de múltiplos inimigos;
- rituais de linhagem Sanguinallis.

## Limites e Fraquezas

- Hemomancia deve ter custo: sangue, dor, fome, exposição ou consequência.
- Não deve resolver todos os conflitos sociais, físicos e mágicos.
- O mestre pode exigir fonte de sangue, ferimento aberto ou risco real.
- Usar hemomancia em público pode gerar medo, perseguição ou rumor.

## Personagens Relacionados

```dataview
TABLE thumbnail, race, status, location, faction
FROM "Characters"
WHERE class = "Hemomante" OR class = this.file.link OR contains(tags, "hemomante")
SORT file.name ASC
```

## Uso em Mesa

- **Como apresentar:** sangue se move como névoa, fio, lâmina, selo ou sombra.
- **O que os jogadores sabem:** hemomantes manipulam sangue com custo real.
- **O que manter em aberto:** origem da técnica, limites avançados e relação com o [[Sangue Antigo]].
- **Como entra em cena:** combate, investigação de ferimentos, rastros de sangue, fome, clãs e vingança.
- **Ganchos:** [[Raziel]], [[Clã Sanguinallis]], [[Vampiro Sanguinallis]], [[Sangue Antigo]].

## Pendências do Sage

- Definir valor final da Reserva de Sangue.
- Definir quais técnicas Raziel conhece no nível 1.
- Definir se Hemomante é classe completa ou especialização futura.
- Definir interação com [[Vampiro]] e [[Sangue Antigo]].
