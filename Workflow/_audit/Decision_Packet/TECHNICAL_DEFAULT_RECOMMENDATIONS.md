# Technical Default Recommendations

Estas recomendações são defaults técnicos conservadores para a futura camada de compatibilidade. Elas não resolvem lore e não executam migração.

## Defaults de campos

- Não remover campo antigo no mesmo passo em que adiciona campo novo.
- Manter `chapters` e adicionar `sessions`.
- Criar consultas que aceitem `chapters` e `sessions` durante transição.
- Manter `status` e adicionar `life_status` apenas onde fizer sentido.
- Usar `type` e `subtype` como campos semânticos sem substituir tags visuais.
- Não tornar campos Old Dragon obrigatórios no primeiro lote.
- Se Old Dragon entrar no YAML, começar com campos mínimos e opcionais.

## Defaults de imagens e mídia

- Manter `thumbnail`.
- Manter `cover` separado de `thumbnail`.
- Adicionar `portrait` apenas quando a nota precisar de retrato específico.
- Adicionar `map_image` apenas em notas de mapa ou compatíveis com Leaflet.
- Adicionar `handout_image` apenas com política de `handout_status` e visibilidade.
- Não apagar mídia órfã.
- Não mover ou renomear mídia antes de resolver referências.
- Não tratar “não referenciado” como “inútil” sem validação cruzada.

## Defaults de tags e visual

- Manter tags visuais antigas como ponte.
- Adicionar tags RPG novas sem remover antigas.
- Não substituir tags por `type/subtype` sem ponte.
- Não editar `supercharged-links-gen.css`.
- Alterar Supercharged Links via plugin/configuração apropriada, não por CSS gerado.
- Validar links coloridos no Obsidian após qualquer mudança visual.

## Defaults de dashboards

- Não migrar Home antes de criar filtro de visibilidade.
- Tratar a Home atual como dashboard do mestre até decisão contrária.
- Dashboard de jogadores deve usar whitelist ou filtros explícitos.
- Não consultar `#secret`, notas sem `visibility` ou mídia não liberada em dashboard público.
- DataCards públicos devem exigir `visibility`, `player_known` ou `handout_status`.

## Defaults de mapas e calendário

- Não renomear notas usadas por Leaflet/Calendarium sem atualizar referências.
- Não renomear imagem base de mapa sem validar Leaflet.
- Não mover notas de mapa antes de exportar links/marcadores.
- Manter eventos/calendário até existir ponte para sessões.

## Defaults de templates

- Criar templates prioritários antes dos avançados.
- Começar com campos mínimos.
- Não criar lore nova durante migração técnica.
- Não consolidar várias decisões narrativas dentro de templates técnicos.
- Validar cada template com uma nota de teste antes de migrar lotes.

## Defaults de processo

- Fazer commits pequenos e separados.
- Nunca usar `git add .` ou `git add -A`.
- Rodar `git diff --cached --name-only` antes de cada commit.
- Validar visualmente no Obsidian depois de cada lote.
- Registrar qualquer decisão narrativa separadamente da mudança técnica.

## Default mais seguro para a primeira camada de compatibilidade

1. Preservar tudo que já funciona.
2. Adicionar campos novos como ponte.
3. Criar consultas compatíveis com campo antigo e novo.
4. Validar dashboard como mestre.
5. Só depois discutir dashboard público, limpeza de mídia e remoção de legado.
