---
tags: 
  - home
cover: zz_media/t7.png
---

```datacards 
TABLE cover, info FROM #lore 
WHERE !contains(file.path, "Workflow/")
AND !contains(file.path, "Templates/")
SORT file.name asc

// Settings 
preset: square 
columns: 6
imageProperty: cover
```
