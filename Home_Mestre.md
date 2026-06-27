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

> [!important]+ DASHBOARD DO MESTRE
> Esta página pode conter preparação, spoilers, pendências, relatórios técnicos, NPCs secretos e links administrativos.
>
> Para uma visão conservadora e segura para jogadores, use [[Home]].

> [!cards|5]
> **NIMALIA**
> [![[mapa-de-nimalia.png|sban htiny ctr p+t]]](Territories/Nimalia.md)
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
> TABLE cover, date, description FROM #story AND #earthropo
> WHERE !contains(file.path, "Workflow/")
> AND !contains(file.path, "Templates/")
> SORT file.ctime desc
> LIMIT 3
>
> // Settings
> preset: square
> columns: 1
> imageProperty: cover
> imageWidth: 50px
> ```

> [!news]+ FIOS DA CAMPANHA
> Três histórias avançam por Earthropo, ainda sem saber onde irão se encontrar:
>
> - [[Vezemir]] percorre a [[Floresta de Avenor]] em busca do dragão de colar dourado que destruiu [[Leth'valora]].
> - [[Varkh Nimalis]] deixa [[Maré Baixa]] para descobrir quem está usando os métodos de seu mestre na fabricação de remédios falsos.
> - [[Raziel]] retorna a um mundo transformado depois de mais de trezentos anos de aprisionamento, carregando antigas dívidas de sangue.
>
> A campanha começa no nível 1. O mapa não será entregue pronto: lugares, perigos e histórias ganharão forma à medida que forem descobertos.
>
> #### **[[LATEST_NEWS|Leia Mais...]]**

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
> TABLE cover, region, leader, population FROM #territorio
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
> TABLE cover, territory, info FROM #location
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
> TABLE cover, status FROM #race
> WHERE !contains(file.path, "Workflow/")
> AND !contains(file.path, "Templates/")
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
> TABLE cover, status FROM "Rules/Classes" AND #classe
> SORT name ASC
>
> // Settings
> preset: portrait
> columns: 4
> imageProperty: cover
> cardSpacing: 4
> ```

## Ferramentas e relatórios do mestre

> [!note]+ SISTEMA E MIGRAÇÃO
> - [[Workflow/OMNISVERA_SYSTEM_TAXONOMY|Taxonomia Técnica do Omnisvera]]
> - [[Workflow/_audit/Plugin_Migration/PLUGIN_TAG_MIGRATION_AUDIT|Auditoria de Migração de Tags]]
> - [[Workflow/_audit/Taxonomy_Alignment/TAXONOMY_ALIGNMENT_VALIDATION|Validação da Taxonomia]]
> - [[Workflow/_audit/Omnisvera/OMNISVERA_OBSIDIAN_DEPENDENCY_MAP|Auditoria Técnica do Omnisvera]]
>
> [!warning]- Arquivo histórico / legado
> Estes documentos são anteriores à taxonomia oficial atual e não devem orientar novas migrações.
> - [[Workflow/COMPATIBILITY_LAYER/COMPATIBILITY_LAYER_INDEX|Camada de Compatibilidade Histórica]]
> - [[Workflow/_audit/Decision_Packet/SAGE_DECISION_PACKET|Pacote de Decisões Histórico]]

<br>

```dataview
TABLE WITHOUT ID
  link(file.path, file.folder + " / " + file.name) AS "Última Modificação",
  file.mtime AS "Data"
FROM "/"
WHERE file.mtime >= date(today) - dur(30 days)
AND file.name != this.file.name
AND !contains(file.path, "zz_media")
AND !contains(file.path, "Workflow/")
AND !contains(file.path, "Templates/")
AND !contains(file.path, "z_Assets")
AND !contains(file.path, "Inline Scripts")
AND !contains(file.path, "z_Templates")
AND !contains(file.path, "daily notes")
AND !contains(file.path, "BRAT")
AND !contains(file.name, "Legacy -")
SORT file.mtime DESC
LIMIT 10
```

---

2026, © **Omnisvera**
