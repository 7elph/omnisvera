import type { ReactNode } from 'react';

/** Reuse the inventory heading/summary layout without changing spell actions. */
export default function SpellCard({ heading, summary, children, className }: {
  heading: ReactNode; summary: ReactNode; children?: ReactNode; className?: string;
}) {
  return <article tabIndex={0} className={`workspace-spell-card${className ? ` ${className}` : ''}`} data-companion-card="true">
    <div className="workspace-catalog-card-heading">{heading}</div>
    <div className="workspace-catalog-card-summary">{summary}</div>
    {children}
  </article>;
}
