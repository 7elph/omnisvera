# Modelo Player-Safe de Entidades — Omnisvera

Este documento define como desenvolver notas de conteúdo no vault sem vazar bastidores da campanha.

## Regra central

Cada entidade deve ter uma nota principal completa, jogável e player-safe.

A nota principal mostra o mundo.

`CAMPANHA/ESTADO_DA_CAMPANHA.md` mostra a engrenagem por trás do mundo.

`Home_Mestre.md` funciona como painel de navegação, não como depósito de lore.

## Nota principal da entidade

Use a nota principal para:

- informação pública;
- descrição em cena;
- atmosfera;
- função em jogo;
- rumores sem confirmação final;
- ganchos sem resposta definitiva;
- relações conhecidas;
- links relevantes;
- pendências visíveis.

Não usar a nota principal para:

- culpado verdadeiro;
- plano secreto;
- resposta final de mistério;
- envolvimento real de NPC oculto;
- verdade canônica ainda não revelada;
- revelações futuras;
- decisões internas do mestre;
- spoiler pesado.

## Estado da Campanha

Use `CAMPANHA/ESTADO_DA_CAMPANHA.md` para:

- segredos do mestre;
- bastidores;
- verdades possíveis;
- decisões pendentes do Sage;
- pistas verdadeiras;
- pistas falsas;
- condições de revelação;
- consequências futuras;
- status atual das frentes;
- o que já foi revelado em sessão;
- o que ainda não pode ser mostrado aos jogadores.

Não duplicar descrições longas da nota principal no Estado da Campanha.

## Home do Mestre

Use `Home_Mestre.md` apenas para:

- links rápidos;
- painéis;
- frentes ativas;
- alertas;
- atalhos para notas importantes.

## Estrutura recomendada para locais

```md
# Nome do Local

> [!world]- SINOPSE PÚBLICA
> Resumo seguro para jogadores.

## Resumo

## Descrição Jogável

## Atmosfera

## Função em Jogo

## Pontos Importantes

## Pessoas Ligadas

## Facções Ligadas

## Rumores Locais

## Ganchos de Aventura

## Uso em Mesa

## Pendências Visíveis

## Links Relevantes
```

## Estrutura recomendada para facções

```md
# Nome da Facção

> [!world]- SINOPSE PÚBLICA
> O que o povo sabe, acredita ou teme.

## Resumo

## Imagem Pública

## Estrutura Conhecida

## Objetivos Declarados

## Métodos Conhecidos

## Relações Conhecidas

## Presença em Jogo

## Rumores

## Ganchos de Aventura

## Uso em Mesa

## Links Relevantes
```

## Estrutura recomendada para personagens

Preservar a ficha quando ela já existir, mas organizar o corpo em torno de:

```md
# Nome do Personagem

## Visão Geral

## Aparência

## Personalidade

## História Conhecida

## Relações Conhecidas

## Objetivos Visíveis

## Função em Jogo

## Equipamentos

## Rumores

## Uso em Mesa

## Pendências Visíveis
```

## Estrutura recomendada para frentes no Estado da Campanha

```md
## Frente — Nome da Entidade ou Arco

### Entidades Ligadas

### Status Atual

### Segredos do Mestre

### Verdades Possíveis

### Pistas

### Rumores: Verdadeiros, Falsos ou Incompletos

### Condições de Revelação

### Consequências

### Decisões Pendentes do Sage
```

## Regra técnica

Preservar frontmatter existente e campos legados.

Não alterar mídia, links, Dataview, DataCards, Leaflet ou mapas durante uma passagem de conteúdo, salvo quando a correção for explicitamente necessária para a própria nota.

## Ordem segura de aplicação

1. Criar ou atualizar o modelo.
2. Centralizar bastidores existentes no Estado da Campanha.
3. Remover seções de segredo pesado das notas principais.
4. Desenvolver notas principais como player-safe.
5. Atualizar a Home do Mestre apenas como painel.
6. Auditar o restante do vault por vazamentos.
