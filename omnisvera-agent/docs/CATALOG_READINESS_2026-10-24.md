# Prontidão dos catálogos — primeiro corte determinístico (24/10/2026)

## Escopo

Inventário somente-leitura de `monster_catalog`/`monster_actions`,
`spell_catalog`/`spell_engine` e `item_catalog`. O módulo
`backend/app/catalog_readiness.py` expõe `build_catalog_readiness()` e devolve
contadores, listas completas, fontes/edições, imagens, famílias e lacunas.
Não cria regras, estoque, preços, NPCs, canon ou endpoints. Não executa ações.
`automation_status` é sempre `not_certified`: classificação não é prova de
automação nem de aceitação visual.

## Contagens reais (loaders locais)

| Catálogo | Total | Edição | Observação |
| --- | ---: | --- | --- |
| Monstros | 255 | OD2 | SRD Old Dragon 2 |
| Magias | 854 | OD2 | Tomos arcano/divino |
| Itens | 326 | OD1 | Livro Básico Aprimorado + expansão compatível |

### Monstros

- 147 com vínculo de imagem no manifesto; 108 sem vínculo. Isso **não prova**
  arquivo disponível nem retrato exclusivo. São vínculos de catálogo externo,
  separados de uploads do Mestre e de arte gerada. O Mestre confirmou somente
  Goblin como upload de monstro e um retrato falado de dragão no Vault como
  referência; essa referência não foi atribuída a todos os dragões.
- 247 com ataques; 8 sem ataques; 365 ataques, 322 prontos e 43 incompletos.
- 14 com baforada/sopro; 23 com conjuração; 16 conjuradores sem repertório
  nomeado no catálogo.
- 183 sem lacunas bloqueantes; 72 com alguma lacuna bloqueante.
- Movimento separado em terrestre, voo (`V`), natação (`N`), escalada (`E`) e
  escavação (`C`), conforme notação declarada.
- Destaques: **Grifo** tem mordida/garras prontas e nenhuma conjuração ou
  baforada declarada; **Dragão Dourado** tem mordida/garras, baforada
  `11d10`/JPD/cone 9×27 m/3× ao dia e conjura “como Mago de 7º nível”, mas o
  catálogo **não declara o repertório de magias** — a lacuna é registrada sem
  inventar magias.

### Magias

| Família | Total |
| --- | ---: |
| próprio | 126 |
| toque | 175 |
| alvo | 177 |
| multi-alvo | 19 |
| área/linha/cone | 194 |
| passiva/assistida | 163 |

- 504 têm mecânica genérica derivável pelo `spell_engine` (JP/dano/alcance);
  350 ficam `manual_only` por falta de mecânica estruturada.
- Custo declarado no texto: 33; recarga declarada: 3. O catálogo não traz custo
  ou recarga estruturados para a maioria; isso é lacuna de dados, não regra nova.
- Todas as 854 entradas têm ao menos uma pendência objetiva (custo/recarga,
  alcance não estruturado, área textual ou handler ausente).

### Itens

| Bucket | Total |
| --- | ---: |
| equipamento | 151 |
| consumível | 37 |
| item mágico | 111 |
| serviço | 15 |
| transporte/montaria | 6 |
| mercadoria/ativo | 6 |

- 198 entradas concretas e 128 fragmentos de tabela (não são itens compráveis).
- 14 sem preço; 142 com alguma pendência.
- Sugestões de distribuição por bucket são apenas indicação de tipo de
  comerciante/local; não criam estoque, NPC, preço ou canon.

## Regras determinísticas usadas

- Campos e textos dos próprios catálogos; sem rede, sem LLM e sem arquivos
  operacionais.
- Movimento por código `V/N/E/C`; ataques classificados por nome
  (mordida, garras, arma, distância).
- Família de magia por alcance e padrões textuais explícitos (cone, linha,
  esfera com medida, cubo, cilindro, multi-alvo, próprio, toque). Casos sem
  JP/dano ofensivo caem em passiva/assistida.
- Itens por categoria e, quando necessário, por “Usos”/palavras de consumo e
  por transporte/montaria versus imóvel.
- Edições preservadas: OD2 para monstros/magias, OD1 para itens. A expansão de
  itens permanece identificada pela fonte de cada entrada.

## Próximos adaptadores seguros

1. Expor o inventário em rota GM somente-leitura, sem tocar em endpoints
   operacionais.
2. Encaixar movimento e tipos de ataque no cadastro de token/inimigo, mantendo
   ataque incompleto como bloqueio explícito.
3. Parametrizar baforada (dano, JP, geometria, frequência) como configuração a
   preencher pelo Mestre, sem repertório inventado.
4. Mapear famílias de magia para o seletor de alvo existente, com fallback
   manual quando alcance/área não forem estruturados.
5. Usar os buckets de itens apenas como sugestão de oferta de comerciante;
   qualquer cadastro real continua exigindo revisão do Mestre.

## Verificação executada

```powershell
cd backend
..\.venv-observer\Scripts\python.exe -m unittest test_catalog_readiness -v
```

Resultado: `Ran 7 tests ... OK` (fixtures pequenas + contagens reais via
loaders locais).

## Riscos restantes

- Heurísticas de família de magia são inventário, não adjudicação; revisar
  casos de área versus alvo antes de qualquer automação.
- A ausência de custo/recarga e de área estruturada é limitação do catálogo,
  não autorização para preencher valores.
- O módulo não verifica arquivos de imagem no disco; “presente” significa
  vínculo no manifesto do catálogo.
- Não houve suíte completa, navegador, banco operacional ou alteração de
  fichas/catálogos.
