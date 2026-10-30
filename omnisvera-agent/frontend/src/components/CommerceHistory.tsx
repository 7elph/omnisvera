import {useEffect,useState} from 'react';
import {getCommerceHistory,type CommerceReceipt} from '../api';
import {formatTradeMoney,purseLabel,saleReason} from '../commercePresentation';

export function ReceiptDetails({receipt}:{receipt:CommerceReceipt}){
  return <>
    {receipt.service_effect?.family==='healing_hp'&&<p>PV {receipt.service_effect.hp_before} → {receipt.service_effect.hp_after} · cura +{receipt.service_effect.healing_applied}{receipt.service_effect.roll&&` · dado ${receipt.service_effect.roll.total}`}</p>}
    {receipt.service_effect?.family==='condition_cure'&&<p>Paralisia removida.</p>}
    {receipt.purse_before&&receipt.purse_after&&<small className="commerce-wallet" aria-label="Saldo antes e depois">{purseLabel(receipt.purse_before)} → {purseLabel(receipt.purse_after)}</small>}
    {receipt.audit_status==='legacy_partial'&&<small>Registro antigo: saldo inicial não registrado.</small>}
    {!!receipt.appraisal?.length&&<details><summary>Ver avaliação ({receipt.appraisal.length})</summary>{receipt.appraisal.map(item=><p key={item.id}><strong>{item.name}</strong> · {item.reason?saleReason(item.reason):`Recompra: ${formatTradeMoney(item.price_copper||0)}`}</p>)}</details>}
  </>;
}

export default function CommerceHistory({characterId,revision}:{characterId:string;revision:number}){
  const [open,setOpen]=useState(false),[rows,setRows]=useState<CommerceReceipt[]>([]),[error,setError]=useState('');
  useEffect(()=>{if(!open||!characterId)return;let active=true;setRows([]);setError('');getCommerceHistory(characterId).then(items=>{if(active)setRows(items);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[open,characterId,revision]);
  return <details className="commerce-history" onToggle={e=>setOpen(e.currentTarget.open)}><summary>Histórico deste personagem</summary>{error&&<p role="alert">{error}</p>}{rows.map((r,i)=><article key={r.receipt_id||i}><strong>{r.title||r.name}</strong><ReceiptDetails receipt={r}/></article>)}{open&&!rows.length&&!error&&<p>Nenhuma negociação registrada.</p>}</details>;
}
