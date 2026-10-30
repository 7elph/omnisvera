import type { ReactNode } from 'react';

export default function NightFormControl({ animal, busy, canActivate, selector, onActivate, onDeactivate }: {
  animal?: string | null; busy: boolean; canActivate: boolean; selector: ReactNode;
  onActivate: () => void; onDeactivate: () => void;
}) {
  const active = Boolean(animal);
  const names: Record<string, string> = { corvo: 'Corvo', coruja: 'Coruja', morcego: 'Morcego' };
  return <div className="workspace-target-actions workspace-night-form-controls">
    {active ? <small>Ativa · {names[animal!] || animal}</small> : selector}
    <button type="button" role="switch" aria-label="Forma da Noite" aria-checked={active}
      disabled={busy || (!active && !canActivate)} onClick={active ? onDeactivate : onActivate}>
      {active ? 'Desativar' : 'Ativar'}
    </button>
  </div>;
}
