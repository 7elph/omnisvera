import { useEffect, useRef, useState } from 'react';
import type { WorkspaceToken } from '../api';
import type { ReactNode } from 'react';
import TargetSelect from './TargetSelect';
import SpellCard from './SpellCard';

export default function SpellTargetControl({ targets, targetId, disabled, onSelect, onUse, heading, summary, gridded = false, actionRef = "", attackerTokenId = "", attackerCharacterId = "" }: {
  targets: WorkspaceToken[]; targetId: string; disabled: boolean;
  onSelect: (id: string) => void; onUse: (target: WorkspaceToken, automatic?:boolean) => void;
  heading: ReactNode; summary: ReactNode;
  gridded?: boolean; actionRef?: string; attackerTokenId?: string; attackerCharacterId?: string;
}) {
  const target = targets.find(item => item.id === targetId);
  const armId = useRef("");
  useEffect(() => {
    if (!gridded) return;
    const confirm = (event: Event) => {
      const detail = (event as CustomEvent).detail || {};
      if (!detail.targetId || detail.armId !== armId.current) return;
      const token = targets.find(item => item.id === detail.targetId);
      if (token) onUse(token, true);
      armId.current = "";
      window.dispatchEvent(new CustomEvent('omnisvera-targeting-clear', { detail: { armId: detail.armId } }));
    };
    window.addEventListener('omnisvera-targeting-confirm', confirm);
    return () => window.removeEventListener('omnisvera-targeting-confirm', confirm);
  });
  if (gridded) return <SpellCard heading={heading} summary={summary}>
    <div className="workspace-inline-actions workspace-spell-target-control">
      <button data-card-command disabled={disabled} onClick={() => {
        armId.current = crypto.randomUUID();
        window.dispatchEvent(new CustomEvent('omnisvera-targeting-arm', { detail: {
          actionRef, actionLabel: "Mísseis Mágicos", attackerTokenId, attackerCharacterId, armId: armId.current,
        } }));
      }}>Usar</button>
    </div>
  </SpellCard>;
  return <SpellCard heading={heading} summary={summary}>
    <div className="workspace-inline-actions workspace-spell-target-control">
    <TargetSelect label="Alvo de Mísseis Mágicos" targets={targets} value={targetId} disabled={disabled} onChange={onSelect} />
    <button data-card-command disabled={disabled || !target} onClick={() => { if (!disabled && target) onUse(target); }}>Usar</button>
    </div>
  </SpellCard>;
}
