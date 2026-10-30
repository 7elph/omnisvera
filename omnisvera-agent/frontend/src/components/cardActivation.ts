import type { MouseEvent, KeyboardEvent } from 'react';

/** Adapt existing commands; never roll, spend, or create a second action here. */
export function activateCard(event: MouseEvent<HTMLElement> | KeyboardEvent<HTMLElement>) {
  if (event.shiftKey) return; // Native heading opens its read-only detail.
  const target=event.target as HTMLElement;
  const card=target.closest('article');
  if (!card || !event.currentTarget.contains(card)) return;
  const command=card.querySelector<HTMLButtonElement>('button[data-card-command]');
  if (!command || target.closest('button[data-card-command]')) return;
  if (target.closest('select,input,textarea,label,a,[data-card-secondary]')) return;
  if ('key' in event && (target!==card || !['Enter',' '].includes(event.key) || event.repeat)) return;
  event.preventDefault();event.stopPropagation();
  if (!command.disabled) command.click();
}
