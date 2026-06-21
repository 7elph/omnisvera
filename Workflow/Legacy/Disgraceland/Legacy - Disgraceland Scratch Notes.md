

```datacards 
TABLE cover, date, description FROM #chapter
SORT name ASC

// Settings 
preset: grid 
columns: 5 
imageProperty: cover
```



> [!news]+ TODAY'S NEWS
> <div class="news-box">
>   <pre class="news-preview">
> - A fisherman on the docks in [[Steeltown#Gage Park|Gage Park]] is packing up for the day when he notices [[The Black Marauder]] approaching on the [[Water#Rustwater Bay|Rustwater Bay]]
> - After warning people the fisherman begins running for the [[Steeltown Wrecking Crew]] clubhouse.
> - Aboard [[The Black Marauder]], [[Lyla Bonetooth]] and [[Blacktide Cray]] decide to anchor the ship and take a dingy into land, just the two of them, waving a white flag in hopes [[Jimmy Douglass]] does not attack.
> - The fisherman makes it to the [[Steeltown Wrecking Crew|Wrecking Crew]] clubhouse and informs them of [[The Black Marauder]].
> - The [[Steeltown Wrecking Crew|Wrecking Crew]] prepare and ride out to the [[Steeltown#Gage Park|Gage Park]] docks.
> - At the docks the [[Steeltown Wrecking Crew|Wrecking Crew]] send the public away and decide [[Jimmy Douglass]], [[Mark Jeffrey]] & [[Abel May Jr.]] will do down to speak with [[Lyla Bonetooth]] and [[Blacktide Cray]].
> - [[Abel May Jr.|Abel]] tells [[Jimmy Douglass|Jimmy]] & [[Mark Jeffrey|Mark]] about [[Flint Garritt]] offering him a contract and inviting him to Final Reckoning. [[Jimmy Douglass|Jimmy]] says [[Abel May Jr.|Abel]] shouldn't go alone.
>   </pre>
> 
>   <input type="checkbox" id="toggle-news" class="news-toggle">
>   <label for="toggle-news" class="expand-button">+ Expand full story</label>
> 
>   <pre class="news-full">
> - [[Jimmy Douglass]] and [[Abel May Jr.]]meet [[Lyla Bonetooth]] and [[Blacktide Cray]] on the shores of [[Steeltown#Gage Park|Gage Park]].
> - [[Lyla Bonetooth|Lyla]] and [[Jimmy Douglass|Jimmy]] are cordial while Abel and Blacktide glare at each other.
> - [[Lyla Bonetooth|Lyla]] tells [[Jimmy Douglass|Jimmy]] about the slaves. [[Lyla Bonetooth|Lyla]] tells [[Jimmy Douglass|Jimmy]] she wants the Wrecking Crew to take the slaves.
> - [[Jimmy Douglass|Jimmy]] says if he takes the slaves he will free them and The Duke will know the Rustwater Raiders didn't deliver the slaves. Lyla says she knows.
> - [[Jimmy Douglass|Jimmy]] introduces [[Mark Jeffrey]] to [[Lyla Bonetooth|Lyla]]. 
> - [[Mark Jeffrey|Mark]] and [[Lyla Bonetooth|Lyla]] instantly hit it off.
> - The [[Steeltown Wrecking Crew|Wrecking Crew]] takes the slaves as [[Katie Kowalski]] fangirls over [[Lyla Bonetooth|Lyla]].
> - [[Mark Jeffrey|Mark]] tells [[Lyla Bonetooth|Lyla]] the [[Steeltown Wrecking Crew|Wrecking Crew]] will protect her from [[Loyalist Guard|Loyalist]]retaliation.
> - The [[Rustwater Raiders|Raiders]] and [[Steeltown Wrecking Crew|Wrecking Crew]] go their separate ways on amicable terms. Although [[Blacktide Cray]] still wants to fight [[Abel May Jr.]].
> - Far away from [[Steeltown]], in the canyons of [[Threshton]], [[Bastian Redd]] is training for the fight. [[Flint Garritt]]appears and offers [[Bastian Redd|Redd]] loaded gloves. [[Bastian Redd|Redd]] declines to cheat.
>   </pre>
> </div>

```dataviewjs
const preview = `
> A fisherman in [[Steeltown#Gage Park|Gage Park]] spots [[The Black Marauder]]...
> The [[Wrecking Crew]] are alerted and prepare to ride...
> [[Abel May Jr.|Abel]] tells [[Jimmy Douglass|Jimmy]] and [[Mark Jeffrey|Mark]] about [[Flint Garritt]]'s offer...
`;

const full = `
> [[Jimmy Douglass]] and [[Abel May Jr.]] meet [[Lyla Bonetooth]]...
> [[Katie Kowalski]] fangirls over [[Lyla Bonetooth]]...
> [[Bastian Redd]] trains in the canyons of [[Threshton]]...
`;

const container = this.container;

// Create root div
const wrapper = document.createElement("div");
wrapper.classList.add("news-box");

// PREVIEW
const previewDiv = document.createElement("div");
previewDiv.classList.add("news-preview");
await MarkdownRenderer.renderMarkdown(preview, previewDiv, "", this.app);
wrapper.appendChild(previewDiv);

// TOGGLE
const toggle = document.createElement("input");
toggle.type = "checkbox";
toggle.id = "toggle-news";
toggle.classList.add("news-toggle");
wrapper.appendChild(toggle);

const label = document.createElement("label");
label.setAttribute("for", "toggle-news");
label.classList.add("expand-button");
label.innerText = "+ Expand full story";
wrapper.appendChild(label);

// FULL CONTENT
const fullDiv = document.createElement("div");
fullDiv.classList.add("news-full");
await MarkdownRenderer.renderMarkdown(full, fullDiv, "", this.app);
wrapper.appendChild(fullDiv);

// Inject all into the container
container.appendChild(wrapper);

```

```datacards
TABLE thumbnail, location, status FROM #character
SORT file.mtime desc
limit 6

// Settings
preset: square
columns: 6
imageProperty: thumbnail
```

```dataviewjs
const classList = dv.current().cssclasses ?? [];
const characterSlugs = classList.filter(c => c.startsWith("character/")).map(c => c.replace("character/", ""));

dv.el("div", "", { cls: "character-gallery" });

for (let slug of characterSlugs) {
    const file = dv.page(`Characters/${slug}`);
    if (!file) continue;

    const displayName = file.file.name
        .split("-").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ")
        .replace("Jr", "Jr.");  // Small formatting nicety

    const img = `<img src="/vault/path/to/thumbnails/th_${slug}.png" alt="${displayName}" />`;
    const name = `<div class="character-name">${displayName}</div>`;

    dv.el("div", img + name, { cls: "character-card" });
}
```



<audio controls autoplay>
<source src="burn.mp3" type="audio/mpeg">
Your browser does not support the audio element.
</audio>

> [!charspire|toggle]-  Main Characters
> ```dataview
> table 
>   "<img src='" + thumbnail + "' width='60' style='border-radius:5px;box-shadow:0 0 4px rgba(255, 102, 0, 0.5);' />" as "Portrait", 
>   location, status, faction, religion
> from "Characters"
> where contains(tags, "character") and contains(tags, "main")
> sort file.name asc
> ```


## [[01 - Main Event Shadows]] 

<div style="float: left; margin-right: 15px; width: 200px;">
  <img src="abevsbob.png" width="200" style="border: 3px solid black;">
</div>

When the [[World Lucha Libre|WLL]] brings its blood-soaked spectacle to [[Steeltown]], tensions explode as undefeated champion **[[Bobby Cutman|Bobby “The Iron Bull” Cutman]]** disrespects the crowd, the city, and the **[[Steeltown Wrecking Crew]]**. As security duty turns personal, **[[Abel May Jr.]]** steps up and steals the spotlight, triggering a ferocious standoff that nearly ignites a riot. But while the world watches [[Bobby Cutman]] rage, a shadowy offer is made. 

And behind the scenes, something far more dangerous is watching everything from the dark. 

---

## [[02 - Ghosts On The Waves]]

<div style="float: left; margin-right: 15px; width: 200px;">
  <img src="lyladuke.png" width="200" style="border: 3px solid black;">
</div>

When [[Lyla Bonetooth]] and the [[Rustwater Raiders]] are summoned to [[The Silo]] in [[Ashmoor]] for a secret job, they’re ordered to smuggle a high-value prisoner to [[Steeltown]] — but the “prisoner” turns out to be something else entirely. As tensions rise aboard [[The Black Marauder]], Lyla must decide whether to complete the job or risk everything by defying [[The Duke]]. 

Meanwhile, a chilling vision haunts the [[Unseen Widows]]: a glimpse of the horrors still to come.

---

## [[03 - The Devil In The Row]]

<div style="float: left; margin-right: 15px; width: 200px;">
  <img src="03.png" width="200" style="border: 3px solid black;">
</div>

When two off-duty [[Loyalist Guard]]s in [[Gutter Row]] take their drunken power trip too far behind [[Hollow House]], they come face to face with a shadow the city guard pretends doesn’t exist. As [[Shana]] fights for survival, a chain rings through the alley, and with it, [[The Grim Man]] delivers his silent judgment. Blood hits brick, legend becomes real, and a quiet pact is sealed in the dark.

And somewhere else in [[Steeltown]], a message is delivered. Not everyone welcomes it.

---

## [[04 - Glowing Darkness]]

<div style="float: left; margin-right: 15px; width: 200px;">
  <img src="04.png" width="200" style="border: 3px solid black;">
</div>

[[Lash Hawkins]] breaks from the [[Murray Boys]], revealing his own potent [[Luxyn]] supply and igniting a dangerous feud with [[Nico Murray]]. After publicly humiliating Nico in the streets of [[Gutter Row]], Nico returns home and informs his family, [[Marco Murray]] and [[Rosa Murray]] of Lash's decisions. Meanwhile, Lash sets out to expand his empire—but a quiet street and a pale stranger bring his rise in the [[Luxyn]] game to a sudden, chilling stop.

Elsewhere in [[Ashmoor]], private meetings are held and plans are discussed.

---

## [[05 - Sight Unseen]]

<div style="float: left; margin-right: 15px; width: 200px;">
  <img src="05.png" width="200" style="border: 3px solid black;">
</div>

In the fog-choked wilds of [[The Drownlands]], twin hunters [[Raina & Risa|Raina]] and [[Raina & Risa|Risa]] complete the sacred rite to become Unseen, pledging their lives to the goddess [[Faith of Mirella|Mirella]]. With [[Riley Thorne]] guiding them, they embark on their quest to become Widows and find an unlikely first kill.

Meanwhile, far from the mire, [[Ava Victoria]] searches the chaos of [[Gutter Row]] for the vanished [[Lash Hawkins]], forcing an uneasy alliance with [[Nico Murray]] as shadows gather and secrets deepen.

---



# Chronos Cheatsheet

After installing the Chronos Timeline plugin for Obsidian, copy and paste this whole markdown file into a file in your vault to play around and learn the syntax.

Hover on a timeline and click the Edit button in the upper right to play with the data.

## Date formats

Chronos can visualize dates from the year down to the second level, using the syntax `YYYY-MM-DDThh:mm:ss`.

The only required component of a date is the year (`YYYY`). Beyond that, you can specify additional time granularity as needed for your use case.

If not explicitly provided:

- The month and day default to `01` (January and the 1st)
- The hour, minute, and second default to `00` (top of the hour or minute)

### Examples

```chronos
- [2020] A year
- [2020-02] A month
- [2020-02-28] A day
- [2020-02-28T12] An hour
- [2020-02-28T12:30] A minute
- [2020-02-28T12:30:09] A second
```

## Events

**Full Syntax**

```
- [Date~Date] #Color {Group Name} Event Name | Description
```

- The second Date, Color, Group Name, Event Name, and Description are optional
- Description appears when you hover on an event in the timeline

### Examples

#### Single Date

**Syntax**

```
- [Date] Event Name
```

```chronos
- [1879-03-14] Einstein born
```

#### Date range

**Syntax**

```
- [Date~Date] Event Name
```

```chronos
- [1991~2001] Time I believed in Santa
```

#### Date range with description

**Syntax**

```
- [Date~Date] Event Name| Description
```

```chronos
- [1991~2001] Time I believed in Santa | ended when my brother tried to videotape Santa with a hidden camera
```

#### With color

See available [Colors](#colors)

**Syntax**

```
- [Date~Date] #Color Event Name| Description
```

```chronos
- [2001~2009] #red Bush
- [2009~2017] #blue Obama
- [2017~2021] #red Trump
- [2021~2025] #blue Biden
```

#### With groups

**Syntax**

```
- [Date(~Date)] {Group Name} Event Name| Description
```

```chronos
@ [1892-10-08~1941-08-31] {Marina Tsvetaeva} 1892-1941
- [1916] {Marina Tsvetaeva} "Подруга"
- [1928] {Marina Tsvetaeva}  "Поэма концов"
- [1941] {Marina Tsvetaeva} "Записки о поэзии"

@ [1899-08-24~1986-06-14] {Jorge Luis Borges} 1899-1986
- [1944] {Jorge Luis Borges} "Ficciones"
- [1949] {Jorge Luis Borges} "El Aleph"
- [1962] {Jorge Luis Borges} "Labyrinths"

```

## Periods

**Full Syntax**

```
@ [Date~Date] #Color {Group Name} Period Name
```

- Color, Group Name, and Period Name are optional

### Examples

#### Basic

```chronos
@ [-300~250] Yayoi Period
- [-100] Introduction of rice cultivation
- [-57] Japan’s first recorded contact with China
```

#### With color

See available [Colors](#colors)

```chronos
@ [-300~250] #red Yayoi Period
- [-100] Introduction of rice cultivation
- [-57] Japan’s first recorded contact with China

@ [250~538] Kofun Period
- [250] Construction of keyhole-shaped kofun burial mounds begins
- [369] Yamato state sends envoys to Korea
```


## Points

**Syntax**

```
* [Date] Point Name | Description
```

```chronos
- [2024-02-26~2024-03-10] Tournament
* [2024-02-26] Game 1 | Austin
* [2024-02-28] Game 2 | Los Angeles
* [2024-03-06] Game 3 | Tokyo
* [2024-03-10] Game 4 | Jakarta
```

## Markers

**Syntax**

```
= [Date] Marker Name
```

### Examples

```chronos
= [1440] Invention of the Gutenberg Press

- [1455] Gutenberg Bible Printed
@ [1501~1600] The Spread of Printing
- [1517] Martin Luther's 95 Theses
```

## Advanced example

```chronos
- [1945-07-17] {Europe} Potsdam Conference | where post-WWII Europe is divided
- [1947-03-12] {USA} Truman Doctrine | committing the U.S. to containing communism
- [1948-06-24~1949-05-12] {Europe} Berlin Blockade | and Airlift in response to Soviet actions in Berlin
- [1949-04-04] {Europe} Formation of NATO

# Early Cold War

@ [1957~1969] #cyan {USSR} Space Race
@ [1957~1969] #cyan {USA} Space Race
- [1950-06-25~1953-07-27] {Asia} Korean War | between North and South Korea
- [1955-05-14] {USSR} Warsaw Pact | in response to NATO
- [1957-10-04] #cyan {USSR} Sputnik launched | initiating the Space Race
- [1961-04-17] {Cuba} Bay of Pigs Invasion | in Cuba

# Height of Tensions

- [1962-10-16] {Cuba} Cuban Missile Crisis | a peak confrontation between the U.S. and USSR
- [1963-08-05] {Global} Partial Nuclear Test Ban Treaty signed
- [1969-07-20] #cyan {USA} Apollo 11 Moon landing | U.S. wins the Space Race
- [1972-05-26] {Global} SALT I signed | first Strategic Arms Limitation Treaty

# Détente Period

- [1979-12-24~1989-02-15] {USSR} Soviet-Afghan War | straining Soviet resources
- [1983-03-23] {USA} Reagan announces the Strategic Defense Initiative (SDI)
- [1986-04-26] {USSR} Chernobyl nuclear disaster
- [1987-12-08] {Global} INF Treaty | signed, eliminating intermediate-range nuclear missiles

# Late Cold War

- [1989-11-09] {Europe} Fall of the Berlin Wall | symbolizing the end of Cold War tensions
- [1991-07-31] {Global} START I Treaty signed | further arms reduction
- [1991-12-26] {USSR} Dissolution of the Soviet Union | officially ending the Cold War

= [1991-12-26] End of the Cold War

```

## Ordering

**Order by start date**

```chronos
> ORDERBY start

- [2026~2028] Event D
- [2024~2028] Event B
- [2025~2030] #red Event C
- [2020~2030] #red  Event A
```

**Order by start (descending)**

```chronos
> ORDERBY -start

- [2026~2028] Event D
- [2024~2028] Event B
- [2025~2030] #red Event C
- [2020~2030] #red  Event A
```

**Order by color and start**

```chronos
> ORDERBY color|start

- [2026~2028] Event D
- [2024~2028] Event B
- [2025~2030] #red Event C
- [2020~2030] #red  Event A
```

## Default view dates

Use the `> DEFAULTVIEW start|end` flag to specify default start and end dates for your timeline's initial load

```chronos
> DEFAULTVIEW  -3000|3000

- [2024] AGI
```

## Colors

- `#red`
- `#orange`
- `#yellow`
- `#green`
- `#blue`
- `#purple`
- `#pink`
- `#cyan`
