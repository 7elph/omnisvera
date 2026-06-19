---
obsidianUIMode: preview
banner: "[[zz_media/big1.png]]"
banner-x: 51
banner-y: 34
banner-height: 280
content-start: 271
banner-fade: -45

---

<div style="text-align: center;">
  <img src="omnisvera.png" width="1300px">
</div>

<br>



> [!cards|5]
> **OMNISVERA**
> [![[sool.png\|sban htiny ctr p+t]]](EARTHROPO/EARTHROPO.md)
>
> **OUTLINES**
> [![[eo.png\|sban htiny ctr]]](Workflow/OUTLINES.md)
>
> **NOTES**
> [![[t2.png\|sban htiny ctr]]](NOTES.md)
> 
> **NOTÍCIAS DO REINO**
> [![[guild.png\|sban htiny ctr]]](LATEST_NEWS.md)
> 
> **MAPA DE EARTHROPO**
> [![[mapp.png\|sban htiny ctr]]](MAPA%20DE%20EARTHROPO.md)
>



> [!world]- OMNISVERA DE PERTO
> ```datacards 
> TABLE cover FROM #home
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
>```calendarium
>```
> **ÚLTIMOS CAPÍTULOS:**
>```datacards 
>TABLE cover, date, description FROM #story
>SORT file.ctime desc
>limit 3
>
>// Settings 
>preset: square 
>columns: 1 
>imageProperty: cover
>imageWidth: 50px
>```


> [!news]+ CORREIO DO REINO — NOTÍCIAS DE EARTHROPO
> ### Capítulo 01: Sombras do Evento Principal
> - Um viajante moribundo chamado **Elias Vorn** chega a [[Locations/Oakvale|Oakvale]] carregando um artefato desconhecido.
> - A [[Factions/Igreja das Sete Chamas|Igreja das Sete Chamas]] envia o Inquisidor **Aldous Vane** para recuperar o artefato.
> - Os heróis descobrem o primeiro **Fragmento dos Criadores** nas ruínas da Floresta de Thornmarch.
> - O [[Factions/Culto dos Sussurrantes|Culto dos Sussurrantes]] começa a se revelar nas sombras.
> #### **[[LATEST_NEWS|Leia Mais...]]**


> [!home]+ ÚLTIMOS (5) PERSONAGENS ATUALIZADOS
> ```dataview
> table 
>  "<img src='" + thumbnail + "' width='60' style='border-radius:4px;box-shadow:0 0 3px rgba(255, 255, 255, 0.4);' />" as "IMAGEM",
>   status, 
>   role, 
>   district, 
>   territory, 
>   faction, 
>   religion,
>   "<span style='font-size: 0.85em; color: #bbb;'>" + date(file.mtime) + "</span>" as "DATA"
> from "Characters"
> where contains(tags, "character")
> sort file.mtime desc
> limit 5
> ```

> [!note]+ TERRITÓRIOS
> ```datacards
> TABLE cover, region, leader, population FROM #territory
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
> TABLE cover, status FROM #class
> SORT name ASC
> 
> // Settings
> preset: portrait
> columns: 4
> imageProperty: cover
> cardSpacing: 4
> ```

<br>

```dataview
 TABLE WITHOUT ID
   link(file.path, file.folder + " / " + file.name) AS "Última Modificação",
   file.mtime AS "Data"
 FROM "/"
 WHERE file.mtime >= date(today) - dur(30 days)
 AND file.name != this.file.name
     AND !contains(file.path, "z_Assets")
    AND !contains(file.path, "Inline Scripts")
     AND !contains(file.path, "z_Templates")
     AND !contains(file.path, "daily notes")
     AND !contains(file.path, "BRAT")
 SORT file.mtime DESC
 LIMIT 10
```

---

2026, © **Omnisvera**