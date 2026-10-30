import type { ReactNode } from 'react';
import SpellCard from './SpellCard';
import SheetDetail from './SheetDetail';

/** Expanded action controls use the same card anatomy as inventory/spells.
 * Presentation only: opening/closing never sends a command or resets a receipt.
 */
export default function ActionControlCard({title,label,description,icon,summary,onClose,children}:{
  title:string;label:string;description:string;icon?:string;summary?:ReactNode;
  onClose:()=>void;children:ReactNode;
}){
  return <section className="workspace-action-catalog workspace-control-panel" aria-label={label}>
    <SpellCard className="workspace-control-card" heading={<div className="workspace-control-heading">
      <SheetDetail title={title} description={description} icon={icon} />
      <button type="button" aria-label="Fechar controle" onClick={onClose}>×</button>
    </div>} summary={summary || <small>Configurar e executar</small>}>
      <div className="workspace-control-body">{children}</div>
    </SpellCard>
  </section>;
}
