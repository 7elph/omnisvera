import { useState, type CSSProperties } from "react";
import { mediaUrlFromVaultPath, type InventoryItem, type PlayableCharacterDefinition } from "../api";
import { iconPathForItem } from "../companionIconCatalog";

type Defenses = PlayableCharacterDefinition["defenses"];
const iconStyle: CSSProperties = { width: 24, height: 24, objectFit: "cover", verticalAlign: "middle", marginLeft: ".35em", background: "#0f1011", border: "1px solid #8f7444", borderRadius: 3, boxSizing: "border-box", flexShrink: 0 };

export function armorClassBonus(defenses: Defenses): number {
  if (defenses?.armor_class == null) return 0;
  return defenses.unmodified_armor_class != null
    ? defenses.armor_class - defenses.unmodified_armor_class
    : defenses.armor_modifier ?? defenses.armor_modifier_source?.value ?? 0;
}

export default function ArmorClassValue({ defenses, inventory = [] }: { defenses: Defenses; inventory?: InventoryItem[] }) {
  const [failed, setFailed] = useState<string[]>([]);
  const bonus = armorClassBonus(defenses);
  const source = defenses?.armor_modifier_source;
  const armor = source && inventory.find((item) => item.item_path === source.item_path);
  const fallback = source ? mediaUrlFromVaultPath(iconPathForItem(armor?.item_title || source.item_title, armor?.item_type), 128) : "";
  const preferred = mediaUrlFromVaultPath(armor?.thumbnail || armor?.cover, 128);
  const icon = preferred && !failed.includes(preferred) ? preferred : fallback;
  return <>{defenses?.armor_class ?? "—"}{source && (icon && !failed.includes(icon) ?
    <img src={icon} alt="" role="img" aria-label={source.item_title} title={source.item_title} style={iconStyle} onError={() => setFailed(previous => previous.includes(icon) ? previous : [...previous, icon])} /> :
    <svg viewBox="0 0 24 24" role="img" aria-label={source.item_title} style={iconStyle}><title>{source.item_title}</title><path d="M12 3 4 6v6c0 4 5 8 8 9 3-1 8-5 8-9V6Z" fill="none" stroke="currentColor" strokeWidth="2" /></svg>
  )}{bonus !== 0 && <span aria-label={`Bônus de CA ${bonus > 0 ? "+" : ""}${bonus}`} style={{ color: "#65d58a", fontSize: ".65em", marginLeft: ".35em", whiteSpace: "nowrap" }}>{bonus > 0 ? "+" : ""}{bonus}</span>}</>;
}
