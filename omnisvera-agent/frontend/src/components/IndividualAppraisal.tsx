import {useEffect,useRef,useState} from 'react';
import {appraiseMerchantItem,type CommerceShop} from '../api';

export default function IndividualAppraisal({shop,characterId,onSaved}:{shop:CommerceShop;characterId:string;onSaved:()=>void}){
  const [item,setItem]=useState(''),[price,setPrice]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const generation=useRef(0),locked=useRef(false);
  useEffect(()=>{generation.current++;setItem('');setPrice('');setError('');setBusy(false);locked.current=false;return()=>{generation.current++;};},[shop.id,characterId]);
  const choices=[...shop.sellable,...(shop.blocked_sales||[]).filter(o=>['modified_item','depleted','price_missing'].includes(o.reason))];
  async function save(){if(locked.current||!item||!characterId||price==='')return;locked.current=true;setBusy(true);setError('');const current=generation.current;
    try{await appraiseMerchantItem(shop.id,{request_id:crypto.randomUUID(),character_id:characterId,item_path:item,unit_copper:Math.round(Number(price)*100)});if(current===generation.current)onSaved();}
    catch(e){if(current===generation.current)setError(e instanceof Error?e.message:String(e));}
    finally{if(current===generation.current){locked.current=false;setBusy(false);}}
  }
  return <details className="commerce-setup"><summary>Avaliação individual</summary><p>Oferta final deste comprador para o objeto atual. Cargas e danos são preservados; o objeto fica separado do estoque novo após a venda.</p>
    <label>Item deste personagem<select aria-label="Item para oferta individual" value={item} onChange={e=>{setItem(e.target.value);setError('');}}><option value="">Selecionar item</option>{choices.map(o=><option key={o.id} value={o.id}>{o.name}</option>)}</select></label>
    <label>Recompra por unidade (PO)<input aria-label="Preço da oferta individual" type="number" min={0} max={1000000} step="0.01" value={price} onChange={e=>setPrice(e.target.value)}/></label>
    {error&&<p role="alert">{error}</p>}<button type="button" disabled={busy||!item||price===''||!Number.isFinite(Number(price))||Number(price)<0} onClick={()=>void save()}>Definir oferta</button>
    {!!shop.blocked_offers?.some(o=>o.instance)&&<details><summary>Objetos adquiridos para avaliação</summary>{shop.blocked_offers.filter(o=>o.instance).map(o=><p key={o.id}><strong>{o.name}</strong> · {o.quantity} un. · {o.instance?.condition?.kind==='rust'?'Ferrugem preservada. ':''}{o.instance?.charges_max!=null?`${o.instance.charges_current}/${o.instance.charges_max} cargas. `:''}Fora do estoque de itens novos.</p>)}</details>}
  </details>;
}
