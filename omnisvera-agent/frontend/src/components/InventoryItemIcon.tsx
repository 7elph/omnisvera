import { useState } from 'react';
import { mediaUrlFromVaultPath, type PlayableCharacter } from '../api';
import { iconPathForItem } from '../companionIconCatalog';

export function inventoryQuantity(item: PlayableCharacter['inventory'][number]) {
  if (item.mechanics?.family !== 'ammunition') return item.quantity;
  if (item.quantity <= 0) return 0;
  const pack = Math.max(1, item.charges_max || item.mechanics.charges_max || 1);
  return (item.quantity - 1) * pack + Math.min(pack, Math.max(0, item.charges_current ?? pack));
}

/** One shared inventory/equipment projection; native item dialog owns all writes. */
export default function InventoryItemIcon({item, onInspect, showQuantity = true}: {
  item: PlayableCharacter['inventory'][number]; onInspect?: () => void; showQuantity?: boolean;
}) {
  const preferred = mediaUrlFromVaultPath(item.thumbnail || item.cover, 128);
  const fallback = mediaUrlFromVaultPath(iconPathForItem(item.item_title, item.item_type) || 'zz_media/ui/icons/items/inventario.jpg', 128);
  const [failed, setFailed] = useState('');
  const icon = preferred && failed !== preferred ? preferred : fallback;
  return <button type="button" className={`workspace-item-icon${item.equipped ? ' equipped' : ''}`} aria-label={item.item_title} title={item.item_title} onClick={onInspect}>
    {failed === icon ? <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14v14H5ZM8 7V4h8v3M5 12h14" fill="none" stroke="currentColor" strokeWidth="2"/></svg> : <img src={icon} alt="" loading="lazy" decoding="async" fetchPriority="low" onError={() => setFailed(icon)} />}
    {showQuantity && <b aria-label="Quantidade">{inventoryQuantity(item)}</b>}
  </button>;
}
