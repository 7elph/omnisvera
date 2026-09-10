import { mediaUrlFromVaultPath, type InventoryItem, type PlayableCharacterDefinition } from "../api";
import { iconPathForItem } from "../companionIconCatalog";

type Defenses = PlayableCharacterDefinition["defenses"];

export function armorClassBonus(defenses: Defenses): number {
  if (defenses?.armor_class == null) return 0;
  return defenses.unmodified_armor_class != null
    ? defenses.armor_class - defenses.unmodified_armor_class
    : defenses.armor_modifier ?? defenses.armor_modifier_source?.value ?? 0;
}

export default function ArmorClassValue({ defenses, inventory = [] }: { defenses: Defenses; inventory?: InventoryItem[] }) {
  const bonus = armorClassBonus(defenses);
  const source = defenses?.armor_modifier_source;
  const armor = source && inventory.find((item) => item.item_path === source.item_path);
  const icon = source ? mediaUrlFromVaultPath(armor?.thumbnail || armor?.cover || iconPathForItem(armor?.item_title || source.item_title, armor?.item_type)) : "";
  return <>{defenses?.armor_class ?? "—"}{source && (icon ? <img src={icon} alt={source.item_title} title={source.item_title} style={{ width: 24, height: 24, objectFit: "cover", verticalAlign: "middle", marginLeft: ".35em", background: "#0f1011", border: "1px solid #8f7444", borderRadius: 3, boxSizing: "border-box" }} /> : <span role="img" aria-label={source.item_title} title={source.item_title} style={{ marginLeft: ".35em" }}>◈</span>)}{bonus !== 0 && <span aria-label={`Bônus de CA ${bonus > 0 ? "+" : ""}${bonus}`} style={{ color: "#65d58a", fontSize: ".65em", marginLeft: ".35em", whiteSpace: "nowrap" }}>{bonus > 0 ? "+" : ""}{bonus}</span>}</>;
}
