import { useEffect, useState, type ReactNode } from 'react';

/** Native disclosure: manual toggle is respected until the combat state changes. */
export default function SheetSection({ title, autoOpen = false, children }: {
  title: string; autoOpen?: boolean; children: ReactNode;
}) {
  const [open, setOpen] = useState(autoOpen);
  useEffect(() => { setOpen(autoOpen); }, [autoOpen]);
  return <details className="workspace-sheet-section" open={open} onToggle={event => setOpen(event.currentTarget.open)}>
    <summary>{title}</summary>{children}
  </details>;
}
