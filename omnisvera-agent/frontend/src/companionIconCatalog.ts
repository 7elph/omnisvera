const MAP_ICON_IDS = [
  "earthropo", "nimalia", "floresta-de-avenor", "vale-dourado", "bosque-sussurrante", "mar-da-neblina", "costa-dos-naufragios", "lago-prateado", "montanhas-geladas", "passagem-de-korr", "montanhas-do-dragao", "terras-de-morghul",
  "nimalis", "porto-de-nimalia", "mare-baixa", "bairro-nobre", "bairro-dos-forasteiros", "mercado-central", "casa-da-moeda-de-nimalia", "o-frasco-afogado", "leth-valora", "ruinas-de-valthor", "fortaleza-de-gharok", "fortaleza-abandonada-de-avenor", "santuario-de-elaris", "porto-de-zevran", "antiga-estrada-esquecida",
  "capital", "cidade", "bairro", "porto", "fortaleza", "santuario", "ruina", "estrada", "floresta", "vale", "lago", "costa", "mar", "montanha", "regiao",
] as const;

const ITEM_ICON_IDS = [
  "adaga", "alabarda", "azagaia", "bordao-cajado", "chicote", "cimitarra", "espada-bastarda", "espada-curta", "espada-larga", "espada-longa", "falcione", "foice-de-mao", "lanca-curta", "lanca-longa", "maca", "machado", "machado-de-arremesso", "machado-de-batalha", "mangual", "martelo", "martelo-de-batalha", "montante", "picareta", "porrete", "sabre", "tridente",
  "arco-curto", "arco-longo", "besta-de-mao", "besta", "dardo", "flecha", "flecha-improvisada",
  "armadura-acolchoada", "armadura-de-couro", "armadura-de-couro-batido", "cota-de-malha", "armadura-de-placas", "armadura-completa", "broquel", "escudo-de-madeira", "escudo-de-aco", "escudo-torre",
  "arpeu", "corda", "giz", "mochila", "odre", "pederneira", "tocha", "vara-de-3-m",
  "apito", "escada-de-corda", "frasco-de-oleo", "lanterna-furta-fogo", "pa-picareta", "pe-de-cabra", "pena-tinta", "pergaminhos", "racao-de-viagem", "rede", "saco-de-dormir", "tenda",
  "cadeado", "estrepe", "ferramentas-de-arrombamento", "ferramentas-de-desarme-de-armadilhas", "vela",
  "acido", "agua-benta", "antitoxina", "bastao-solar", "fogo-de-alquimista", "ima", "incenso", "pedra-trovao", "anel-magico", "dados", "inventario", "kit-basico",
] as const;

export type CompanionIconCategory = "map" | "items";
export type CompanionIcon = { id: string; label: string; category: CompanionIconCategory; path: string };

function labelFromId(id: string) {
  return id.split("-").map((part) => part ? part[0].toUpperCase() + part.slice(1) : part).join(" ");
}

const ITEM_ICON_EXTENSIONS: Record<string, string> = {
  "anel-magico": "jpg",
  dados: "jpg",
  inventario: "jpg",
  "kit-basico": "jpg",
};

function itemIconPath(id: string) {
  return `zz_media/ui/icons/items/${id}.${ITEM_ICON_EXTENSIONS[id] || "png"}`;
}

export const COMPANION_ICON_CATALOG: CompanionIcon[] = [
  ...MAP_ICON_IDS.map((id) => ({ id, label: labelFromId(id), category: "map" as const, path: `zz_media/ui/icons/map/${id}.png` })),
  ...ITEM_ICON_IDS.map((id) => ({ id, label: labelFromId(id), category: "items" as const, path: itemIconPath(id) })),
];

function slug(value: unknown) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/['’]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function cleanItemDisplayName(value: unknown) {
  return String(value || "")
    .replace(/\s+(?:de|da)\s+varkh\b/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

const ITEM_ALIASES: Record<string, string> = {
  cajado: "bordao-cajado",
  bordao: "bordao-cajado",
  bastao: "bordao-cajado",
  espada: "espada-longa",
  machado: "machado-de-batalha",
  arco: "arco-curto",
  escudo: "escudo-de-aco",
  armadura: "armadura-completa",
  lanterna: "lanterna-furta-fogo",
  picareta: "pa-picareta",
};

const MAP_ALIASES: Record<string, string> = {
  nimalis: "nimalis",
  nimalia: "nimalia",
  avenor: "floresta-de-avenor",
  floresta: "floresta",
  bosque: "bosque-sussurrante",
  mercado: "mercado-central",
  ruinas: "ruinas-de-valthor",
  porto: "porto",
  montanha: "montanha",
  realm: "regiao",
  territory: "regiao",
  region: "regiao",
  city: "cidade",
  village: "bairro",
  district: "bairro",
  fortress: "fortaleza",
  sanctuary: "santuario",
  forest: "floresta",
  road: "estrada",
  lake: "lago",
  sea: "mar",
  coast: "costa",
  valley: "vale",
  unknown: "regiao",
};

function resolveIcon(ids: readonly string[], value: unknown, aliases: Record<string, string>) {
  const normalized = slug(value);
  if (!normalized) return null;
  if (ids.includes(normalized as never)) return normalized;
  const alias = aliases[normalized];
  if (alias && ids.includes(alias as never)) return alias;
  const matching = ids.filter((id) => normalized.includes(id) || id.includes(normalized)).sort((a, b) => b.length - a.length);
  return matching[0] || null;
}

export function iconPathForItem(name: unknown, itemType?: unknown) {
  const direct = resolveIcon(ITEM_ICON_IDS, name, ITEM_ALIASES);
  const byType = direct || resolveIcon(ITEM_ICON_IDS, itemType, ITEM_ALIASES);
  return byType ? itemIconPath(byType) : null;
}

export function iconPathForMapLocation(name: unknown, locationType?: unknown, markerIcon?: unknown) {
  const direct = resolveIcon(MAP_ICON_IDS, name, MAP_ALIASES);
  const marker = direct || resolveIcon(MAP_ICON_IDS, markerIcon, MAP_ALIASES);
  const type = marker || resolveIcon(MAP_ICON_IDS, locationType, MAP_ALIASES);
  return type ? `zz_media/ui/icons/map/${type}.png` : null;
}
