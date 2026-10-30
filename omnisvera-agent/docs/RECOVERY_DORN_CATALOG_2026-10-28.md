# Recuperação, mídia de Dorn e família de cura

## Recuperação após reload

Os quatro caminhos de comandos genéricos do corte anterior agora guardam
chaves pendentes em `sessionStorage`, antes de enviar. Só persistem hashes e
IDs: sem token, alvo, ficha ou corpo da requisição. O namespace usa SHA-256 do
acesso, modo, servidor e canal; abas diferentes têm armazenamentos distintos.

Após recarregar, repetir a mesma intenção recupera o ID anterior e o backend
devolve o recibo existente. Não há reenvio automático. O registro sai somente
após confirmação e sincronização. Falha/quota/corrupção de storage impede o
envio; não degrada silenciosamente para um comando sem recuperação. Limite de
32 intenções pendentes por canal; não há descarte automático de pendências.

Isso cobre compêndio, conjuração de criatura, ação usável e seletor do grimório.
Não é uma outbox universal para todos os comandos nativos. Fechar a aba,
limpar o armazenamento, trocar acesso ou mudar a intenção não constitui retry
da ação anterior. A interface não restaura automaticamente os seletores.

## Imagens de Dorn

Relâmpago e Adaga existem no Vault. A coleta da fixture não incluía as imagens
projetadas por `dorn_mage`/`approved_spell_pack` nem o fallback de Adaga. Agora
coleta os metadados empacotados quando Dorn está presente e inclui o fallback
conhecido. Não aplica builds, não concede magias e não altera o banco de origem.
Mantém limites de quantidade/tamanho e rejeição de caminhos inseguros.

## Catálogo por famílias

`catalog_spell_contracts.json` registra os três contratos revisados da família
`healing_hp`: Curar Ferimentos Leves (1d8), Graves (2d8+1), Críticos (3d8+3).
O hash de fonte protege a correspondência com o texto: mudança exige revisão.
O lado normal por toque cura um alvo, respeita PV máximo e usa `change_hp`,
ação do turno, ledger e recibos existentes, na mesma transação.

Natureza desconhecida permanece assistida. Mortos-vivos, constructos,
incorpóreos e extraplanares são rejeitados antes de rolar. Não introduz cura
invertida ou dano do reverso. Cura Completa continua assistida. Sem grid, o
alcance permanece assistido; com grid configurado, exige posições e adjacência.

O catálogo publica `automation`: efeito de PV automatizado, JP/dano parcial,
assistido ou bloqueado por falta de fonte. Não chama todo o catálogo de pronto.
Custos/repertórios do grimório continuam assistidos. O frontend apresenta
rolagem, cura efetiva e antes/depois dos PV; não mostra cura como dano.

## QA e limites

Testes descartáveis cobrem reload, perda de confirmação, acesso/aba, falhas de
storage, fórmulas, elegibilidade, máximo, turno, alcance, rollback e HTTP.
Novo lote MCP `catalog`, com quatro atores e `ui:true`: identidade das fichas e
`catalog-recovery-smoke.cjs` em 1440/390 px, com perda de resposta após commit,
reload/replay, três curas e carregamento real dos dois ícones de Dorn.

OpenCode analisou somente o pacote de fontes explicitamente autorizado para
GPT-OSS 120B Cloud. Suas sugestões foram revisadas; funções/executores
hipotéticos da resposta não foram adotados. Nenhuma ficha real é fixture.

## Validação e ativação em 28/10

- Backend: 1.637 testes em 698,866 s; 1.636 aprovados e 1 ignorado porque o
  Windows não permitiu criar symlink no teste de mídia. Nenhuma falha.
- Frontend: suíte completa 458/458; após o ajuste visual, 32 testes focados,
  typecheck e build novamente aprovados. Somente o aviso existente de chunks.
- MCP final: `test-93ec57a65f26439693465ea869a8a911`, PASS, quatro ataques
  de regressão e os dois scripts de UI. `production_modified=false`.
  As capturas de curas/ícones e identidade das quatro fichas foram inspecionadas.
  O compêndio agora usa descrição em largura inteira e controles abaixo,
  sem herdar a coluna estreita reservada a retratos de monstros.
- A primeira tentativa falhou por navegação incorreta do ensaio. Uma rodada
  funcional passou, mas a inspeção revelou o problema de layout. Outra teve
  reset de conexão local; o transporte de teste tolera um único ECONNRESET,
  sempre com o mesmo corpo/ID, e não mascara erros HTTP ou asserções.
  A rodada final confirmou reload sem novo envio automático nem cura duplicada,
  três fórmulas, PV persistidos e imagens em 1440/390 px.
- Backend reiniciado com backup `recovery-dorn-catalog-20261028-104113` em
  `C:\Users\delib\OmnisveraBackups`. Comparadas 25 tabelas protegidas: apenas
  `updated_at` de mapas foi atualizado; fichas, inventários, efeitos, posições,
  sessão, combate, ledger e tokens preservados.
- Endereço público, JS `index-CN2zph6l.js` e CSS `index-DsHLNtKV.css`: HTTP 200,
  conteúdo conferido com o build local. Fichas em leitura: Vezemir, Raziel e
  Morthak com seus acessos; Dorn pelo Mestre, todos HTTP 200. OpenCode saudável
  e `companion-tests` conectado; demais conectores preservados.

Catálogo operacional: 854 magias; 3 com efeito de cura de PV automatizado,
83 com dano/JP parcial, 764 assistidas e 4 bloqueadas por fonte insuficiente.
Isso não certifica custos/repertórios, reversos, toda a mídia ou mesa real em
redes diferentes. O lote não concedeu magias nem alterou fichas operacionais.
Sem staging, commit ou push; alterações anteriores da worktree preservadas.
