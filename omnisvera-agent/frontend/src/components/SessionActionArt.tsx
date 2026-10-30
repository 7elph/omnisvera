import type { SessionActionCard, SessionLedgerEntry } from '../api';
import type { ReactNode } from 'react';
import { mediaUrlFromVaultPath } from '../api';
import SheetDetail from './SheetDetail';

export function ActionArt({ card, iconOnly = false }: { card: SessionActionCard; iconOnly?: boolean }) {
  return <span className="workspace-session-action-art"><SheetDetail title={card.name} description={card.description} icon={mediaUrlFromVaultPath(card.image_path) || undefined}>
    {iconOnly ? card.image_path ? <span className="workspace-visually-hidden">{card.name}</span> : <span role="img" aria-label={card.name}>◈</span> : card.name}
  </SheetDetail></span>;
}

export function ActionTitle({ title, cards = [] }: { title: string; cards?: SessionActionCard[] }) {
  const parts: Array<string | ReactNode> = [];
  let rest = title;
  while (rest) {
    const found = cards.map(card => ({ card, at: rest.toLocaleLowerCase().indexOf(card.name.toLocaleLowerCase()) }))
      .filter(hit => hit.at >= 0).sort((a, b) => a.at - b.at)[0];
    if (!found) { parts.push(rest); break; }
    parts.push(rest.slice(0, found.at), <ActionArt key={`${parts.length}:${found.card.id}`} card={found.card} />);
    rest = rest.slice(found.at + found.card.name.length);
  }
  return <>{parts}{cards.filter(card => !title.toLocaleLowerCase().includes(card.name.toLocaleLowerCase())).map(card => <ActionArt key={card.id} card={card} />)}</>;
}

/** Actions used in this encounter, not an assertion that their effects remain active. */
export function combatActionCards(ledger: SessionLedgerEntry[], characterId: string, active?: boolean, startedAt?: string) {
  const start = Date.parse(startedAt || '');
  if (!active || !Number.isFinite(start)) return [];
  const unique = new Map<string, SessionActionCard>();
  for (const entry of ledger) {
    if (entry.character_id !== characterId || entry.event_kind !== 'action' || entry.voided_at ||
        !['table', 'public'].includes(entry.visibility) || Date.parse(entry.created_at) < start || !Number.isFinite(Date.parse(entry.created_at))) continue;
    for (const card of entry.action_cards || []) if (card.image_path) unique.set(card.id, card);
  }
  return [...unique.values()];
}
