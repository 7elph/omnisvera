import CommerceHistory,{ReceiptDetails} from './CommerceHistory';
import IndividualAppraisal from './IndividualAppraisal';
import {configureMagicServices} from '../api';
import {tradeGroups,saleReason} from '../commercePresentation';
import {useEffect,useRef,useState} from 'react';
import CommerceItemImage from './CommerceItemImage';
import {addMerchantService,addMerchantStock,configureMerchant,confirmCommerce,createMerchant,getPinCommerce,removeMerchantService,removeMerchantStock,
  getTradeCatalog,setItemTradeProfile,listMerchants,listNpcs,listWorldLocations,quoteCommerce,
  type CommerceShop,type CommerceQuote,type CommerceReceipt,type CompendiumItemsResponse,type Merchant,type NpcRecord,type WorldLocationRecord} from '../api';

const money=(copper:number)=>`${(copper/100).toLocaleString('pt-BR',{maximumFractionDigits:2})} PO`;

/** Same pin and character stores as the table. Opening never spends anything. */
export default function MapCommerce({tokenId,tokenName,characterId,mode,onChange,onInspectNpc}:{
  tokenId:string;tokenName:string;characterId:string;mode:'gm'|'player';onChange:()=>Promise<void>;onInspectNpc?:(tokenId:string)=>void;
}) {
  const [shops,setShops]=useState<CommerceShop[]>([]),[error,setError]=useState(''),[message,setMessage]=useState('');
  const [busy,setBusy]=useState(false),[quote,setQuote]=useState<CommerceQuote|null>(null),[quantity,setQuantity]=useState(1);
  const [tab,setTab]=useState<'buy'|'sell'|'service'>('buy');
  const epoch=useRef(0),lock=useRef(false),confirmKey=useRef('');
  const [revision,setRevision]=useState(0),[receipt,setReceipt]=useState<CommerceReceipt|null>(null),[historyRevision,setHistoryRevision]=useState(0);
  useEffect(()=>{
    const generation=++epoch.current,abort=new AbortController();setQuote(null);setReceipt(null);setError('');setMessage('');setShops([]);setBusy(false);lock.current=false;
    let latest=0;
    const refresh=()=>{const request=++latest;return getPinCommerce(tokenId,characterId,abort.signal).then(rows=>{if(epoch.current===generation&&request===latest)setShops(rows);}).catch(reason=>{if(!abort.signal.aborted&&epoch.current===generation&&request===latest)setError(String(reason.message||reason));});};
    void refresh();const changed=()=>{void refresh();};window.addEventListener('omnisvera-session-changed',changed);
    return()=>{++epoch.current;abort.abort();window.removeEventListener('omnisvera-session-changed',changed);};
  },[tokenId,characterId,revision]);
  async function negotiate(shop:CommerceShop,id:string,kind:'buy'|'sell'|'service',haggle=false){
    if(lock.current||!characterId)return;lock.current=true;setBusy(true);setError('');const generation=epoch.current;
    try {const result=await quoteCommerce(shop.id,{request_id:crypto.randomUUID(),character_id:characterId,kind,target_id:id,quantity:kind==='service'?1:quantity,negotiate:haggle});
      if(epoch.current!==generation)return;confirmKey.current=crypto.randomUUID();setQuote(result);
    }catch(reason){if(epoch.current===generation)setError(reason instanceof Error?reason.message:String(reason));}
    finally{if(epoch.current===generation){lock.current=false;setBusy(false);}}
  }
  async function confirm(){
    if(!quote||lock.current)return;lock.current=true;setBusy(true);setError('');const generation=epoch.current;
    try {const result=await confirmCommerce(quote.id,confirmKey.current);
      if(epoch.current!==generation)return;
      setQuote(null);setReceipt(result);setHistoryRevision(v=>v+1);setMessage(`${result.kind==='sell'?'Vendido':result.kind==='service'?'Contratado':'Comprado'}: ${result.quantity}× ${result.name} · ${money(result.total_copper)}${result.service_status==='reserved'?' · reservado até o descanso concedido pelo Mestre':''}`);
      await onChange();if(epoch.current===generation){const rows=await getPinCommerce(tokenId,characterId);if(epoch.current===generation)setShops(rows);}
    }catch(reason){if(epoch.current===generation)setError(reason instanceof Error?reason.message:String(reason));}
    finally{if(epoch.current===generation){lock.current=false;setBusy(false);}}
  }
  if(mode==='player'&&!shops.length&&!error)return null;
  return <section className="workspace-commerce" aria-label="Comércio e serviços">
    {error&&<p role="alert">{error}</p>}{message&&<p role="status">{message}</p>}{receipt&&<div data-commerce-receipt={receipt.receipt_id}><ReceiptDetails receipt={receipt}/></div>}
    {characterId&&<CommerceHistory characterId={characterId} revision={historyRevision}/>}
    {shops.map(shop=><section key={shop.id} aria-label={`Ofertas de ${shop.name}`}>
      <header><strong>{shop.name}</strong>{!shop.enabled&&<small>Não disponível aos jogadores</small>}</header>
      {mode==='gm'&&characterId&&<IndividualAppraisal shop={shop} characterId={characterId} onSaved={()=>setRevision(v=>v+1)}/>}
      {shop.responsible_npc&&<details className="commerce-npc"><summary><CommerceItemImage name={shop.responsible_npc.name} imagePath={shop.responsible_npc.portrait_path}/>{shop.responsible_npc.name}</summary><p>{shop.responsible_npc.public_description}</p>{mode==='gm'&&shop.responsible_npc.combat_token_id&&onInspectNpc&&<button type="button" onClick={()=>onInspectNpc(shop.responsible_npc!.combat_token_id!)}>Abrir ficha de {shop.responsible_npc.name}</button>}</details>}
      <div className="commerce-tabs">{(['buy','sell','service'] as const).map(kind=><button type="button" key={kind} aria-pressed={tab===kind} onClick={()=>{setTab(kind);setQuote(null);}}>{kind==='buy'?'Comprar':kind==='sell'?'Vender':'Serviços'}</button>)}</div>
      {tab==='sell'&&<small>Recompra: {shop.buy_pct}% do valor cadastrado{shop.trade_policy?.buy?` · Aceita: ${shop.trade_policy.buy.map(g=>tradeGroups[g]||g).join(', ')}`:''}</small>}
      {tab!=='service'&&<label>Quantidade <input aria-label="Quantidade da negociação" type="number" min={1} max={999} value={quantity} onChange={e=>{setQuantity(Math.max(1,Math.min(999,Number(e.target.value)||1)));setQuote(null);}} /></label>}
      <div className="commerce-offers">{tab==='service'?shop.services.map(service=><button type="button" key={service.id} disabled={busy||!characterId||service.available===false} onClick={()=>void negotiate(shop,service.id,'service')}><strong>{service.name}</strong><span>{money(service.price_copper)}</span><small>{service.unavailable_reason||(service.kind==='lodging'?'Reserva para o descanso do Mestre':service.kind==='appraisal'?'Avaliação dos itens deste personagem':service.kind==='spell'?'Atendimento mágico fora de combate':'Entrega de itens')}</small></button>):(tab==='sell'?shop.sellable:shop.offers).map(offer=><article key={offer.id}>
        <button type="button" disabled={busy||!characterId||offer.quantity===0} onClick={()=>void negotiate(shop,offer.id,tab)}><CommerceItemImage name={offer.name} imagePath={offer.image_path}/><strong>{offer.name}</strong><span>{money(offer.price_copper)} · <span aria-label={tab==='sell'?'Quantidade no inventário':'Estoque disponível'}>{offer.quantity===-1?'Disponível sem limite':`${offer.quantity} ${tab==='sell'?'no inventário':'disponíveis'}`}</span></span></button>
        {tab==='buy'&&offer.quantity!==0&&<button type="button" className="commerce-bargain" disabled={busy||!characterId} aria-label={`Barganhar ${offer.name}`} onClick={()=>void negotiate(shop,offer.id,'buy',true)}>Barganhar</button>}
      </article>)}</div>
      {tab==='sell'&&!!shop.blocked_sales?.length&&<details className="commerce-blocked"><summary>Itens indisponíveis para venda ({shop.blocked_sales.length})</summary>{shop.blocked_sales.map(item=><p key={item.id}><strong>{item.name}</strong> · {saleReason(item.reason)}</p>)}</details>}
      {tab==='sell'&&!shop.sellable.length&&<p>Nenhum item guardado com preço de recompra disponível.</p>}
      {tab==='service'&&!shop.services.length&&<p>Sem serviços disponíveis.</p>}
    </section>)}
    {quote&&<section className="commerce-confirmation" role="group" aria-label="Confirmar negociação"><strong>{quote.quantity}× {quote.name} · {money(quote.total_copper)}</strong><small>{quote.kind==='sell'?'Você receberá':'Você pagará'} {money(quote.total_copper)}</small>{quote.bargain&&<p>d20 {quote.bargain.d20} + {quote.bargain.modifier} = {quote.bargain.total} · {quote.bargain.label}</p>}<div><button type="button" disabled={busy} onClick={()=>void confirm()}>{busy?'Concluindo…':'Confirmar'}</button><button type="button" disabled={busy} onClick={()=>setQuote(null)}>Cancelar</button></div></section>}
    {mode==='gm'&&<CommerceSetup tokenId={tokenId} tokenName={tokenName} shops={shops} onSaved={()=>setRevision(value=>value+1)} />}
  </section>;
}

function CommerceSetup({tokenId,tokenName,shops,onSaved}:{tokenId:string;tokenName:string;shops:CommerceShop[];onSaved:()=>void}){
  const [open,setOpen]=useState(false),[merchants,setMerchants]=useState<Merchant[]>([]),[items,setItems]=useState<CompendiumItemsResponse|null>(null);
  const [npcs,setNpcs]=useState<NpcRecord[]>([]),[locations,setLocations]=useState<WorldLocationRecord[]>([]);
  const [mid,setMid]=useState(''),[npc,setNpc]=useState(''),[location,setLocation]=useState(''),[enabled,setEnabled]=useState(true),[pct,setPct]=useState(50);
  const [item,setItem]=useState(''),[qty,setQty]=useState(1),[price,setPrice]=useState('');
  const [serviceName,setServiceName]=useState(''),[serviceKind,setServiceKind]=useState<'lodging'|'delivery'|'appraisal'>('lodging'),[servicePrice,setServicePrice]=useState(''),[serviceItem,setServiceItem]=useState(''),[serviceQty,setServiceQty]=useState(1);
  const [busy,setBusy]=useState(false),[error,setError]=useState('');const lock=useRef(false);
  const [valuation,setValuation]=useState(''),[value,setValue]=useState(''),[group,setGroup]=useState('equipment');
  const [policy,setPolicy]=useState<{buy?:string[];sell?:string[]}|undefined>();
  const autoLinked=useRef(false);
  useEffect(()=>{if(!open||autoLinked.current||mid||!shops.length)return;autoLinked.current=true;const linked=shops[0];setMid(linked.id);setNpc(linked.npc_id?String(linked.npc_id):'');setLocation(linked.location_id?String(linked.location_id):'');setPct(linked.buy_pct);setEnabled(linked.enabled);setPolicy(linked.trade_policy);},[open,mid,shops]);
  useEffect(()=>{if(!open)return;let active=true;
    Promise.all([listMerchants(),getTradeCatalog(),listNpcs(),listWorldLocations()]).then(([m,i,n,l])=>{if(active){setMerchants(m);setItems(i);setNpcs(n);setLocations(l);}}).catch(reason=>{if(active)setError(String(reason.message||reason));});
    return()=>{active=false;};
  },[open]);
  async function run(action:()=>Promise<unknown>){if(lock.current)return;lock.current=true;setBusy(true);setError('');try{await action();onSaved();}catch(reason){setError(reason instanceof Error?reason.message:String(reason));}finally{lock.current=false;setBusy(false);}}
  const binding=(id:string)=>configureMerchant(id,{token_id:tokenId,npc_id:npc?Number(npc):null,location_id:location?Number(location):null,enabled,buy_pct:pct,policy});
  return <details className="commerce-setup" onToggle={event=>setOpen(event.currentTarget.open)}><summary>Configurar ofertas</summary>{error&&<p role="alert">{error}</p>}
    <fieldset disabled={busy}><label>Estabelecimento<select aria-label="Estabelecimento" value={mid} onChange={event=>{const id=event.target.value;setMid(id);const linked=shops.find(s=>s.id===id);setNpc(linked?.npc_id?String(linked.npc_id):'');setLocation(linked?.location_id?String(linked.location_id):'');setPct(linked?.buy_pct??50);setEnabled(linked?.enabled??true);setPolicy(linked?.trade_policy);}}><option value="">Novo neste pin</option>{merchants.map(m=><option key={m.id} value={m.id}>{m.name}</option>)}</select></label>
    <label>NPC responsável<select aria-label="NPC responsável" value={npc} onChange={e=>setNpc(e.target.value)}><option value="">Sem NPC vinculado</option>{npcs.map(n=><option value={n.id} key={n.id}>{n.name}</option>)}</select></label>
    <label>Local<select aria-label="Local do estabelecimento" value={location} onChange={e=>setLocation(e.target.value)}><option value="">O próprio pin</option>{locations.map(l=><option value={l.id} key={l.id}>{l.name}</option>)}</select></label>
    <label>Recompra (%)<input type="number" min={0} max={100} value={pct} onChange={e=>setPct(Number(e.target.value))} /></label>
    <label><input type="checkbox" checked={enabled} onChange={e=>setEnabled(e.target.checked)} /> Disponível aos jogadores</label>
    <details><summary>Tipos de item comprados e vendidos</summary>{(['buy','sell'] as const).map(side=><fieldset key={side}><legend>{side==='buy'?'O estabelecimento compra':'O estabelecimento vende'}</legend>{Object.entries(tradeGroups).map(([key,label])=><label key={key}><input type="checkbox" checked={(policy?.[side]||Object.keys(tradeGroups)).includes(key)} onChange={e=>setPolicy(previous=>{const current=previous?.[side]||Object.keys(tradeGroups);return {...previous,[side]:e.target.checked?[...current,key]:current.filter(g=>g!==key)};})}/>{label}</label>)}</fieldset>)}</details>
    <details><summary>Avaliar preço de um item</summary><label>Item<select aria-label="Item para avaliar" value={valuation} onChange={e=>setValuation(e.target.value)}><option value="">Escolher item</option>{items?.items.filter(i=>i.catalog_entry_kind!=='reference').map(i=><option key={i.id} value={i.native_item_path||'compendium:'+i.id}>{i.name}</option>)}</select></label><label>Valor base em PO<input aria-label="Valor base do item" type="number" min={0} step="0.01" value={value} onChange={e=>setValue(e.target.value)}/></label><select aria-label="Tipo de comércio" value={group} onChange={e=>setGroup(e.target.value)}>{Object.entries(tradeGroups).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select><button disabled={!valuation||value===''} onClick={()=>void run(async()=>{await setItemTradeProfile({item_path:valuation,price_copper:Math.round(Number(value)*100),trade_group:group,request_id:crypto.randomUUID()});setItems(await getTradeCatalog());})}>Salvar avaliação</button></details>
    <button type="button" onClick={()=>void run(async()=>{let id=mid;if(!id){const created=await createMerchant({name:tokenName});id=created.id;setMerchants(current=>[...current,created]);setMid(id);}await binding(id);})}>Salvar vínculo</button>
    {mid&&<>{shops.find(s=>s.id===mid)?.offers.map(offer=><button type="button" key={offer.id} onClick={()=>void run(()=>removeMerchantStock(mid,offer.id))}>Retirar oferta: {offer.name}</button>)}
      <button type="button" onClick={()=>void run(()=>configureMagicServices(mid))}>Adicionar atendimento mágico revisado</button>
      {shops.find(s=>s.id===mid)?.services.map(service=><button type="button" key={service.id} onClick={()=>void run(()=>removeMerchantService(mid,service.id))}>Retirar serviço: {service.name}</button>)}
      <label>Item do estoque<select aria-label="Item para oferta" value={item} onChange={e=>setItem(e.target.value)}><option value="">Escolher item</option>{items?.items.filter(i=>i.catalog_entry_kind!=='reference').map(i=><option key={i.id} value={i.id}>{i.name}</option>)}</select></label>
      <label>Estoque<input type="number" min={-1} value={qty} onChange={e=>setQty(Number(e.target.value))} /></label><label>Preço em PO (vazio: catálogo)<input type="number" min={0} step="0.01" value={price} onChange={e=>setPrice(e.target.value)} /></label>
      <button type="button" disabled={!item} onClick={()=>void run(()=>addMerchantStock(mid,{compendium_item_id:item,quantity:qty,price_override_po:price===''?null:Number(price)}))}>Adicionar oferta</button>
      <label>Serviço<input aria-label="Nome do serviço" value={serviceName} onChange={e=>setServiceName(e.target.value)} /></label>
      <label>Entrega<select value={serviceKind} onChange={e=>setServiceKind(e.target.value as 'lodging'|'delivery'|'appraisal')}><option value="lodging">Hospedagem até o descanso do Mestre</option><option value="delivery">Entrega de itens</option><option value="appraisal">Avaliação de inventário</option></select></label>
      <label>Preço do serviço (PO)<input type="number" min={0} step="0.01" value={servicePrice} onChange={e=>setServicePrice(e.target.value)} /></label>
      {serviceKind==='delivery'&&<><select aria-label="Item do serviço" value={serviceItem} onChange={e=>setServiceItem(e.target.value)}><option value="">Item entregue</option>{items?.items.filter(i=>i.catalog_entry_kind!=='reference').map(i=><option key={i.id} value={i.id}>{i.name}</option>)}</select><input aria-label="Quantidade entregue" type="number" min={1} value={serviceQty} onChange={e=>setServiceQty(Number(e.target.value))} /></>}
      <button type="button" disabled={!serviceName.trim()||servicePrice===''||(serviceKind==='delivery'&&!serviceItem)} onClick={()=>void run(()=>addMerchantService(mid,{name:serviceName,kind:serviceKind,price_copper:Math.round(Number(servicePrice)*100),amount:serviceQty,compendium_item_id:serviceKind==='delivery'?serviceItem:undefined}))}>Adicionar serviço</button>
    </>}</fieldset>
  </details>;
}
