import { createPortal } from 'react-dom';
import { useEffect, useRef, type ReactNode } from 'react';

export default function TargetConfirmation({ action, target, busy, onYes, onNo, onRemove, children, message, confirmDisabled = false }: {
  action: string; target: string; busy: boolean; onYes: () => void; onNo: () => void; onRemove?:()=>void; children?:ReactNode; message?:string; confirmDisabled?:boolean;
}) {
  const sent = useRef(false);
  const dialogRef=useRef<HTMLElement>(null);
  useEffect(()=>{
    const previous=document.activeElement;
    const key=(event:KeyboardEvent)=>{
      if(event.key==='Escape' && !busy){event.preventDefault();onNo();}
      if(event.key!=='Tab')return;
      const buttons=dialogRef.current?.querySelectorAll<HTMLElement>('button:not(:disabled), select:not(:disabled), input:not(:disabled)');
      if(!buttons?.length)return;
      const first=buttons[0],last=buttons[buttons.length-1];
      if(event.shiftKey && document.activeElement===first){event.preventDefault();last.focus();}
      else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first.focus();}
    };
    document.addEventListener('keydown',key);
    return()=>{document.removeEventListener('keydown',key);if(previous instanceof HTMLElement && previous.isConnected)previous.focus();};
  },[busy,onNo]);
  return createPortal(<div className="workspace-item-modal-backdrop" onClick={()=>{if(!busy)onNo();}}>
    <section ref={dialogRef} className="workspace-item-modal" role="dialog" aria-modal="true" aria-label="Confirmar alvo" onClick={event => event.stopPropagation()}>
      <header><h2>{action}</h2><button type="button" disabled={busy} aria-label="Cancelar ação" onClick={onNo}>×</button></header>
      <p>{onRemove ? `${target} já está selecionado. Remover este alvo ou concluir com os alvos atuais?` : (message || `Usar em ${target}? Os dados serão rolados e o resultado aplicado automaticamente.`)}</p>
      {children}<div className="workspace-inline-actions">
        {onRemove && <button type="button" disabled={busy} onClick={onRemove}>Deselecionar</button>}
        <button type="button" autoFocus disabled={busy || confirmDisabled} onClick={() => { if (!sent.current) { sent.current = true; onYes(); } }}>{onRemove?'Terminar ação':'Sim'}</button>
        <button type="button" disabled={busy} onClick={onNo}>{onRemove?'Continuar selecionando':'Não'}</button>
      </div>
    </section>
  </div>, document.body);
}
