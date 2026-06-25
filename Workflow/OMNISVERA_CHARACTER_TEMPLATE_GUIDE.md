---
type: workflow
subtype: standard
work_status: Active
canon_status: Reference
visibility: Mestre
created_by: IA
requires_review: true
tags:
  - workflow
  - standard
  - template
  - character
---

# Guia de Templates de Personagem — Omnisvera

Este documento explica como usar os templates de personagem do vault Omnisvera.

## Visão Geral

Omnisvera fornece templates prontos para cada subtipo de personagem:

- `Templates/Characters/Personagem Jogador.md` - Para personagens controlados por jogadores
- `Templates/Characters/NPC Importante.md` - Para NPCs centrais na campanha
- `Templates/Characters/NPC Menor.md` - Para NPCs de cena ou papel limitado
- `Templates/Characters/Antagonista.md` - Para vilões principais
- `Templates/Characters/Criatura.md` - Para monstros e criaturas

## Como Usar os Templates

### Passo 1: Escolha o Template Adequado

Selecione o template baseado no tipo de personagem:

- **Personagem Jogador** - Use para PCs (Vezemir, Varkh, Raziel)
- **NPC Importante** - Use para NPCs recorrentes (Elarion Vaelthor, Mestre Odran Veyl)
- **NPC Menor** - Use para NPCs transitórios (comerciante, guarda)
- **Antagonista** - Use para vilões principais (Dragão de Colar Dourado, Lorde Malakar)
- **Criatura** - Use para monstros e bestas

### Passo 2: Copie o Template

Copie o conteúdo do template para uma nova nota.

### Passo 3: Ajuste o Frontmatter

Preencha os campos do frontmatter:

```yaml
name: Nome do Personagem
epithet: Epíteto ou apelido
aliases: ["Apelido 1", "Apelido 2"]
race: Raça
class: Classe (para PCs)
life_status: Vivo/Morto/Desaparecido
role: Papel na história
origin: "[[Local de origem]]"
location: "[[Local atual]]"
territory: "[[Território]]"
faction: ["[[Facção]]"]
faith: ["[[Religião]]"]
thumbnail: zz_media/characters/th_nome.png
portrait: zz_media/characters/nome.png
cover: zz_media/covers/nome_banner.png
arcs: ["Arco narrativo 1", "Arco narrativo 2"]
chapters: ["Capítulo 1", "Capítulo 2"]
```

### Passo 4: Preencha as Seções

Preencha as seções do template com informações do personagem.

### Passo 5: Ajuste o Subtipo

Certifique-se de que o campo `subtype` está correto:

- `player_character` - Para PCs
- `major_npc` - Para NPCs importantes
- `minor_npc` - Para NPCs menores
- `antagonist` - Para antagonistas
- `creature` - Para criaturas

### Passo 6: Salve no Local Adequado

Salve a nota na pasta apropriada:

- `Characters/Individual/` - Para personagens sem afiliação principal
- `Characters/[Nome da Facção]/` - Para membros de facções

## Diferença Entre Templates

### Personagem Jogador

**Quando usar:** Personagens controlados por jogadores

**Seções específicas:**
- O que os jogadores sabem
- O que só o mestre sabe
- Equipamentos importantes
- Capacidades narrativas
- Mecânicas confirmadas
- Mecânicas pendentes

**Campos obrigatórios adicionais:**
- `class` - Classe do personagem
- `chapters` - Lista de aparições

**Exemplo:** Vezemir, Varkh, Raziel

### NPC Importante

**Quando usar:** NPCs com papel recorrente na campanha

**Seções específicas:**
- Função narrativa
- Segredos
- Relações detalhadas

**Campos obrigatórios adicionais:**
- `role` - Função narrativa
- `chapters` - Lista de aparições (se aplicável)

**Exemplo:** Elarion Vaelthor, Mestre Odran Veyl

### NPC Menor

**Quando usar:** NPCs de cena ou papel limitado

**Seções específicas:**
- Descrição rápida
- Função em cena
- Informações conhecidas
- Segredo opcional

**Campos obrigatórios adicionais:**
- `role` - Função em cena
- `chapters` - Opcional

**Exemplo:** Comerciante aleatório, guarda de porta

### Antagonista

**Quando usar:** Vilões principais da campanha

**Seções específicas:**
- Motivação
- Métodos
- Recursos
- Aliados
- Inimigos
- Plano atual
- Fraquezas
- Segredos

**Campos obrigatórios adicionais:**
- `role` - Papel antagonista
- `arcs` - Arcos antagonistas
- `chapters` - Lista de aparições

**Exemplo:** Dragão de Colar Dourado, Lorde Malakar

### Criatura

**Quando usar:** Monstros, bestas, entidades sobrenaturais

**Seções específicas:**
- Descrição
- Origem
- Habitat
- Comportamento
- Ameaça
- Capacidades narrativas
- Mecânicas pendentes

**Campos obrigatórios adicionais:**
- `race` - Tipo de criatura
- `life_status` - Estado vital
- `role` - Papel ecossistêmico ou narrativo

**Exemplo:** Bestas selvagens, monstros de masmorra

## Boas Práticas

### 1. Não Invente Lore

Templates não devem conter lore inventado. Use apenas como estrutura.

### 2. Marque Incertezas

Use a seção "Pendências do Sage" para marcar informações não confirmadas.

### 3. Separe Lore e Mecânica

Mantenha narrativa e regras de jogo em seções separadas.

### 4. Use Wikilinks

Sempre use wikilinks para referências a outras notas.

### 5. Seja Consistente

Use sempre a mesma estrutura e nomenclatura definida nos padrões.

### 6. Atualize Regularmente

Mantenha as notas atualizadas conforme a campanha avança.

## Exemplo de Uso

### Criando Vezemir

1. Copie `Templates/Characters/Personagem Jogador.md`
2. Ajuste frontmatter:
   ```yaml
   name: Vezemir
   epithet: O Bastardo de Ferro
   race: Meio-elfo
   class: Guerreiro
   life_status: Vivo
   role: Bastardo de Ferro, vingador de Leth'valora
   origin: "[[Antiga Estrada Esquecida]]"
   location: "[[Nimalis]]"
   territory: "[[Nimalia]]"
   faction: ["[[Guardiões do Véu Cinzento]]"]
   ```
3. Preencha seções com informações de Vezemir
4. Salve como `Characters/Individual/Vezemir.md`
5. Adicione aparições em `chapters`

## Personalização

Templates podem ser personalizados conforme necessário, mas mantenha:

- Estrutura básica de seções
- Campos obrigatórios do frontmatter
- Separação entre lore e mecânica
- Seção de pendências do Sage

## Documentos Relacionados

- `Workflow/OMNISVERA_NOTE_STANDARD.md` - Padrão geral de notas
- `Workflow/OMNISVERA_FRONTMATTER_SCHEMA.md` - Esquema de frontmatter
- `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` - Sistema de dashboards
- `Workflow/OMNISVERA_MEDIA_STANDARD.md` - Padrão de mídia
