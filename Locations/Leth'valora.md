---
obsidianUIMode: preview
NoteIcon: lore
NoteStatus: New
status: 
territory: "[[Floresta de Avenor]]"
district:
info: O mais antigo reino élfico conhecido em Earthropo. Erguido entre florestas ancestrais e árvores tão antigas quanto a própria história registrada, Leth'valora é considerado por muitos o ápice da civilização élfica.
cover: zz_media/leth'valora.png   
tags:
- lore
- location
- elf   
- kingdom 
---

# [[LETH'VALORA]]

> [!NOTE|clean no-i right]+ ANTIGA ‎LETH'VALORA  
> ![[leth'valora.png|400]]

O mais antigo reino élfico conhecido em Earthropo.
Erguido entre florestas ancestrais e árvores tão antigas quanto a própria história registrada, Leth'valora é considerado por muitos o ápice da civilização élfica.
Suas cidades parecem ter sido moldadas pela própria natureza. Torres de mármore branco surgem entre árvores colossais, pontes vivas conectam distritos suspensos e rios cristalinos atravessam jardins encantados.
Por trás de sua beleza, porém, existe uma sociedade rígida e profundamente tradicionalista.
A pureza da linhagem é considerada uma virtude.
A tradição vale mais que a inovação.
E aqueles que nascem fora dos padrões esperados raramente encontram seu lugar.
Foi neste reino que [[Vezemir]] cresceu.
E foi também aqui que aprendeu que nem toda civilização é tão nobre quanto parece.

---

## Coração de Valora

Centro administrativo do reino.
Abriga o Conselho de Leth'valora, as residências das famílias e salões diplomáticos.

---

## Bosque das Estrelas

Uma floresta sagrada utilizada para cerimônias religiosas e rituais ancestrais.
Dizem que os primeiros elfos caminharam por estas terras.

---

## A Fortaleza

Antiga fortaleza militar localizada nas montanhas ao norte do reino.
Originalmente construída durante as Guerras Antigas para vigiar passagens estratégicas.
Foi abandonada após séculos de paz.
Mais tarde tornou-se o lar de [[Elarion Vaelthor]] e de seu pupilo, [[Vezemir]].
Atualmente seu estado é desconhecido.


---

## Conselho de Leth'valora

Órgão responsável pelo governo do reino.
Formado pelas principais famílias nobres élficas.

---

## [[Sentinelas de Leth'valora]]

Força militar responsável pela defesa das fronteiras.
Foi nesta organização que [[Elarion Vaelthor]] serviu durante séculos.

---

## Casas Nobres Élficas

Famílias aristocráticas que exercem influência política, econômica e militar.

---

```dataview
table location, status, faction
from "Characters"
where contains(lower(string(location)), "leth'valora")
limit 10
```