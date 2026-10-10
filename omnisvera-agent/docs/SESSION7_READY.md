# Sessão 7 — Portões Fechados

Preparação instalada no Companion nativo como **planejada**, não jogada. Sessão id 7; cenas 14–22 nesta instalação. IDs podem variar em outro banco. Os dados operacionais estão em sessões, cenas, NPCs, mapas, pins, elementos e loot; este documento é apenas a cola de mesa.

## Abrir hoje

1. Backend já reiniciado em 8787, com os tokens existentes. Se estiver desligado: na pasta `omnisvera-agent`, execute `./start_backend.ps1 -Port 8787` (frontend compilado é servido pelo backend).
2. Abra `http://127.0.0.1:8787` no PC ou o endereço Tailscale já usado pelos celulares. Entre como Mestre com seu token existente.
3. O combate antigo foi preservado, inclusive turno de Morthak e PV. **Encerre-o pelo painel Combate quando estiver pronto para começar a nova mesa**; a preparação não o substitui.
4. Em **Cenas**, escolha **01 · Retorno e reunião**. Na referência S7, clique **Iniciar Sessão 7** e depois **Abrir cena preparada na Mesa**. Checklist 17/17 pronto. O histórico e briefing estão em **Sessão → Sessão 7 → Ver sessão**.
5. Escolha as próximas cenas no seletor. Abrir na Mesa ativa o mapa associado. Revele NPCs, pins e documentos individualmente quando fizer sentido.
6. Se houver confronto, abra **06 · Armazém: provas e captura** na Mesa. Use **Iniciar encontro preparado** na referência rápida S7; Dorn é opcional. Ajuste iniciativas no painel nativo de Combate.
7. Ao final, encerre o combate, registre as descobertas/decisões reais e clique **Encerrar Sessão 7** na referência da cena. Os dois botões usam o status nativo e recusam alterar um combate salvo. Recarregar não apaga o estado.

## Referência rápida

| Cena | Objetivo / elenco | Pistas e testes sugeridos | Saídas |
| --- | --- | --- | --- |
| 01 Retorno | Reunião; três jogadores e Dorn | Estrada movimentada; SAB 10 opcional | Portão ou desvio |
| 02 Portão Sul | Maera Dhal; inspeção, não combate automático | CAR 12; documentação/aval; ocultação DES 14 se plausível | Conclave / porto / outra entrada |
| 03 Conclave | Teren Voss; engenharia recente, encaixe antigo | INT 12; diagnóstico de Dorn 14; relatório | Maré Baixa / outra investigação |
| 04 Maré Baixa | Iria do Cais; lote MB-17 | CAR 11 ou registros públicos; SAB 12 saída secundária | Armazém / acompanhar carroça |
| 05 Exterior | Entrada por rua, cais, conversa ou furtividade | Ancoragem FOR/INT 12; sangue SAB 12 | Arena / desvio |
| 06 Arena | Serren + caçador + operador + artífice | Preservar documentos, impedir fuga, capturar vivo, recuperar liga | Oficina / retirada / negociação |
| 06b Oficina | Ordem, desenho e selo | INT 12 rota; mana residual; Dorn 14 classificação incompleta | Montanhas ou Nimalis |
| 07 Opcional | Segunda equipe de captura | SAB 12 antecedência; falha custa tempo, não encerra trilha | Próxima viagem, se escolhida |
| 08 Opcional | Financiamento/permissões em Nimalis | CAR/INT 12 contato por código | Outra investigação, se escolhida |

Notas completas e consequências ficam na **Referência rápida do Mestre · S7** de cada cena. Não narrar fala, decisão nem ação dos jogadores. Testes não são pedágios obrigatórios: argumentos/evidências plausíveis podem resolver; falhas mantêm testemunhas, cópias e caminhos alternativos.

## Arena preparada

Seis mapas esquemáticos funcionais, gerados por código (não IA), 32×24 células de 1,5 m. Caixas, guindaste, correntes, oficina, carroça e acessos estão marcados. São coberturas/zonas, não paredes contínuas. Pins dos personagens vinculam suas fichas reais. Inimigos inicialmente ocultos; fog inicialmente desligado, editável pelo Mestre.

| Inimigo | PV | CA | JP | Ataque |
| --- | --- | --- | --- | --- |
| Caçador de Captura | 8 | 13 | 14 | Besta +2, 1d6; sedativo separado 1d4 |
| Operador de Corrente | 14 | 14 | 13 | Corrente +2, 1d6+1 |
| Artífice de Campo | 7 | 12 | 15 | Ferramenta +1, 1d4 |
| Serren Kaal | 20 | 14 | 12 | Arpão +3, 1d8 |

Uma ação por turno. Segundo caçador é **reserva oculta**, não participa do início. Considere-o somente se houver domínio claro, aviso plausível e necessidade real; Morthak continua com 8 PV, não foi curado artificialmente.

Captura usa **JP normal da ficha do alvo**. Efeitos especiais destes novos inimigos são adjudicados pelo Mestre nos controles já existentes, não um motor novo:

- Sedativo: até dois virotes; após acerto, JP; falha sonolência por um turno (-2 ataque e metade do movimento), sem inconsciência ou empilhamento.
- Corrente/arpão: escolher dano **ou** manobra; JP evita puxão/queda/ligação. Declare antes de rolar, não aplique ambos automaticamente.
- Fumaça: até duas bombas, área 2×2 por duas rodadas; ajustar fog/cobertura manualmente. Rede permite tentativa de escape por JP/ação conforme ficha e situação.
- Queimar ordem exige duas ações consecutivas junto à mesa; interrupção cancela. Preparar carroça exige duas ações e caminho livre. Mensageiro deve alcançar saída e gastar ação para avisar. Não são relógios automáticos nem eventos inevitáveis.

## Documentos e recompensa

Cinco handouts nativos, inicialmente privados: relatório do Conclave; código de remessas; ordem de captura parcialmente destruída; desenho técnico; selo parcial. Use **Revelar aos jogadores** no elemento correspondente. A ordem diz prioridade ao adulto, filhote vivo, terceiro conhecido e expressa ordem de não enfrentar o terceiro. Não identifica contratante.

Loot nativo `loot:session7-cache`, inicialmente rascunho: no máximo 20 PO, seis virotes comuns, fragmento de liga e recibo MB-17. Revele/distribua em **Mestre → Itens e loot** somente se recuperado. Não somar a caixa e rolagens Q para inflacionar recompensa; morte não é requisito. Informação, contatos e consequências são a recompensa principal.

## Fichas e continuidade

- Vezemir, Morthak e Raziel são os jogadores da S7; Dorn é aliado opcional. Varkh continua preservado globalmente, excluído do elenco e encontro preparados.
- Grisalma permanece a arma real de Vezemir. Pulseira é item separado. Sua restrição por três turnos usa a mecânica existente com JP do alvo; eventual retorno de Grisalma ainda exige decisão do Mestre, não foi inventado poder automático.
- Página de Grimório: desequipada = três usos; equipada = quatro. Após o reinício, a normalização vigente corrigiu o limite de Morthak de quatro para três porque o item estava desequipado; nenhuma magia foi consumida.
- Esqueleto nativo: 10 PV, CA 16, ataque +2 / 1d6+1, visual vegetal enviado pelo usuário; novas invocações usam o ícone atual do catálogo. Essência é apresentada no card pelo fluxo existente. Não foi inventada ficha inferior para desequipar, pois não há baseline anterior aprovado.
- Dorn mantém Guarda, Vanguarda e ficha atual. Diagnóstico voltou como controle compacto recolhido; INT nativo, custo/turno nativo e interpretação do Mestre. Resultado nunca revela lore automaticamente.
- Canon anterior, proposta S7, segredo e possibilidades não definidas estão separados no briefing. Coroa, Guilda, Odran, mandante, origem completa e natureza do terceiro dragão permanecem abertos.

## Reproduzir a preparação / QA

`python backend/prepare_session7.py --install` é create-only/idempotente; não inicia a mesa, não restaura PV, não equipa itens, não distribui loot. Recusa outra Sessão 7 conflitante. `--encounter` só é permitido com S7 e arena ativas, sem combate anterior. Prefira o botão da cena durante a mesa.

Verificação operacional em **cópia temporária** do banco: `python backend/smoke_session7.py`. Abre nove cenas por HTTP, usa fichas persistidas, inicia encontro, confirma ataque, invoca esqueleto, usa Dorn, revela documentos, distribui loot, encerra/recarrega e compara sessões/cenas 1–6. Não altera a mesa real.

Checks desta entrega: 417 testes backend; 181 testes frontend; typecheck e build aprovados; smoke operacional aprovado. Acesso local e Tailscale HTTP conferidos. Isso não substitui teste ao vivo com Mestre + jogadores em redes distintas. Build conserva aviso de chunk grande; Ollama offline não impede conteúdo preparado nem combate. A árvore já tinha alterações extensas: checkpoint é parcial e depende dessa base de trabalho preservada.
