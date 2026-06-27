# Omnisvera — Resumo de Decisões da Taxonomia

Fonte principal: `Workflow/OMNISVERA_SYSTEM_TAXONOMY.md`.

## 1. Itens aprovados

- Português BR para linguagem visual e operacional.
- Tags técnicas em minúsculas, sem acento e com hífen.
- Manter `thumbnail`, `cover`, `status`, `chapters` e `tags`.
- Reinterpretar `chapters` como capítulos/seções/partes da campanha.
- Não criar `sessions` como padrão.
- Manter Disgraceland apenas como legado/documentação, não como camada operacional.
- Migrar tags aprovadas:
  - `loyalist` → `coroa-de-nimalia`;
  - `rancher` → `guilda-dos-mercadores`;
  - `pirate` → `conclave-dos-errantes`;
  - `widow` → `guardioes-do-veu-cinzento`;
  - `steeltown` → `nimalia`;
  - `water` → `mar-da-neblina`;
  - `individual` → `personagem`;
  - `religion` → `religiao`;
  - `territory` → `territorio`;
  - `lore` → `lore`.
- Criar categorias RPG:
  - raças;
  - classes;
  - magias;
  - itens;
  - monstros;
  - quests;
  - rumores.

## 2. Itens alterados

| proposta original | decisão alterada |
|---|---|
| `sessions` como eixo RPG | Rejeitado. Usar `chapters`. |
| `story` virar sessão | Rejeitado. Manter como `story`/capítulo até decisão final. |
| Tags antigas preservadas indefinidamente | Devem ser migradas para taxonomia Omnisvera depois de auditoria de plugins. |
| `nimalia` como tag genérica ampla | Permitida com ressalva; precisa revisão por causa de `nimalis` como capital. |
| Pastas em português BR imediatamente | Planejar primeiro; renomear só quando links/consultas/configurações puderem ser atualizados. |

## 3. Itens removidos ou não usados em novos padrões

### Facções removidas da migração oficial

- `resistencia-de-libervale`;
- `tripulacao-de-libervale`;
- `igreja-de-mirella`;
- `palavra-da-estrela-nascida-morta`.

### Territórios removidos da migração oficial

- `eryndor`;
- `libervale`;
- `ashmoor`;
- `terras-de-morghul`;
- `montanhas-do-dragao`.

### Campos YAML rejeitados para novos padrões

- `sessions`;
- `player_known`;
- `subtype`;
- `portrait`;
- `token_image`;
- `map_image`;
- `handout_image`;
- `life_status`;
- `old_dragon_class`;
- `old_dragon_race`;
- `requires_review`;
- `work_status`;
- `canon_status`;
- `source`;
- `state`.

## 4. Dúvidas pendentes

| decisão | motivo |
|---|---|
| `third` | Não aplicar `terceira-fileira`; precisa decidir entre `guardioes-de-lethvalora` ou remoção. |
| `murray` | Precisa decidir entre `nobreza-de-nimalia` e `nobreza-de-nimalis`. |
| `story` | Manter por enquanto; decidir depois se vira `capitulo`. |
| `nimalia` vs `nimalis` | Separar claramente reino/contexto e capital/localização. |
| `porto-de-zevran` | Revisar se deve virar `porto-de-nimalis`. |
| `region` vs `location` | Definir semântica antes de padronizar templates. |
| `cssclass` vs `cssclasses` | Auditar impacto visual antes de alterar. |
| `Government` | Decidir se mantém herdado ou se será substituído por campo técnico normalizado. |

## 5. Contradições ou riscos que precisam revisão

| ponto | risco | decisão segura atual |
|---|---|---|
| `tags` marcado como remover em decisão anterior | Quebrar Supercharged Links, Dataview e DataCards. | Não remover globalmente. Usar tags como infraestrutura técnica. |
| `sessions` aprovado em etapa anterior, rejeitado agora | Consultas futuras poderiam divergir. | Congelar novo padrão em `chapters`; não criar novas consultas por `sessions`. |
| Templates atuais usam campos rejeitados | Templates podem perpetuar schema ruim. | Atualizar templates novos e deixar correção em massa para etapa posterior. |
| CSS gerado contém tags antigas | Editar CSS gerado direto pode ser frágil. | Preferir configuração fonte do Supercharged Links; CSS só muda se controlado/versionado. |
| Pastas em inglês ainda existem | Renomear sem plano quebra links e Dataview. | Criar plano PT-BR; não renomear nesta etapa. |
