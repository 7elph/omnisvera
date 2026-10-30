import type { PlayableCharacter } from '../api';
import { mediaUrlFromVaultPath } from '../api';
import InventoryItemIcon from './InventoryItemIcon';

/** Read-only projection of existing slots, never creates/equips inventory. */
export default function EquipmentLoadout({ inventory, cover, portrait, onInspect }: { inventory: PlayableCharacter['inventory']; cover?: string | null; portrait?: string | null; onInspect?: (item: PlayableCharacter['inventory'][number]) => void }) {
  const art = mediaUrlFromVaultPath(cover || portrait, 768);
  const equipped = inventory.filter(item => item.equipped && item.quantity > 0);
  const slots = [...new Set(['Cabeça', 'Armadura', 'Corpo a corpo', 'Mão secundária', 'À distância', 'Cinto', 'Pés', 'Acessório', ...equipped.map(item => item.equipment_slot || 'Acessório')])];
  return <section className="workspace-equipment-loadout" aria-label="Equipamentos atuais">
    <header>Equipamentos</header>
    <svg className="workspace-equipment-silhouette" viewBox="0 0 100 160" aria-hidden="true"><circle cx="50" cy="20" r="13"/><path d="M32 42 Q50 32 68 42 L82 90 L69 94 L62 65 L62 102 L68 151 L53 151 L50 109 L47 151 L32 151 L38 102 L38 65 L31 94 L18 90Z"/></svg>
    {art && <img key={art} className="workspace-equipment-portrait" src={art} alt="" aria-hidden="true" loading="lazy" decoding="async" fetchPriority="low" onError={event => { event.currentTarget.hidden = true; }} />}
    <div>{slots.map(slot => <div className="workspace-equipment-slot" key={slot}>
      <small>{slot}</small>
      {equipped.filter(item => (item.equipment_slot || 'Acessório') === slot).map(item => <InventoryItemIcon key={item.item_path} item={item} showQuantity={false} onInspect={() => onInspect?.(item)} />)}
      {!equipped.some(item => (item.equipment_slot || 'Acessório') === slot) && <span aria-label={`${slot}: vazio`}>—</span>}
    </div>)}</div>
  </section>;
}
