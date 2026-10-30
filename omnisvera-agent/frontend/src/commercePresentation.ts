export const tradeGroups:Record<string,string>={equipment:'Equipamentos',supplies:'Suprimentos',healing:'Poções comuns',arcane:'Itens arcanos',transport:'Transportes',livestock:'Animais',unclassified:'Outros'};
export const saleReason=(reason:string)=>({equipped:'Guarde o item no inventário antes de vender.',price_missing:'Valor ainda não definido pelo Mestre.',merchant_category:'Este estabelecimento não compra este tipo de item.',not_physical:'Serviço ou referência: não pode ser vendido como objeto.',modified_item:'Item modificado: solicite uma oferta individual ao Mestre.',depleted:'Item com cargas usadas: solicite uma oferta individual.'}[reason]||'Item indisponível para venda.');
export const formatTradeMoney=(copper:number)=>`${(copper/100).toLocaleString('pt-BR',{maximumFractionDigits:2})} PO`;
export function purseLabel(purse:Record<string,number>){return [['copper_coins','PC'],['silver_coins','PP'],['coins','PO'],['platinum_coins','PL']].filter(([key])=>purse[key]).map(([key,label])=>`${purse[key]} ${label}`).join(' · ')||'0 PO';}
/** A location owns its merchant portrait; an actual combat participant stays visible. */
export function showMerchantMapToken(token:{id:string;sheet?:{embedded_in_location?:string}},presentIds:ReadonlySet<string>,combatIds:ReadonlySet<string>):boolean {
  const parent=token.sheet?.embedded_in_location;
  return !parent || !presentIds.has(parent) || combatIds.has(token.id);
}
