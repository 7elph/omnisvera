## VAULT REPORT
![[Vault Report]]

## RELIGION REPORT
```dataviewjs
const pages = dv.pages().where(p => p.tags);
let tagCounts = {};

// Count key tags
for (let page of pages) {
  const tags = Array.isArray(page.tags) ? page.tags : [page.tags];
  for (let tag of tags) {
if (['stillborn-star', 'ember-saint', 'el-santo', 'mirella', 'none'].includes(tag)) {
      tagCounts[tag] = (tagCounts[tag] || 0) + 1;
    }
  }
}

// Data
const labels = Object.keys(tagCounts);
const counts = Object.values(tagCounts);

// 💀 Grunge palette
const colorMap = {
  'stillborn-star': '#c8ae5f', // antique gold
  'ember-saint': '#9e9e9e',   // blood rust red
  'el-santo': '#D66843',      // steel blue
  'none': '#91a6ba'           // swamp green
};
// Helper: Darken a hex color
function shadeColor(hex, percent) {
  let num = parseInt(hex.replace("#", ""), 16);
  let r = (num >> 16) + percent;
  let g = ((num >> 8) & 0x00FF) + percent;
  let b = (num & 0x0000FF) + percent;

  r = Math.min(255, Math.max(0, r));
  g = Math.min(255, Math.max(0, g));
  b = Math.min(255, Math.max(0, b));

  return `rgb(${r}, ${g}, ${b})`;
}

const backgroundColors = labels.map(label => colorMap[label] || '#777');

// Chart config
const chartData = {
    type: 'bar',
    data: {
        labels: labels,
        datasets: [{
            label: 'Religion',
            data: counts,
            backgroundColor: backgroundColors,
            borderColor: '#222',
            borderWidth: 1
        }]
    },
    options: {
        plugins: {
            legend: {
                labels: {
                    color: '#CCC'
                }
            }
        },
        scales: {
            x: {
                ticks: { color: '#CCC' },
                grid: { color: '#444' }
            },
            y: {
                ticks: { color: '#CCC' },
                grid: { color: '#444' }
            }
        }
    }
};

window.renderChart(chartData, this.container);
```
