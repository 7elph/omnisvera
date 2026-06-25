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
  <img src="wod.png" width="1300px">
</div>

<br>



> [!cards|5]
> **DISGRACELAND**
> [![[sool.png\|sban htiny ctr p+t]]](DISGRACELAND.md)
>
> **OUTLINES**
> [![[eo.png\|sban htiny ctr]]](Outlines.md)
>
> **NOTES**
> [![[t2.png\|sban htiny ctr]]](NOTES.md)
> 
> **TTV EVENING NEWS REPORT**
> [![[news1.png\|sban htiny ctr]]](LATEST_NEWS.md)
> 
> **MAP OF TRIBUCIA**
> [![[mapp.png\|sban htiny ctr]]](TRIBUCIA%20MAP)
>



> [!world]- A LOOK AT DISGRACELAND
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
> **LATEST CHAPTERS:**
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

> [!news]+ TRIBUCIA TRIBUTE NEWS REPORT
> ### Thank you for purchasing Disgraceland!
> - Be sure to UPDATE all plug-ins and Obsidian itself, if necessary.
> #### Omegaday, 12th of [[Calendar|Bloomsun]], 2186
> - At a [[Loyalist Guard#Blackforce|Blackforce]] press conference in [[Gutter Row]], Captain [[Kullen Dane]] provided limited updates on the ongoing investigations into the [[Gutter Row#Pisstown|Pisstown]] murders, the disappearance of [[Lash Hawkins]], and the [[Loyalist Guard]] killing in the [[Gutter Row#Red Light District|Red Light District]].
> - Tensions escalated when [[Ava Victoria]] confronted the press, leading to a brief disruption.
> - Reporters [[Rachel Gold]] and [[Marlon Lambert]] pursued leads with Ava and [[Nico Murray]], following the trail to the alley where [[Lash Hawkins]] vanished.
> - A disturbing encounter with a homeless witness revealed chilling references to the ancient legend of [[Valkaara]].
> - While searching the [[Three Nail Market]], the group was threatened by gang leader [[Samson Knight]] and his enforcer [[Jailface]], raising tensions between the [[Murray Boys]] and [[Third Row]].
> - Later, at the Murray residence, Nico, Ava, Rachel & Marlon discussed the legend of [[Valkaara]] and its possible connection to the case.
> #### **[[LATEST_NEWS|Read More...]]**

> [!home]+ LAST (5) Updated Characters
> ```dataview
> table 
>  "<img src='" + thumbnail + "' width='60' style='border-radius:4px;box-shadow:0 0 3px rgba(255, 255, 255, 0.4);' />" as "IMAGE",
>   status, 
>   role, 
>   district, 
>   territory, 
>   faction, 
>   religion,
>   "<span style='font-size: 0.85em; color: #bbb;'>" + date(file.mtime) + "</span>" as "TIME/DATE"
> from "Characters"
> where contains(tags, "character")
> sort file.mtime desc
> limit 5
> ```

> [!note]+ TERRITORIES
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

> [!note]- LOCATIONS
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

<br>

```dataview
 TABLE WITHOUT ID
   link(file.path, file.folder + " / " + file.name) AS "Last Modified",
   file.mtime AS "Date"
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

2025, © **Disgraceland**