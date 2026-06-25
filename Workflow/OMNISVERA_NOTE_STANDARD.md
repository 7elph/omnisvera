---
obsidianUIMode: preview
NoteIcon: list
NoteStatus: Active
status: Active
tags:
  - workflow
  - standard
  - character
---

# Padrão de Notas de Personagem — Omnisvera

Este documento define o padrão oficial para notas de personagem no vault Omnisvera.

## Princípios Fundamentais

Omnisvera segue estes princípios para notas de personagem:

1. **Disgraceland é referência visual/técnica, não cânone** - O vault `Workflow/Legacy/Disgraceland/` serve apenas como inspiração para estrutura visual e organização técnica.
2. **O vault deve ser útil para o Sage mestrar** - A estrutura prioriza acessibilidade para o mestre durante sessões.
3. **O vault deve ser navegável no Obsidian** - Links, wikilinks e navegação devem ser intuitivos.
4. **O vault deve ser legível por IA** - Estrutura consistente facilita processamento por agentes de IA.
5. **O vault deve separar jogador/mestre** - Informações sensíveis ficam em seções separadas.
6. **O vault deve separar lore/mecânica** - Narrativa e regras de jogo ficam em seções distintas.
7. **O vault deve separar estado da nota e estado do personagem** - Frontmatter distingue editorial de narrativa.
8. **O vault deve evitar campos duplicados** - Cada informação tem um lugar definido.
9. **O vault deve usar português como idioma principal** - Exceto termos técnicos consolidados.
10. **O vault deve usar propriedades como fonte principal da verdade** - Frontmatter > corpo > tags.
11. **Tags devem ser auxiliares, não a fonte principal da verdade** - Tags servem para filtros, não para dados estruturados.

## Regra Crítica de Frontmatter

Nunca usar `status` para duas coisas diferentes.

Use sempre:

```yaml
work_status: Em desenvolvimento
life_status: Vivo
canon_status: Draft
```

**Significados:**

- `work_status`: Estado editorial da nota (Em desenvolvimento, Revisão, Finalizado)
- `life_status`: Estado narrativo do personagem (Vivo, Morto, Desaparecido, Desconhecido)
- `canon_status`: Estado canônico (Draft, Working Canon, Confirmed)

## Estrutura de Pastas

Personagens são organizados em:

```
Characters/
├── Individual/          # Personagens sem afiliação de grupo principal
├── [Nome da Facção]/    # Personagens de facções específicas
└── [Outros grupos]/     # Outras organizações naturais
```

**Exemplos:**

- `Characters/Individual/Varkh Nimalis.md` - Kenku sem afiliação principal
- `Characters/Clã Sanguinallis/Lorde Malakar.md` - Membro de facção
- `Characters/Guardiões do Véu Cinzento/Elarion Vaelthor.md` - Membro de ordem

## Subtipos Oficiais

Omnisvera define cinco subtipos de personagem:

### 1. player_character

Personagem controlado por um jogador.

- **Uso:** Todos os PCs (Vezemir, Varkh, Raziel)
- **Requisitos:** Mecânicas confirmadas, mecânicas pendentes, equipamentos
- **Seções especiais:** O que jogadores sabem, O que só o mestre sabe

### 2. major_npc

NPC importante com papel recorrente na campanha.

- **Uso:** NPCs centrais (Elarion Vaelthor, Mestre Odran Veyl)
- **Requisitos:** História detalhada, relações, segredos
- **Seções especiais:** Função narrativa, segredos, relações

### 3. minor_npc

NPC de cena ou papel limitado.

- **Uso:** NPCs transitórios (comerciante, guarda aleatória)
- **Requisitos:** Descrição rápida, função em cena
- **Seções especiais:** Informações conhecidas, segredo opcional

### 4. antagonist

Antagonista ativo da campanha.

- **Uso:** Vilões principais (Dragão de Colar Dourado, Lorde Malakar)
- **Requisitos:** Motivação, métodos, recursos, plano atual
- **Seções especiais:** Motivação, fraquezas, segredos

### 5. creature

Criatura não-humanóide ou monstro.

- **Uso:** Monstros, bestas, entidades sobrenaturais
- **Requisitos:** Descrição, habitat, comportamento, ameaça
- **Seções especiais:** Biologia, comportamento, capacidades narrativas

## Separação de Informações

### Jogador vs Mestre

Informações são divididas em três níveis de acesso:

1. **Público** - Visível para todos (Visão Geral, Aparência)
2. **Jogadores** - Visível para PCs (O que os jogadores sabem)
3. **Mestre** - Visível apenas para o Sage (O que só o mestre sabe)

### Lore vs Mecânica

Informações narrativas e regras de jogo são separadas:

- **Lore** - História, personalidade, relações, segredos
- **Mecânica** - Estatísticas, habilidades, regras confirmadas
- **Pendente** - Regras não definidas ainda

## Seções Obrigatórias

Todas as notas de personagem devem incluir:

1. **Visão Geral** - Dados vitais em tabela
2. **Aparições** - Lista de capítulos onde aparece (Dataview)
3. **História** - Biografia narrativa
4. **Personalidade** - Temperamento, virtudes, defeitos
5. **Relações** - Conexões com outros personagens
6. **Papel na Campanha** - Função narrativa
7. **Pendências do Sage** - Itens pendentes de confirmação
8. **Links relevantes** - Wikilinks para notas relacionadas

## Seções Específicas por Subtipo

### Personagem Jogador

- O que os jogadores sabem
- O que só o mestre sabe
- Equipamentos importantes
- Capacidades narrativas
- Mecânicas confirmadas
- Mecânicas pendentes

### NPC Importante

- Função narrativa
- Segredos
- Relações detalhadas

### NPC Menor

- Descrição rápida
- Função em cena
- Informações conhecidas
- Segredo opcional

### Antagonista

- Motivação
- Métodos
- Recursos
- Aliados
- Inimigos
- Plano atual
- Fraquezas
- Segredos

### Criatura

- Descrição
- Origem
- Habitat
- Comportamento
- Ameaça
- Capacidades narrativas
- Mecânicas pendentes

## Referência Disgraceland

O vault Disgraceland (`Workflow/Legacy/Disgraceland/`) foi usado como referência para:

- Estrutura de pastas por facção
- Sistema de thumbnails e retratos laterais
- Uso de Dataview para aparições
- Frontmatter com campos de localização, facção, capítulos
- Páginas de facção listando membros
- Capítulos listando personagens
- Dashboards em Home

Omnisvera adapta esses elementos com schema mais limpo e adequado ao contexto de fantasia medieval.

## Documentos Relacionados

- `Workflow/OMNISVERA_FRONTMATTER_SCHEMA.md` - Esquema detalhado de frontmatter
- `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` - Sistema de dashboards e Dataview
- `Workflow/OMNISVERA_MEDIA_STANDARD.md` - Padrão de organização de mídia
- `Workflow/OMNISVERA_CHARACTER_TEMPLATE_GUIDE.md` - Guia de uso de templates
- `Templates/Characters/` - Templates prontos para cada subtipo
