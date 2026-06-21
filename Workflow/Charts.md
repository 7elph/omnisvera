---
obsidianUIMode: preview
NoteIcon: chart
NoteStatus: Active
status: Ativo
visibility: gm
tags:
  - workflow
  - chart
  - report
  - omnisvera
---

# Painéis de Omnisvera

## Relatório geral

![[Vault Report]]

## Personagens por papel

```dataviewjs
const pages = dv.pages('"Characters"')
  .where(page => page.file.tags?.includes("character"));

const counts = {};
for (const page of pages) {
  const role = page.role ?? "não definido";
  counts[role] = (counts[role] ?? 0) + 1;
}

const labels = Object.keys(counts);
const values = Object.values(counts);

window.renderChart({
  type: "bar",
  data: {
    labels,
    datasets: [{
      label: "Personagens",
      data: values,
      backgroundColor: ["#8f6f43", "#6f8294", "#8b5f66", "#667a5b"]
    }]
  },
  options: {
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
  }
}, this.container);
```

## Religiões em desenvolvimento

```dataview
TABLE status, info
FROM "Religion"
WHERE contains(tags, "religion")
SORT file.name ASC
```
