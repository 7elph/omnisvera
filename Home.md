---
obsidianUIMode: preview
banner: "[[zz_media/locations/floresta-de-avenor.webp]]"
banner-x: 51
banner-y: 34
banner-height: 280
content-start: 271
banner-fade: -45
NoteStatus: Active
status: Ativo
visibility: player
tags:
  - home
  - player
---

# 🜂 NIMALIA

> *“Toda estrada parece simples antes do primeiro passo. Nas fronteiras de Nimalia, a floresta guarda nomes esquecidos, as ruínas preservam vozes antigas e cada viajante carrega uma história que ainda pode mudar Earthropo.”*

Esta é a entrada dos jogadores para as **Crônicas de Earthropo**. O mapa será preenchido conforme lugares, perigos e histórias forem descobertos.

> [!cards|5]
> **GUIA DO JOGADOR**
> [![[zz_media/ui/card-guia.webp\|sban htiny ctr p+t]]](Players/Guia%20do%20Jogador.md)
>
> **CRÔNICAS**
> [![[zz_media/ui/card-cronicas.webp\|sban htiny ctr]]](EARTHROPO/EARTHROPO.md)
>
> **PERSONAGENS**
> [![[zz_media/ui/card-notas.webp\|sban htiny ctr]]](Players/Personagens.md)
>
> **RUMORES**
> [![[zz_media/ui/card-boletim.webp\|sban htiny ctr]]](LATEST_NEWS.md)
>
> **MAPA**
> [![[zz_media/ui/card-mapa.webp\|sban htiny ctr]]](MAPA%20DE%20EARTHROPO.md)

> [!world]- O que é conhecido
> **Earthropo** é um continente de caminhos antigos, reinos ainda pouco conhecidos e ruínas que sobreviveram às histórias contadas sobre elas.
>
> O **Reino de Nimalia**, terra de muitos povos antropos, será o ponto de partida da campanha. Sua capital é [[Nimalis]].
>
> A campanha começa no nível 1, em **3 de Ventara de 2377**.

> [!infobox]
> ```calendarium
> ```
>
> **CRÔNICAS DISPONÍVEIS**
> ```datacards
> TABLE cover, date, description
> FROM #story AND #earthropo
> WHERE visibility = "player" OR visibility = "shared"
> SORT file.name ASC
>
> // Settings
> preset: square
> columns: 1
> imageProperty: cover
> imageWidth: 50px
> ```

> [!news]+ Rumores atuais
> - Viajantes evitam estradas onde a névoa parece permanecer mesmo sob o sol.
> - Remédios falsos circulam nas regiões portuárias de Nimalis.
> - Algumas ruínas do sudeste voltaram a atrair exploradores.
>
> [[LATEST_NEWS|Ler rumores e descobertas]]

> [!home]+ Personagens jogadores
> ```datacards
> TABLE cover, class, race, level, status
> FROM "Characters/Individual"
> SORT file.name ASC
> 
> // Settings
> preset: portrait
> columns: 5
> imageProperty: cover
> cardSpacing: 4
> ```

> [!note]+ Territórios conhecidos
> ```datacards
> TABLE cover, type, population
> FROM #territory
> WHERE visibility = "player" OR visibility = "shared"
> SORT file.name ASC
>
> // Settings
> preset: portrait
> columns: 5
> imageProperty: cover
> cardSpacing: 4
> ```

> [!note]- Localizações conhecidas
> ```datacards
> TABLE cover, territory, info
> FROM #location
> WHERE visibility = "player" OR visibility = "shared"
> SORT file.name ASC
>
> // Settings
> preset: grid
> columns: 5
> imageProperty: cover
> cardSpacing: 4
> ```

---

2026, © **Omnisvera**
