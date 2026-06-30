# Etapa 1 — Padrão de Lore, História e Cultura

## Objetivo

Criar uma camada de formatos para Omnisvera inspirada na disposição técnica do Disgraceland, sem copiar conteúdo narrativo, vocabulário antigo ou estrutura operacional legada.

Disgraceland continua sendo referência de **gramática visual**:

- página-mãe com sinopse;
- capítulos com capa, data, descrição e elenco;
- B-Sides como histórias paralelas/de origem;
- lore mítica com imagem, origem e conexão com o presente;
- dossiês de eventos/fenômenos com classificação, efeitos e legado;
- religião e cultura como índices úteis para consulta.

Omnisvera mantém seu próprio motor:

- português BR;
- `visibility`;
- `spoiler_level`;
- `gm_secret`;
- `chapters`;
- `thumbnail`;
- `cover`;
- tags Omnisvera;
- Home dos Jogadores pública;
- Home/Estado da Campanha para mestre.

## Arquivos criados nesta etapa

| arquivo | função |
|---|---|
| `Templates/RPG/Lore.md` | Template para mito, entidade, conceito cosmológico, tradição antiga ou lore geral. |
| `Templates/RPG/Fenômeno.md` | Template para fenômeno, evento histórico, ruptura, catástrofe ou dossiê de mistério. |
| `Templates/RPG/Cultura.md` | Template para cultura, costumes, sociedades, festivais e comportamento social. |
| `Templates/RPG/Religião.md` | Template para religião, culto, tradição espiritual ou fé organizada. |

## Padrões herdados como forma, não como conteúdo

### Lore mítica

Referência formal: notas como `Valkaara`.

Adaptação Omnisvera:

- `Sinopse Pública`;
- `Fundamento`;
- `O que se Sabe`;
- `Conexão com o Presente`;
- `Sinais, Frases e Registros`;
- `Segredos do Mestre`;
- `Uso em Mesa`;
- `Pendências do Sage`.

### Fenômeno ou evento

Referência formal: notas como `Tetra Bomb`.

Adaptação Omnisvera:

- bloco de classificação;
- origem;
- manifestação;
- efeitos em tabela;
- consequências históricas;
- conexão com a campanha atual;
- segredos do mestre;
- uso em mesa.

### Cultura

Referência formal: `CULTURE.md` do Disgraceland como dashboard de categorias.

Adaptação Omnisvera:

- cultura como ferramenta de mesa;
- categorias só devem virar consulta ativa quando existirem notas reais;
- manter rascunhos e categorias futuras separados do cânone.

### Religião

Referência formal: `RELIGION.md` do Disgraceland como índice comparativo.

Adaptação Omnisvera:

- crenças centrais;
- práticas;
- símbolos;
- estrutura;
- influência;
- relações;
- segredos do mestre;
- uso em mesa.

## Próxima etapa recomendada

Aplicar estes padrões primeiro nos arquivos-mãe, sem reescrever a lore inteira:

1. `CULTURE.md`;
2. `Religion/RELIGION.md`;
3. `TIMELINE.md`;
4. `CALENDAR.md`;
5. `Lore/Criadores.md`;
6. `Lore/Véu Cinzento.md`;
7. `Lore/Sangue Antigo.md`.

Depois disso, fazer o pente fino completo da pasta `Lore/`, separando:

- lore pública;
- rumor;
- segredo do mestre;
- fenômeno;
- mito;
- evento histórico;
- religião/culto;
- pendência narrativa.

## Cuidados

- Não transformar rascunho em cânone sem validação.
- Não mover spoiler para nota pública.
- Não copiar nomes, facções ou tom do Disgraceland.
- Não criar dashboards vazios com tags que ainda não têm notas.
- Não remover conteúdo já construído; reorganizar antes de resumir ou cortar.
