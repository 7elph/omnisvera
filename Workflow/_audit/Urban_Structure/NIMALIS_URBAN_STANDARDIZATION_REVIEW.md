# Pente Fino — Estrutura Urbana de Nimalis

## Objetivo

Padronizar a camada urbana de [[Nimalis]] sem criar lore política pesada nem alterar o mapa.

Esta etapa focou em:

- bairros raciais/culturais;
- zonas comerciais;
- porto;
- Casa da Moeda;
- leitura visual das notas;
- consistência com `Nimalis` como capital de `Nimalia`.

## Notas revisadas

| nota | função urbana | alteração aplicada |
|---|---|---|
| `Locations/Bairro dos Humanos.md` | Bairro/comunidade humana | Sinopse pública, imagem e tag `bairro`. |
| `Locations/Bairro dos Elfos.md` | Bairro/comunidade élfica | Sinopse pública, imagem e tag `bairro`. |
| `Locations/Bairro dos Anões.md` | Bairro/comunidade anã | Sinopse pública, imagem e tag `bairro`. |
| `Locations/Bairro dos Dragonborns.md` | Bairro/comunidade dragonborn | Sinopse pública, imagem e tag `bairro`. |
| `Locations/Bairro dos Forasteiros.md` | Bairro pobre/temporário | Sinopse pública, imagem e tag `bairro`. |
| `Locations/Bairro Nobre.md` | Zona nobre | Sinopse pública, imagem e tag `bairro`. |
| `Locations/Mercado Central.md` | Mercado público | Sinopse pública e imagem. |
| `Locations/Distrito Comercial.md` | Comércio especializado/sensível | Sinopse pública e imagem. |
| `Locations/Porto de Nimalia.md` | Porto da capital | Sinopse pública e imagem. |
| `Locations/Casa da Moeda de Nimalia.md` | Instituição econômica | Sinopse pública preservando imagens de exterior/interior. |

## Decisões consolidadas

### Bairros

- Bairros de Nimalis usam `location: [[Nimalis]]` e `territory: [[Nimalia]]`.
- Bairros receberam tag `bairro` quando a função era claramente bairro urbano.
- O mapa usado como imagem padrão continua `zz_media/mapa-de-nimalis.png`.

### Zonas comerciais

- `Mercado Central` = comércio cotidiano e público.
- `Distrito Comercial` = comércio especializado, caro, restrito ou moralmente perigoso.
- `Casa da Moeda de Nimalia` = instituição de cunhagem, impostos, moeda e possíveis falsificações.

### Porto

- `Porto de Nimalia` fica como porta de entrada/saída de cargas, rumores e contrabando.
- A relação com o [[Mar da Neblina]] foi preservada como origem de rumores e rotas incertas.

## Cuidados adotados

- Não foi criada liderança nova para nenhum bairro.
- Não foram definidos nomes de casas nobres.
- Não foram definidos mapas internos.
- Não foi suavizado nem expandido o tema sensível do Distrito Comercial; ele continua marcado com aviso.
- Não foi alterada a estrutura do mapa Leaflet.
- Não foi criada lore política nova.

## Pendências do Sage

1. Definir lideranças locais dos bairros.
2. Definir casas nobres principais do Bairro Nobre.
3. Definir autoridade portuária.
4. Definir se o porto é marítimo, fluvial ou ambos.
5. Definir lojas recorrentes no Mercado Central e Distrito Comercial.
6. Definir limite de conteúdo sensível para escravidão/comércio sombrio.
7. Definir se bairros terão pins próprios no mapa de Nimalis.
8. Definir relação formal entre Guilda dos Mercadores, Casa da Moeda e Coroa.

## Próxima etapa recomendada

Padronizar facções operacionais ligadas à cidade e ao reino:

1. `Factions/Coroa de Nimalia.md`;
2. `Factions/Nobreza de Nimalia.md`;
3. `Factions/Guarda Real de Nimalia.md`;
4. `Factions/Guilda dos Mercadores.md`;
5. `Factions/Conclave dos Errantes.md`;
6. `Factions/Rede de Falsificadores de Maré Baixa.md`.

Objetivo da próxima etapa:

- separar poder político, econômico, militar e criminoso;
- evitar que todas as facções urbanas façam a mesma coisa;
- preparar DataCards e ganchos de campanha.
