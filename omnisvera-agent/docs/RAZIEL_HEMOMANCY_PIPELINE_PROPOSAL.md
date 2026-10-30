# Hemomante — proposta de pipeline no nível 5

Histórico: esta alternativa foi substituída pela [base aprovada em 17/10](RAZIEL_HEMOMANCY_APPROVED.md).

Estado: **PROPOSTA PARA APROVAÇÃO**, não implementada no backend, catálogo,
inventário ou ficha operacional. Não é regra de Old Dragon. Substitui somente
a discussão de alternativas, não as mecânicas aprovadas que já estão funcionando.

Objetivo: DPS com cinco armas, cinco habilidades compartilhadas e cinco
passivas condicionais. Sem criar 25 handlers independentes.

## Fluxo de uma ação

Escolher arma → escolher habilidade → card → alcance no mapa → alvo → Sim →
backend valida uma vez → rola/aplica → passiva compatível automática → registro.
Escolher a forma não gasta outro turno. O custo TOTAL é mostrado antes do Sim.
Uma ação principal, sem ataques gratuitos por troca de arma ou acionamento de
passiva. Recusar/cancelar não gasta; ataque confirmado gasta mesmo se errar.

## Cinco armas propostas

Custos por ataque confirmado; dados antes dos modificadores autorizados da ficha.

| Arma | Sangue | Dano base | Alcance | Identidade/perk |
|---|---:|---|---|---|
| Espada Rubra | 2 | 1d8 | adjacência | +1 no dano contra alvo já ferido |
| Lança Carmesim | 2 | 1d6 | 3 m | atacar a duas células de 1,5 m, sem reação gratuita |
| Adagas Hemáticas | 2 | dois golpes de 1d4 | adjacência | dois d20, mas uma única ação e um único custo |
| Foice Escarlate | 3 | 1d10 | adjacência | +2 no dano contra alvo com até metade dos PV |
| Arco Sanguíneo | 2 | 1d6 | 9 m | ataque à distância, sem munição física |

As Adagas Hemáticas NÃO são as Adagas de Espectro Fantasma. O item físico
continua separado, com sua drenagem e reforço já aprovados. Estes nomes não
concedem bônus de equipamento físico a armas conjuradas.

## Cinco habilidades compartilhadas

Cada arma usa **uma** destas por ação; custo abaixo é adicional ao da arma.
Todos os bônus de dano por ação aplicam-se somente ao primeiro golpe que acerta,
inclusive nas adagas; não duplicar bônus/recursos em cada projétil ou golpe.

| Habilidade | Extra | Efeito proposto |
|---|---:|---|
| Ataque Preciso | 0 | ataque normal com a arma escolhida |
| Investida Rubra | 1 | até 3 m pelo movimento restante do turno; +2 no acerto após mover ao menos 1,5 m |
| Ruptura | 1 | ignora até 2 de redução de dano; não modifica CA nem ignora imunidades |
| Marca de Caça | 1 | se acertar, marca esse alvo por 2 turnos completos de Raziel; próximo ataque dele recebe +1 no dano |
| Execução | 2 | +1d6 no dano se o alvo já estava com até metade dos PV antes do ataque |

Marca: uma por invocador, substituição não acumula; benefício consumido no
primeiro acerto subsequente, nunca no ataque que a criou. É uma alternativa
proposta, **não aprovação de Marca Rubra aprimorada**.
Investida não teleporta e não cria outro orçamento de movimento.

## Cinco passivas automáticas

| Passiva | Combinação que a dispara | Benefício proposto |
|---|---|---|
| Fio Persistente | Espada + Ruptura, acertando alvo com RD | +1 dano após mitigação, sem superar imunidade |
| Ponta Predatória | Lança + Investida, movimento válido de ao menos 1,5 m | +1 no acerto, além da habilidade |
| Coleta Vital | Adagas + Marca, ao menos um golpe acertou | cura 1 PV, no máximo uma vez por ação e limitada aos PV removidos |
| Ceifa | Foice + Execução, alvo previamente com até metade dos PV | +2 dano; não gera ataque nem recupera sangue |
| Pulso Estável | Arco + Ataque Preciso, sem deslocamento anterior no turno | +1 no acerto |

Passivas não têm botão nem custo separado. Só uma pode disparar por ação.
Não recuperam Reserva de Sangue, evitando ciclos infinitos. Cura não ultrapassa
PV máximo. “Já ferido/metade” usa o snapshot anterior ao ataque, não o dano dele.

## Limites de balanceamento para aprovar

- Reserva atual: 10. Combos acima custam 2–5: entre 2 explosões e 5 ataques
  sustentados sem recuperar sangue. Fora deles, preservar opções sem sangue.
- Exemplo: espada + Ruptura custa 3; foice + Execução custa 5. Com dois usos
  desta última esgota-se a reserva: não prometer DPS infinito.
- Proposta inicial: não empilhar reforço +1d4/ponto nestas cinco armas conjuradas;
  reforço já aprovado nas armas equipadas continua intocado. Qualquer ampliação
  depende de aprovação, inclusive como interage com as duas adagas.
- Não somar automaticamente estes valores a Arma de Sangue/Garras/Investida
  antigas: aprovar coexistência ou substituição/migração antes de ativar.
- Sem escalonamento adicional por nível até aprovar tabela; conservar nível 5
  como referência, sem inventar perks para Corpo/Técnica de Predador.
- Aprovar números, custos, passivas, dois golpes e duração antes do backend.
  As cinco passivas são propostas novas, não desbloqueio silencioso das antigas.

## Implementação posterior, depois da aprovação

Usar os contratos existentes: catálogo/action cards, resolução/confirm,
orçamento do turno, efeitos, grid, ledger e realtime. Arma/habilidade/passiva
são dados de um comando com chave idempotente, não três chamadas de mutação.
Backend compõe e valida o custo total e a compatibilidade; frontend só escolhe
e mostra. Reutilizar a Hemomancia atual, sem outro inventário/sistema de combate.

Testar acerto/erro, sangue insuficiente, cancelamento, retry simultâneo,
duas adagas, marca sem auto-consumo, expiração, alcance, movimento e cura real.
Comparar dano em 3 turnos contra CA/RD declaradas na fixture, com Vezemir como
referência e com/sem recursos; não usar produção como laboratório.
