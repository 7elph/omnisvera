import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import type { ReactNode } from 'react';
import { imagePreviewUrl } from '../api';

/** Read-only inventory-style detail; never executes an action on opening. */
export default function SheetDetail({ title, description, icon, children, showIcon = true, triggerLabel, compactImage = false }: {
  title: string; description: ReactNode; icon?: string; children?: ReactNode; showIcon?: boolean; triggerLabel?: string; compactImage?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [failedIcon, setFailedIcon] = useState<string | null>(null);
  const triggerRef=useRef<HTMLButtonElement>(null);
  const dialogRef=useRef<HTMLElement>(null);
  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => {
      const dialogs=document.querySelectorAll('[role="dialog"][aria-modal="true"]');
      if(dialogs[dialogs.length-1]!==dialogRef.current)return;
      if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();setOpen(false);}
      if(event.key==='Tab'){
        const controls=dialogRef.current?.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]');
        if(!controls?.length)return;
        const first=controls[0],last=controls[controls.length-1];
        if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
        else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
      }
    };
    window.addEventListener('keydown', close);
    return () => {window.removeEventListener('keydown', close);triggerRef.current?.focus();};
  }, [open]);
  return <><button ref={triggerRef} type="button" className="workspace-ability-name" aria-label={triggerLabel} aria-haspopup="dialog" aria-expanded={open} onClick={() => setOpen(true)} onContextMenu={event=>{event.preventDefault();setOpen(true);}}>
    {icon && failedIcon !== icon && showIcon && <img src={imagePreviewUrl(icon)} alt="" loading="lazy" decoding="async" fetchPriority="low" onError={() => setFailedIcon(icon)} />}{children || title}
  </button>{open && createPortal(<div className="workspace-item-modal-backdrop workspace-ability-backdrop" onClick={() => setOpen(false)}>
    <section ref={dialogRef} className={`workspace-ability-detail${compactImage ? ' workspace-identity-detail' : ''}`} role="dialog" aria-modal="true" aria-label={title} onClick={event => event.stopPropagation()}>
      <header><h2>{title}</h2><button type="button" autoFocus aria-label="Fechar descrição" onClick={() => setOpen(false)}>×</button></header>
      {icon && failedIcon !== icon && <img className="workspace-detail-image" src={icon} alt={`Imagem de ${title}`} onError={() => setFailedIcon(icon)} />}
      {typeof description === 'string' || !description ? <p>{description || 'Sem descrição cadastrada.'}</p> : <div className="workspace-detail-content">{description}</div>}
    </section>
  </div>, document.body)}</>;
}
