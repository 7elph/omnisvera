# CSS SNIPPET INDEX

Gerado em: 2026-06-26 07:40.

## Snippets

| snippet | tamanho | classes | callouts | atributos/seletores | gerado | notas afetadas exemplo |
| --- | --- | --- | --- | --- | --- | --- |
| bside.css | 1318 | b-sides-script | — | — | não detectado | DISGRACELAND/01 - Main Event Shadows.md, DISGRACELAND/02 - Ghosts On The Waves.md, DISGRACELAND/03 - The Devil In The Row.md |
| dgl.css | 5093 | calendar, calendar-title, callout, callout-icon, callout-stack, callout-title, centered-img, character-box-right, cm-header, console-callout-grid, console-grid, dataview +8 | info, note, tip, todo | [data-callout="info"], [data-callout="note"], [data-callout="tip"], [data-callout="todo"] | não detectado | .trash/Call Out Boxes/Call Out Boxes.md, .trash/Call Out Boxes/Call Out - Call Out Box.md, .trash/Call Out Boxes/Call Out - Read Aloud.md, .trash/Call Out Boxes/Call Out - Flavor.md +2 |
| disgraceland-profile.css | 2967 | com, disgraceland-profile, googleapis, region-ashmoor, region-charspire, region-drownlands, region-gutterrow, region-steeltown, region-threshton | — | [class^="region-"] | não detectado | — |
| fullstat.css | 110 | obsidian-vault-full-statistics--item | — | — | não detectado | — |
| hrline.css | 371 | homepage | — | — | não detectado | DISGRACELAND/DISGRACELAND.md, Home.md |
| htc.css | 80 | datacards-card | — | — | não detectado | — |
| scriptwrite.css | 1446 | disgraceland-script | — | — | não detectado | .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 01.md, .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 02.md, .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 03.md |
| supercharged-links-gen.css | 33980 | c-15ae-9b1f-use-background, c-287d-312f-use-background, c-3623-52e1-use-background, c-4740-17da-use-background, c-6e9a-b654-use-background, c-7457-fe20-use-background, c-7e5f-283b-use-background, c-7eac-9a5f-use-background, c-9cd0-d420-use-background, c-ce91-5784-use-background, c-e2c5-b197-use-background, c-e997-0713-use-background +5 | — | [data-id="15ae-9b1f"], [data-id="287d-312f"], [data-id="3623-52e1"], [data-id="4740-17da"], [data-id="6e9a-b654"], [data-id="7457-fe20"], [data-id="7e5f-283b"], [data-id="7eac-9a5f"] +12 | sim; não editar diretamente | — |
| test.css | 790 | expand-button, news-box, news-full, news-preview, news-toggle | — | — | não detectado | Legacy - Disgraceland Scratch Notes.md, Workflow/Scratch Notes.md +8 |
| titlehide.css | 118 | markdown-preview-view | — | — | não detectado | — |
| topnav.css | 682 | top-nav | — | — | não detectado | — |
| videopop.css | 1495 | callout, video-container, video-popup, video-wrapper | video | [data-callout="video"] | não detectado | — |
| world.css | 2601 | callout, callout-icon, callout-title | home, news, world | [!news], [data-callout="home"], [data-callout="news"], [data-callout="world"] | não detectado | Home.md, Legacy - Disgraceland Scratch Notes.md, Workflow/Scratch Notes.md, DISGRACELAND/01 - Main Event Shadows.md, DISGRACELAND/02 - Ghosts On The Waves.md, DISGRACELAND/03 - The Devil In The Row.md +1 |

## Detalhe por snippet


### bside.css

Classes: b-sides-script.

Callouts: —.

Seletores/atributos: —.

Notas afetadas: DISGRACELAND/01 - Main Event Shadows.md, DISGRACELAND/02 - Ghosts On The Waves.md, DISGRACELAND/03 - The Devil In The Row.md.

Amostra:

```css
/* B-Sides from the End Times: Script Styling */

.b-sides-script {
  --b-sides-bg: #111416;
  --b-sides-accent: #b22d2d;
  --b-sides-muted: #888;
  --b-sides-font: 'Atkinson Hyperlegible Next', monospace;

  background-color: var(--b-sides-bg);
  color: #e3e3e3;
  font-family: var(--b-sides-font);
  padding: 2rem;
  border: 1px solid var(--b-sides-accent);
  box-shadow: 0 0 20px rgba(178, 45, 45, 0.3);
  border-radius: 8px;
  line-height: 1.6;
```

### dgl.css

Classes: calendar, calendar-title, callout, callout-icon, callout-stack, callout-title, centered-img, character-box-right, cm-header, console-callout-grid, console-grid, dataview, inline-title, internal-link, is-clean, is-right, markdown-preview-view, metadata-container, nav-row, result-group-title.

Callouts: info, note, tip, todo.

Seletores/atributos: [data-callout="info"], [data-callout="note"], [data-callout="tip"], [data-callout="todo"].

Notas afetadas: .trash/Call Out Boxes/Call Out Boxes.md, .trash/Call Out Boxes/Call Out - Call Out Box.md, .trash/Call Out Boxes/Call Out - Read Aloud.md, .trash/Call Out Boxes/Call Out - Flavor.md +2.

Amostra:

```css

.callout {
  background-color: #1f2329; /* steel grey */
  border-left: 4px solid #5e6b75; /* muted steel blue accent */
  color: #d0d5dc; /* cool, light steel text */
  border-radius: 6px;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.4);
}

.callout-title {
  background-color: #2a2f36; /* darker steel tone for header */
  color: #e0e4e9;
  font-weight: 600;
  border-bottom: 1px solid #3b424a;
}
```

### disgraceland-profile.css

Classes: com, disgraceland-profile, googleapis, region-ashmoor, region-charspire, region-drownlands, region-gutterrow, region-steeltown, region-threshton.

Callouts: —.

Seletores/atributos: [class^="region-"].

Notas afetadas: —.

Amostra:

```css
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@400;700&display=swap');

/* ───────────── CHARACTER PROFILE ───────────── */
.disgraceland-profile {
  background-color: #1a1a1a;
  color: #f8f8f2;
  border: 2px solid #ff6600;
  padding: 1.5rem;
  border-radius: 8px;
  font-family: 'Raleway', sans-serif;
  line-height: 1.6;
}

.disgraceland-profile h1 {
  color: #ffcc00;
  border-bottom: 2px solid #ff6600;
```

### fullstat.css

Classes: obsidian-vault-full-statistics--item.

Callouts: —.

Seletores/atributos: —.

Notas afetadas: —.

Amostra:

```css
/* Show all vault statistics. */
.obsidian-vault-full-statistics--item {
    display: initial !important;
}
```

### hrline.css

Classes: homepage.

Callouts: —.

Seletores/atributos: —.

Notas afetadas: DISGRACELAND/DISGRACELAND.md, Home.md.

Amostra:

```css
.homepage hr {
  border: none;
  border-top: 2px solid #8D9DB5;
  margin-top: 1.5rem;
  margin-bottom: 1.5rem;
  animation: pulse-glow 1.5s infinite ease-in-out;
  box-shadow: 0 0 4px #8D9DB5;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 4px #8D9DB5;
    opacity: 1;
  }
  50% {
    box-shadow: 0 0 12px #8D9DB5;
```

### htc.css

Classes: datacards-card.

Callouts: —.

Seletores/atributos: —.

Notas afetadas: —.

Amostra:

```css
.datacards-card {
  color: #ffffff; /* ← Change to any color you want */
}
```

### scriptwrite.css

Classes: disgraceland-script.

Callouts: —.

Seletores/atributos: —.

Notas afetadas: .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 01.md, .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 02.md, .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 03.md.

Amostra:

```css
/* Disgraceland Script Mode — Grey with Gold Accents */
.disgraceland-script {
  --font-mono: 'Courier New', Courier, monospace;
  --bg-grey: #1e1e1e;
  --bg-softer: #2a2a2a;
  --text-white: #f7f7f7;
  --accent-gold: #d4af37;
  --accent-muted: #555;

  background-color: var(--bg-grey);
  color: var(--text-white);
  font-family: var(--font-mono);
  padding: 2rem;
  line-height: 1.7;
  letter-spacing: 0.04em;
  border-left: 4px solid var(--accent-gold);
```

### supercharged-links-gen.css

Aviso: arquivo gerado automaticamente/sobrescrito; não editar diretamente.
Classes: c-15ae-9b1f-use-background, c-287d-312f-use-background, c-3623-52e1-use-background, c-4740-17da-use-background, c-6e9a-b654-use-background, c-7457-fe20-use-background, c-7e5f-283b-use-background, c-7eac-9a5f-use-background, c-9cd0-d420-use-background, c-ce91-5784-use-background, c-e2c5-b197-use-background, c-e997-0713-use-background, c-f884-7b00-use-background, data-link-icon, data-link-icon-after, data-link-text, setting-item-description.

Callouts: —.

Seletores/atributos: [data-id="15ae-9b1f"], [data-id="287d-312f"], [data-id="3623-52e1"], [data-id="4740-17da"], [data-id="6e9a-b654"], [data-id="7457-fe20"], [data-id="7e5f-283b"], [data-id="7eac-9a5f"], [data-id="9cd0-d420"], [data-id="ce91-5784"], [data-id="e2c5-b197"], [data-id="e997-0713"], [data-id="f884-7b00"], [data-link-tags*="individual" i], [data-link-tags*="lore" i], [data-link-tags*="loyalist" i], [data-link-tags*="murray" i], [data-link-tags*="pirate" i], [data-link-tags*="rancher" i], [data-link-tags*="religion" i].

Notas afetadas: —.

Amostra:

```css
/* WARNING: This file will be overwritten by the plugin.
Do not edit this file directly! First copy this file and rename it if you want to edit things. */

:root {
    --ce91-5784-color: #9270D3;
    --ce91-5784-weight: initial;
    --ce91-5784-before: '';
    --ce91-5784-after: '';
    --ce91-5784-background-color: #ffffff;
    --ce91-5784-decoration: initial;
    --f884-7b00-color: #FF9671;
    --f884-7b00-weight: initial;
    --f884-7b00-before: '';
    --f884-7b00-after: '';
    --f884-7b00-background-color: #ffffff;
    --f884-7b00-decoration: initial;
```

### test.css

Classes: expand-button, news-box, news-full, news-preview, news-toggle.

Callouts: —.

Seletores/atributos: —.

Notas afetadas: Legacy - Disgraceland Scratch Notes.md, Workflow/Scratch Notes.md +8.

Amostra:

```css
.news-box {
  background-color: var(--background-primary);
  border: 1px solid var(--color-base-30);
  border-radius: 8px;
  padding: 10px;
  margin-top: 10px;
  position: relative;
  font-size: 0.9rem;
}

.news-preview,
.news-full {
  font-family: Atkinson Hyperlegible Next;
  white-space: pre-wrap;
  line-height: 1.5;
}
```

### titlehide.css

Classes: markdown-preview-view.

Callouts: —.

Seletores/atributos: —.

Notas afetadas: —.

Amostra:

```css
/* Hide the centered title at the top of the page */
.markdown-preview-view h1:first-of-type {
  display: none;
}
```

### topnav.css

Classes: top-nav.

Callouts: —.

Seletores/atributos: —.

Notas afetadas: —.

Amostra:

```css
.top-nav {
  background-color: #333942;
  padding: 10px 20px;
  text-align: center;
  border-bottom: 2px solid #444;
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  justify-content: center;
  gap: 30px; /* controls spacing between items */
}

.top-nav a {
  color: #ddd;
  text-decoration: none;
```

### videopop.css

Classes: callout, video-container, video-popup, video-wrapper.

Callouts: video.

Seletores/atributos: [data-callout="video"].

Notas afetadas: —.

Amostra:

```css
.callout[data-callout="video"] {
    max-width: 700px;
    margin: 20px auto; /* centers horizontally */
    padding: 15px;
    background-color: #222;
    border: 2px solid #555;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0,0,0,0.7);
    display: block; /* ensure block behavior */
}



/* Base popup */
.video-container {
  position: relative;
```

### world.css

Classes: callout, callout-icon, callout-title.

Callouts: home, news, world.

Seletores/atributos: [!news], [data-callout="home"], [data-callout="news"], [data-callout="world"].

Notas afetadas: Home.md, Legacy - Disgraceland Scratch Notes.md, Workflow/Scratch Notes.md, DISGRACELAND/01 - Main Event Shadows.md, DISGRACELAND/02 - Ghosts On The Waves.md, DISGRACELAND/03 - The Devil In The Row.md +1.

Amostra:

```css
/* === [!news] Custom Callout === */
.callout[data-callout="news"] {
  --callout-color: 45, 52, 64; /* Deep charcoal */
  --callout-bg-color: rgba(53, 60, 69, 0.9); /* Rich dark background */
  background-color: var(--callout-bg-color);
  color: #dddddd;
}

.callout[data-callout="news"] .callout-title {
  font-weight: bold;
  text-transform: uppercase;
  color: #ffffff;
}

.callout[data-callout="news"] .callout-icon {
  display: flex;
```

## Callouts detectados

| callout | ocorrências | modificadores | arquivos exemplo | função visual inferida |
| --- | --- | --- | --- | --- |
| [[eo.png\ | 1 | sban htiny ctr (1) | Home.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| [[mapp.png\ | 1 | sban htiny ctr (1) | Home.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| [[news1.png\ | 1 | sban htiny ctr (1) | Home.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| [[sool.png\ | 1 | sban htiny ctr p+t (1) | Home.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| [[t2.png\ | 1 | sban htiny ctr (1) | Home.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| abstract | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| bug | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| cards | 1 | 5 (1) | Home.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| charspire | 2 | toggle (2) | Legacy - Disgraceland Scratch Notes.md, Workflow/Scratch Notes.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| column | 11 | — | .trash/City Forces/Blueforce.md, Factions/Third Row.md, Lore/Blackshift Massacre.md, Lore/Darrell Douglass.md, Lore/Final Force.md, Lore/Galliah, the Stillborn Star.md, Lore/Night Time with Morris Gable.md, Lore/The Wanderers.md, Lore/Transportation.md, Lore/Water Wars.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| danger | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| example | 2 | — | .trash/Call Out Boxes/Call Out - Magic Item.md, .trash/Call Out Boxes/Call Out Boxes.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| failure | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| hollow | 1 | — | Locations/Hollow House.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| home | 1 | — | Home.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| info | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| infobox | 19 | left (1) | .trash/Call Out Boxes/Call Out - Left Section.md, .trash/Call Out Boxes/Call Out - Right Section.md, Characters/Individual/Cassidy LaRue.md, Characters/Individual/Kullen Dane.md, Characters/Individual/Salem Quinn.md, Characters/Individual/Shana.md, Characters/Individual/The Grim Man.md, Characters/Rancher Collective/Turner Anderson.md, Characters/Rustwater Raiders/Silas Vayne.md, Characters/Steeltown Wrecking Crew/Katie Kowalski.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| news | 3 | — | Home.md, Legacy - Disgraceland Scratch Notes.md, Workflow/Scratch Notes.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| note | 125 | clean no-i right (119) | .trash/Call Out Boxes/Call Out Boxes.md, Characters/Rancher Collective/Freddy Blanchard.md, Home.md, .trash/Call Out Boxes/Call Out - Call Out Box.md, .trash/Call Out Boxes/Call Out - Read Aloud.md, Characters/Individual/Ava Victoria.md, Characters/Individual/Bastian Redd.md, Characters/Individual/Bobby Cutman.md, Characters/Individual/Cassidy LaRue.md, Characters/Individual/Dusty Dillon.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| question | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| quote | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| rustwater | 2 | — | Characters/Individual/Cassidy LaRue.md, Characters/The Elite & Loyalist Guard/Emily Burton.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| success | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| tip | 2 | — | .trash/Call Out Boxes/Call Out - Flavor.md, .trash/Call Out Boxes/Call Out Boxes.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| warning | 4 | — | .trash/Call Out Boxes/Call Out - GM Direction.md, .trash/Call Out Boxes/Call Out Boxes.md, Legacy - Disgraceland Chapter 01 - Ghosts on the Waves.md, Lore/Tetra Bomb.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |
| world | 12 | — | DISGRACELAND/DISGRACELAND.md, DISGRACELAND/01 - Main Event Shadows.md, DISGRACELAND/02 - Ghosts On The Waves.md, DISGRACELAND/03 - The Devil In The Row.md, DISGRACELAND/04 - Glowing Darkness.md, DISGRACELAND/05 - Sight Unseen.md, DISGRACELAND/06 - Showdown In Gage Park.md, DISGRACELAND/07 - The Spotlight Lies.md, DISGRACELAND/08 - No Answers.md, Home.md | cards/dashboard/retrato/bloco visual; confirmar no snippet correspondente |