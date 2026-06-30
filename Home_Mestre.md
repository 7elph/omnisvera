---
obsidianUIMode: preview
banner: "[[zz_media/avenor.png]]"
banner-x: 51
banner-y: 34
banner-height: 280
content-start: 271
banner-fade: -45
visibility: Mestre
spoiler_level: heavy
gm_secret: true
---

<div style="text-align: center;">
  <img src="zz_media/omnisvera.PNG" width="1300px">
</div>

<br>

> [!cards|5]
> **NIMALIA**
> [![[mapa-de-nimalia.png|sban htiny ctr p+t]]](MAPA%20DE%20NIMALIA.md)
>
> **CRÔNICAS**
> [![[banner-earthropo.png|sban htiny ctr]]](EARTHROPO/EARTHROPO.md)
>
> **NOTAS**
> [![[guild.png|sban htiny ctr]]](NOTES.md)
>
> **RUMORES E DESCOBERTAS**
> [![[guild1.png|sban htiny ctr]]](LATEST_NEWS.md)
>
> **MAPAS DE EARTHROPO**
> [![[earthropo.png|sban htiny ctr]]](MAPA%20DE%20EARTHROPO.md)

> [!home]+ NAVEGAÇÃO DO MESTRE
> Esta Home é a mesa visual do mestre: mapas, índices e acesso rápido. A preparação completa, segredos e decisões de sessão ficam em [[CAMPANHA/ESTADO_DA_CAMPANHA|Estado da Campanha]].
>
> - [[CAMPANHA/ESTADO_DA_CAMPANHA|Estado da Campanha — painel operacional]]
> - [[CAMPANHA/ESTADO_DA_CAMPANHA#Próxima Sessão|Próxima Sessão]]
> - [[CAMPANHA/ESTADO_DA_CAMPANHA#Dossiê do Mestre — Capítulo 01: Ecos do Mundo Perdido|Dossiê do Mestre — Capítulo 01]]
> - [[01 - Ecos do Mundo Perdido|Capítulo 01 — versão pública]]
> - [[EARTHROPO/EARTHROPO|Crônicas de Earthropo]]
> - [[CAMPANHA/Quests/INDICE_DE_QUESTS|Índice de Quests]]
> - [[CAMPANHA/Rumors/INDICE_DE_RUMORES|Índice de Rumores]]

# 🜂 NIMALIA

> *“Toda estrada parece simples antes do primeiro passo. Nas fronteiras de Nimalia, a floresta guarda nomes esquecidos, as ruínas preservam vozes antigas e cada viajante carrega uma história que ainda pode mudar Earthropo.”*

Nimalia é o primeiro horizonte das **Crônicas de Earthropo**: um ponto de partida para jornadas, descobertas e histórias que serão construídas durante a campanha.

> [!world]- UM PRIMEIRO OLHAR SOBRE EARTHROPO
> ```datacards
> TABLE cover FROM #home
> WHERE !contains(file.path, "Workflow/")
> AND !contains(file.path, "Templates/")
> SORT file.name asc
>
> // Settings
> preset: dense
> columns: 6
> imageProperty: cover
> cardSpacing: 4
> imageHeight: 50px
> ```

<div class="homepage">
<hr>
</div>

> [!infobox]
> ```calendarium
> ```
> **CRÔNICAS DISPONÍVEIS:**
> ```datacards
> TABLE cover, status, campaign_status, description
> FROM "EARTHROPO"
> WHERE contains(tags, "story")
> SORT file.name asc
> LIMIT 3
>
> // Settings
> preset: square
> columns: 1
> imageProperty: cover
> imageWidth: 50px
> ```

> [!news]+ FIOS DA CAMPANHA
> A Home do Mestre mostra a visão rápida: personagens, territórios, locais, raças, classes e crônicas disponíveis.
>
> A preparação real de sessão fica centralizada em [[CAMPANHA/ESTADO_DA_CAMPANHA|Estado da Campanha]], incluindo segredos, pistas escolhidas, consequências, bastidores e pendências antes da mesa.
>
> - Capítulo público atual: [[01 - Ecos do Mundo Perdido]]
> - Painel de preparação: [[CAMPANHA/ESTADO_DA_CAMPANHA#Próxima Sessão|Próxima Sessão]]
> - Quests: [[CAMPANHA/Quests/INDICE_DE_QUESTS]]
> - Rumores: [[CAMPANHA/Rumors/INDICE_DE_RUMORES]]

> [!home]+ ÚLTIMOS (5) PERSONAGENS ATUALIZADOS
> ```dataview
> TABLE
>   choice(thumbnail, "<img src='" + thumbnail + "' width='60' style='border-radius:4px;box-shadow:0 0 3px rgba(255, 255, 255, 0.4);' />", "—") AS "IMAGEM",
>   status,
>   role,
>   district,
>   territory,
>   faction,
>   religion,
>   "<span style='font-size: 0.85em; color: #bbb;'>" + date(file.mtime) + "</span>" AS "DATA"
> FROM "Characters"
> WHERE contains(tags, "character")
> SORT file.mtime DESC
> LIMIT 5
> ```

> [!note]+ TERRITÓRIOS
> ```datacards
> TABLE cover, region, leader, population FROM "Territories"
> WHERE NoteStatus != "Placeholder"
> AND !contains(file.path, "Workflow/")
> AND !contains(file.path, "Templates/")
> SORT name DESC
>
> // Settings
> preset: portrait
> columns: 6
> imageProperty: cover
> cardSpacing: 4
> ```

> [!note]- LOCALIZAÇÕES
> ```datacards
> TABLE cover, territory, info FROM "Locations"
> WHERE NoteStatus != "Placeholder"
> AND !contains(file.path, "Workflow/")
> AND !contains(file.path, "Templates/")
> SORT rating ASC
>
> // Settings
> preset: grid
> columns: 5
> imageProperty: cover
> cardSpacing: 4
> ```

> [!note]- RAÇAS
> ```datacards
> TABLE cover, status FROM "Races"
> WHERE NoteStatus != "Placeholder"
> SORT name ASC
>
> // Settings
> preset: portrait
> columns: 6
> imageProperty: cover
> cardSpacing: 4
> ```

> [!note]- CLASSES
> ```datacards
> TABLE cover, status FROM "Classes" AND #classe
> SORT name ASC
>
> // Settings
> preset: portrait
> columns: 4
> imageProperty: cover
> cardSpacing: 4
> ```

## Ferramentas do Mestre

> [!note]+ OPERAÇÃO DE MESA
> - [[CAMPANHA/ESTADO_DA_CAMPANHA|Estado da Campanha]]
> - [[Workflow/_audit/Pending_Review/VAULT_STANDARDIZATION_BACKLOG|Fila de Padronização]]
> - [[Workflow/_audit/Pending_Review/VAULT_PENDING_REVIEW|Pendências do Vault]]
>
> [!warning]- DOCUMENTAÇÃO TÉCNICA
> Abrir apenas quando estiver organizando o vault, não durante sessão.
> - [[Workflow/OMNISVERA_SYSTEM_TAXONOMY|Taxonomia Técnica do Omnisvera]]
> - [[Workflow/OMNISVERA_DASHBOARD_SYSTEM|Sistema de Dashboards]]
> - [[Workflow/README|Índice do Workflow]]

<br>

> [!note]- MODIFICADOS RECENTEMENTE
> ```dataview
> TABLE WITHOUT ID
>   link(file.path, file.folder + " / " + file.name) AS "Última Modificação",
>   file.mtime AS "Data"
> FROM "/"
> WHERE file.mtime >= date(today) - dur(30 days)
> AND file.name != this.file.name
> AND !contains(file.path, "zz_media")
> AND !contains(file.path, "Workflow/")
> AND !contains(file.path, "Templates/")
> AND !contains(file.path, "z_Assets")
> AND !contains(file.path, "Inline Scripts")
> AND !contains(file.path, "z_Templates")
> AND !contains(file.path, "daily notes")
> AND !contains(file.path, "BRAT")
> AND !contains(file.name, "Legacy -")
> SORT file.mtime DESC
> LIMIT 10
> ```

---

2026, © **Omnisvera**
