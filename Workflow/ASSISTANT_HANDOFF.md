---
obsidianUIMode: preview
NoteIcon: outline
NoteStatus: Active
status: Active
tags:
  - workflow
  - assistant
  - handoff
  - backup
---

# Handoff dos Assistentes

Este arquivo é a memória operacional compartilhada entre Codex e a IA local. Ele deve permanecer curto, factual e versionado no Git.

## Objetivo atual

1. Concluir a migração técnica e narrativa do template Disgraceland para Omnisvera.
2. Preservar frontmatter, YAML, plugins, estilos e funcionalidades do Obsidian.
3. Manter um assistente local capaz de consultar o vault, preparar evidências e continuar tarefas seguras quando Codex não estiver disponível.
4. Manter backups recuperáveis do repositório e das alterações ainda não commitadas.

## Estado atual

- Omnisvera é o universo; Earthropo é o continente principal.
- Nimalia é o reino dos antropos e faz fronteira com a Floresta de Avenor.
- [[Leth'valora]] era uma pequena vila élfica em Avenor e foi destruída.
- Os personagens de jogador são [[Vezemir]], [[Varkh Nimalis]] e [[Raziel]].
- Disgraceland é fonte de template e referência técnica, nunca cânone automático.
- O registro central de continuidade é [[CANON]].
- O estado da migração é controlado em [[MIGRATION_LEDGER]].
- A IA local usa `nomic-embed-text` para busca e `omnisvera-local` para síntese auxiliar.

## Restrições obrigatórias

- Não alterar fatos confirmados em [[CANON]] sem decisão explícita do usuário.
- Não editar diretamente notas canônicas a partir de saída da IA local.
- A IA local deve produzir propostas em `.local-proposals/`.
- Não normalizar `NoteIcon`, listas, wikilinks ou nomes de propriedades por preferência estética.
- Não varrer `zz_media` integralmente sem necessidade.
- Não incluir automaticamente mudanças de mapa ou Leaflet em commits de outras tarefas.
- Nunca tratar conteúdo de Disgraceland como Omnisvera apenas porque está dentro do vault.

## Hierarquia de fontes

1. Decisão explícita mais recente do usuário.
2. [[CANON]].
3. Notas consolidadas dos três personagens.
4. Referências fornecidas pelos jogadores.
5. Notas de Omnisvera.
6. Disgraceland, exclusivamente como template ou inspiração deliberada.

## Próxima sequência

1. Revisar o calendário de trabalho e decidir quais nomes e feriados entram no cânone.
2. Revisar conteúdo de trabalho por pasta, começando por geografia e regiões.
3. Consolidar fronteiras, capital e marcadores do mapa sem antecipar descobertas dos jogadores.
4. Revisar as histórias dos três personagens em busca de nomes, lugares e datas inconsistentes.
5. Registrar cada decisão aprovada em [[CANON]] antes de fazer correções em massa.

## Última atualização

- Data: 2026-06-21
- Branch: `main`
- Repositório remoto privado: `7elph/omnisvera`
- Conector remoto antigo: indisponível por depender de túnel ngrok expirado.
- Substituição: servidor MCP local por `stdio`, configurado no próprio notebook.
- `NOTES.md` e o caminho ativo do Capítulo 01 já foram separados de seus equivalentes legados.
- O modelo local de contingência exige fontes explícitas; busca semântica isolada não autoriza síntese.
- As notas ativas de Guerreiro, Ladrão, Clérigo e Mago agora resumem OD2; as versões da edição anterior estão arquivadas como `Legacy`.
- A auditoria de runtime verifica consultas, mídias, frontmatter e Leaflet por `Workflow/audit_runtime.py`.
- As notas narrativas antigas foram agrupadas em `Workflow/Legacy/`; configurações reutilizáveis permanecem em `Workflow/Templates/`.
- O Calendarium ativo usa um rascunho de Omnisvera no ano 2100; a configuração original de Tribucia foi preservada como template.
- O snippet ativo de perfil chama-se `omnisvera-profile`; a classe antiga continua disponível apenas como compatibilidade.
