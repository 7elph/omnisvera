---
obsidianUIMode: preview
NoteIcon: race
NoteStatus: Active
type: race
status: Ativa
campaign_status: Ativa
visibility: Jogadores
spoiler_level: light
gm_secret: false
name: Meio-Elfo
aliases:
  - Meio Humano
  - Meio Elfo
  - Meio-Elfos
origin: Earthropo
territory:
region:
faction:
religion:
level:
danger_level:
hooks:
  - Identidade entre culturas
  - Relações humanas e élficas em Avenor
rumors: []
thumbnail: zz_media/thumbnails/th_vezemir.png
cover: zz_media/thumbnails/th_vezemir.png
chapters: []
tags:
  - raca
  - race
  - meio-elfo
---

# Meio-Elfo

## Visão Geral

Meio-elfos existem entre mundos: tradição élfica, urgência humana, pertencimento parcial e desconfiança de ambos os lados.

[[Vezemir]] é o exemplo central dessa raça no início da campanha.

## Presença em Omnisvera

- Podem surgir em regiões de contato humano/élfico.
- Avenor, Leth'valora e vilas mistas são pontos prováveis.
- Podem carregar heranças sociais, familiares ou mágicas ambíguas.

## Cultura e Relações

Meio-elfos são ótimos para histórias de fronteira, identidade, perda e escolha de pertencimento.

## Mecânica Resumida

Meio-Elfo é uma categoria especial em Omnisvera.

Para [[Vezemir]], a ficha foi montada pegando parte da base mecânica de Humano e parte da base mecânica de Elfo, conforme decisão de mesa.

| Elemento | Regra de consulta |
|---|---|
| Base | Combinação de Humano + Elfo |
| Uso atual | Raça de [[Vezemir]] |
| Status | Categoria especial aprovada para personagem |
| Ajuste fino | Decisão do mestre conforme ficha final |

Não tratar Meio-Elfo como simples “humano com orelha élfica”. Em mesa, ele representa mistura de linhagem, cultura, memória e pertencimento dividido.

## Personagens Relacionados

```dataview
TABLE status, role, location, faction
FROM "Characters"
WHERE race = "Meio-Elfo" OR contains(string(race), "Meio-Elfo") OR contains(string(race), "Meio Humano") OR contains(string(race), "Meio Elfo")
SORT file.name ASC
```

## Uso em Mesa

- Como apresentar: personagem entre culturas.
- O que os jogadores sabem: Vezemir é meio humano/meio elfo.
- O que manter em aberto no [[ESTADO_DA_CAMPANHA]]: linhagens específicas podem se conectar a segredos de Avenor.
- Como entra em cena: conflitos de herança, famílias partidas, memória de vilas destruídas.
- Ganchos: Leth'valora, Mira Valen, o dragão, o medalhão.
- Consequências possíveis: escolhas do personagem podem afetar humanos e elfos.

## Pendências do Sage

- Definir se meio-elfos são comuns ou raros em Omnisvera.
- Definir tratamento social em Nimalia e no futuro reino élfico.
