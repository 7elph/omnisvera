const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const TOKEN_KEY = "omnisvera_access_token";
const MODE_KEY = "omnisvera_access_mode";

export type AccessMode = "gm" | "player";

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setAccessToken(token: string) {
  if (token.trim()) {
    localStorage.setItem(TOKEN_KEY, token.trim());
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function getAccessMode(): AccessMode {
  return localStorage.getItem(MODE_KEY) === "player" ? "player" : "gm";
}

export function setAccessMode(mode: AccessMode) {
  localStorage.setItem(MODE_KEY, mode);
}

export function consumeAccessBootstrapFromUrl(): { token: string; mode: AccessMode } | null {
  if (typeof window === "undefined" || !window.location.hash) return null;
  const params = new URLSearchParams(window.location.hash.slice(1));
  const token = (params.get("token") || params.get("companion_token") || "").trim();
  if (!token) return null;

  const rawMode = params.get("mode") || params.get("companion_mode");
  const mode: AccessMode = rawMode === "gm" ? "gm" : "player";
  setAccessToken(token);
  setAccessMode(mode);

  // The fragment never reaches the server. Remove the credential from the
  // address bar immediately after saving it for this browser/origin.
  for (const key of ["token", "companion_token", "mode", "companion_mode", "profile", "companion_profile"]) {
    params.delete(key);
  }
  const remainingHash = params.toString();
  window.history.replaceState(
    null,
    "",
    `${window.location.pathname}${window.location.search}${remainingHash ? `#${remainingHash}` : ""}`,
  );
  return { token, mode };
}

export function mediaUrlFromVaultPath(path?: string | null) {
  if (!path) return "";
  const clean = path
    .trim()
    .replace(/^["']|["']$/g, "")
    .replace(/^\[\[/, "")
    .replace(/\]\]$/, "")
    .split("|")[0]
    .replace(/^\/media\//, "")
    .split("?")[0]
    .trim()
    .replace(/^\/+/, "");
  if (!clean) return "";
  const mediaPath = clean.startsWith("zz_media/") ? clean : `zz_media/${clean}`;
  const encoded = mediaPath
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
  const token = getAccessToken();
  const query = token ? `?token=${encodeURIComponent(token)}` : "";
  return `${API_BASE}/media/${encoded}${query}`;
}

function scoped(path: string) {
  return `${API_BASE}/${getAccessMode()}${path}`;
}

function authHeaders(extra: Record<string, string> = {}) {
  const token = getAccessToken();
  return {
    "ngrok-skip-browser-warning": "true",
    ...extra,
    ...(token ? { "X-Omnisvera-Token": token } : {}),
  };
}

export type NoteSummary = {
  id: number;
  path: string;
  title: string;
  aliases: string[];
  type?: string | null;
  visibility?: string | null;
  tags: string[];
  cover?: string | null;
  thumbnail?: string | null;
  status?: string | null;
  description?: string | null;
  updated_at: string;
};

export type NoteDetail = NoteSummary & {
  content: string;
  frontmatter: Record<string, unknown>;
};

export type SearchResult = NoteSummary & {
  score: number;
  excerpt: string;
};

export type ChatResult = {
  answer: string;
  notes_used: NoteSummary[];
  note_paths: string[];
  insufficient_context: boolean;
  warning?: string | null;
  suggested_questions?: string[];
  fatos_confirmados?: Array<{ fato: string; fonte: string }>;
  teorias?: Array<{ teoria: string; base: string[] }>;
  informacoes_insuficientes?: string[];
  fontes_usadas?: string[];
  ollama_used?: boolean;
  ollama_attempted?: boolean;
  model?: string | null;
  retrieval_mode?: string | null;
  interaction_id?: string | null;
  created_at?: string | null;
  response_time_ms?: number | null;
  raw_model_response?: string | null;
  validator_rejections?: Array<Record<string, unknown>>;
  behavior_memory_used?: boolean;
  behavioral_trace?: Record<string, unknown> | null;
};

export type TrainingFeedbackAction = "good" | "correct" | "reject" | "hallucination" | "leak" | "incomplete" | "artificial" | "incorrect_source";

export type TrainingExample = {
  id: string;
  schema_version: string;
  created_at: string;
  updated_at: string;
  source_type: string;
  category: string;
  access_profile: "player" | "gm" | "system";
  persona_id?: string | null;
  instruction: string;
  retrieved_context: Array<Record<string, unknown>>;
  ideal_response: string;
  facts_expected: string[];
  theories_allowed: string[];
  insufficient_information_expected: boolean;
  requires_rag: boolean;
  contains_canon: boolean;
  contains_secret: boolean;
  review_status: "captured" | "pending" | "approved" | "rejected";
  reviewer?: string | null;
  quality_score?: number | null;
  notes?: string | null;
  curation?: {
    interaction_id?: string;
    feedback_action?: TrainingFeedbackAction;
    flags?: Record<string, boolean>;
    quality_5?: number | null;
    curator_notes?: string | null;
    model?: string | null;
    retrieval_mode?: string | null;
  };
  interaction?: TrainingInteraction | null;
};

export type TrainingInteraction = {
  interaction_id: string;
  created_at: string;
  session_id?: string | null;
  user_profile: "player" | "gm";
  question: string;
  raw_model_response?: string | null;
  final_response: string;
  verified_facts: Array<Record<string, unknown>>;
  theories: Array<Record<string, unknown>>;
  insufficient_information: string[];
  retrieved_sources: Array<Record<string, unknown>>;
  retrieval_mode?: string | null;
  model?: string | null;
  ollama_used: boolean;
  response_time_ms: number;
  validator_rejections: Array<Record<string, unknown>>;
  warning?: string | null;
  feedback_status: string;
};

export type TrainingStats = {
  captured: number;
  examples: number;
  statuses: Record<string, number>;
  categories: Record<string, number>;
  profiles: Record<string, number>;
  models: Record<string, number>;
  flags: Record<string, number>;
  approved: number;
  minimum_approved: number;
  progress_percent: number;
  coverage: {
    approved: number;
    categories: Record<string, { current: number; target: number; missing: number }>;
    profiles: Record<string, number>;
    personas: Record<string, number>;
  };
  training_blocked: boolean;
  warning: string;
  behavior_memory: BehaviorMemoryStats;
};

export type BehaviorMemoryStats = {
  enabled: boolean;
  mode: string;
  ab_mode: string;
  approved_total: number;
  eligible: number;
  indexed: number;
  excluded: Array<{ example_id: string; reason: string }>;
  categories: Record<string, number>;
  personas: Record<string, number>;
  access_profiles: Record<string, number>;
  last_updated_at?: string | null;
  recent_responses_using_memory: number;
  average_examples_per_response: number;
  milestones: Array<{ target: number; stage: string; reached: boolean }>;
  next_milestone: { target: number; stage: string; remaining: number };
};

export type TrainingBatchValidation = {
  requested: number;
  eligible: Array<{ id: string; instruction: string; category?: string; access_profile?: string; quality?: number }>;
  blocked: Array<{ id: string; instruction: string; category?: string; access_profile?: string; quality?: number; reasons: string[] }>;
  minimum_quality: number;
  confirmation_required: string;
  approved?: Array<{ id: string; category?: string; access_profile?: string }>;
  approved_count?: number;
};

export type DashboardSection = {
  kind?: string | null;
  title: string;
  description?: string | null;
  cover?: string | null;
  prompt?: string | null;
  items: NoteSummary[];
};

export type PlayerDashboard = {
  mode: "player";
  sections: DashboardSection[];
};

export type PlayerActionType = "investigate" | "talk" | "mission" | "rumor" | "destination" | "theory" | "item_use" | "item_equip" | "item_give";
export type PlayerActionStatus = "submitted" | "in_review" | "answered" | "canonized" | "rejected";

export type PlayerAction = {
  id: number;
  character_path: string;
  character_title: string;
  action_type: PlayerActionType;
  target_path: string;
  target_title: string;
  intent: string;
  status: PlayerActionStatus;
  gm_response?: string | null;
  created_at: string;
  updated_at: string;
};

export type PlayerProfile = {
  profile_id?: string | null;
  character_path?: string | null;
  character_title?: string | null;
  character_note_id?: number | null;
  thumbnail?: string | null;
  cover?: string | null;
  character_class?: string | null;
  race?: string | null;
  level?: string | number | null;
  status?: string | null;
  location?: string | null;
  faction?: string | null;
  shared_access: boolean;
};

export type PlayerDiscovery = {
  id: number;
  profile_id: string;
  note_path: string;
  note_title: string;
  created_at: string;
};

export type PlayerEvent = {
  id: number;
  profile_id: string;
  kind: string;
  title: string;
  message: string;
  note_path?: string | null;
  created_at: string;
  read_at?: string | null;
};

export type PlayerQuestStatus = "available" | "accepted" | "in_progress" | "completed" | "failed" | "archived";

export type PlayerQuest = {
  id: number;
  profile_id: string;
  note_path: string;
  note_title: string;
  status: PlayerQuestStatus;
  progress?: string | null;
  updated_at: string;
};

export type EditableNote = { path: string; content: string; content_hash: string; updated_at: string };
export type ItemEffectRule = {
  id: string;
  trigger: "on_use" | "while_equipped";
  kind: "heal_hp" | "restore_resource" | "add_condition" | "temporary_hp" | "attribute_bonus" | "skill_bonus" | "saving_throw_bonus" | "armor_class_bonus" | "attack_bonus" | "damage_bonus" | "movement_bonus" | "maximum_hp_bonus" | "grant_ability" | "resistance" | "immunity" | "vulnerability";
  target?: string | null;
  value: number;
  formula?: string | null;
  label?: string | null;
  stacking?: "stack" | "highest" | "non_stack" | "replace";
  duration?: "instant" | "round" | "scene" | "rest" | "equipped";
  condition?: string | null;
};
export type ItemMechanics = {
  equipment_slots: string[];
  damage_formula?: string | null;
  consume_mode: "none" | "quantity" | "charges";
  charges_max: number;
  recharge: "none" | "inn_rest" | "scene" | "dawn";
  slot_limit: number;
};
export type InventoryItem = {
  id: number; profile_id: string; item_path: string; item_title: string;
  note_id?: number | null; thumbnail?: string | null; cover?: string | null; damage_formula?: string | null;
  item_type?: string | null; description?: string | null; effects?: string[]; effect_rules?: ItemEffectRule[]; mechanics?: ItemMechanics; usable?: boolean;
  charges_current?: number | null; charges_max?: number | null; recharge?: string | null;
  quantity: number; equipped: boolean; notes?: string | null; updated_at: string;
  equipment_slot?: string | null;
};
export type PlayerIdea = {
  id: number; author: string; title: string; concept: string; appearance?: string | null;
  motivation?: string | null; world_connection?: string | null; status: string;
  gm_feedback?: string | null; created_at: string; updated_at: string;
};

export type CharacterSheetStep = {
  key: string;
  title: string;
  summary: string;
  status: "complete" | "pending";
  fields: Record<string, string | number | null>;
  missing_fields: string[];
  guide: {
    instruction?: string;
    checklist?: string[];
    calculations?: string[];
    sources?: Array<{
      kind: "race" | "class";
      title: string;
      intro?: string;
      rules?: Array<{ label: string; value: string }>;
      level_one?: Record<string, string>;
      abilities?: Array<{ title: string; text: string }>;
      tables?: Array<{ headers: string[]; rows: string[][] }>;
    }>;
  };
};

export type CharacterSheet = {
  profile_id: string;
  character_path: string;
  character_title: string;
  status: "draft" | "submitted" | "approved" | "changes_requested";
  completion_count: number;
  total_steps: number;
  steps: CharacterSheetStep[];
  submitted_at?: string | null;
  reviewed_at?: string | null;
  gm_feedback?: string | null;
  updated_at: string;
};

export type CharacterResource = {
  key: string;
  label: string;
  current: number;
  maximum: number;
  recharge?: string | null;
};

export type CharacterAttack = {
  attack_count?: number;
  base_attack_count?: number;
  id: string;
  name: string;
  attack_bonus?: number | null;
  base_attack_bonus?: number | null;
  item_attack_bonus?: number | null;
  damage?: string | null;
  range?: string | null;
  notes?: string | null;
  weapon_item_path?: string | null;
  equipment?: Array<{
    item_path: string;
    item_title: string;
    item_type?: string | null;
    equipment_slot?: string | null;
    thumbnail?: string | null;
    cover?: string | null;
    damage_formula?: string | null;
    role: "weapon" | "support";
  }>;
};

export type SessionAbility = {
  id: string;
  name: string;
  kind: "ability" | "power" | "technique" | "spell" | "resource" | "attack";
  group: string;
  circle?: number | null;
  description?: string | null;
  mechanics_status: "structured" | "partial";
  active?: boolean;
  blocked?: boolean;
  source?: string | null;
  requires_equipped_item?: string | null;
  requires_target?: boolean;
  uses?: {
    resource_key: string;
    label: string;
    maximum: number;
    recharge: string;
    cost?: number;
  } | null;
};

export type PlayableCharacterDefinition = {
  id: string;
  slug: string;
  name: string;
  portrait?: string | null;
  cover?: string | null;
  epithet?: string | null;
  race?: string | null;
  class_name?: string | null;
  level?: number | null;
  player_name?: string | null;
  campaign?: string | null;
  attributes?: Record<string, number | null> | null;
  base_attributes?: Record<string, number | null> | null;
  attribute_modifiers?: Record<string, number | null> | null;
  item_effects?: {
    totals: Record<string, number>;
    breakdown: Array<{ rule_id: string; item_path: string; item_title: string; kind: string; target: string; value: number; formula?: string | null; label?: string | null; stacking: string; condition?: string | null; active: boolean }>;
    skill_modifiers: Record<string, number>;
    resistances: string[];
    immunities: string[];
    vulnerabilities: string[];
  } | null;
  abilities?: Record<string, string> | null;
  session_abilities?: SessionAbility[] | null;
  attacks?: CharacterAttack[] | null;
  attack_notes?: string | null;
  defenses?: {
    armor_class?: number | null; base_armor_class?: number | null; unmodified_armor_class?: number | null; armor_modifier?: number;
    armor_modifier_source?: { item_path: string; item_title: string; value: number; kind: string } | null;
    saving_throw?: string | number | null; saving_throw_bonus?: number | null; initiative?: number | null; initiative_configured?: boolean;
  } | null;
  progression?: { experience?: number | null; base_attack?: number | null; maximum_hp?: number | null } | null;
  movement?: string | null;
  base_equipment?: string[] | null;
  public_description?: string | null;
  history?: string | null;
  relationships?: string | null;
  physical_description?: string | null;
  personality?: string | null;
  goals?: string | null;
  location?: string | null;
  current_status?: string | null;
  canonical_state?: string | null;
  source_vault?: string | null;
  definition_updated_at?: string | null;
  gm_fields?: { notes?: string; private_state?: string } | null;
};

export type PlayableCharacterState = {
  current_hp?: number | null;
  maximum_hp?: number | null;
  temporary_hp: number;
  conditions: string[];
  resources: CharacterResource[];
  coins?: number | null;
  copper_coins?: number | null;
  silver_coins?: number | null;
  platinum_coins?: number | null;
  location?: string | null;
  session_notes: string;
  updated_at: string;
  version: number;
};

export type PlayableCharacter = {
  access_level: "gm" | "owner" | "public";
  definition: PlayableCharacterDefinition;
  state?: PlayableCharacterState | null;
  inventory: InventoryItem[];
  permissions: {
    view_private_mechanics: boolean;
    edit_state: boolean;
    edit_definition: boolean;
    view_gm_fields: boolean;
    revert_events: boolean;
  };
};

export type PlayableCharacterSummary = {
  id: string;
  name: string;
  portrait?: string | null;
  epithet?: string | null;
  race?: string | null;
  class_name?: string | null;
  level?: number | null;
  current_hp?: number | null;
  maximum_hp?: number | null;
  armor_class?: number | null;
  initiative?: number | null;
  movement?: string | null;
  conditions: string[];
  resources: CharacterResource[];
  access_level: "gm" | "owner" | "public";
};

export type WorkspaceMessage = {
  id: number;
  actor_id: string;
  actor_name: string;
  actor_role: "gm" | "player";
  character_id?: string | null;
  message_kind: "message" | "action";
  text: string;
  created_at: string;
};

export type SessionLedgerEntry = {
  id: number;
  source_type: "workspace_message" | "character_event" | "dice_roll" | string;
  source_id: string;
  event_kind: "message" | "action" | "state" | "roll" | string;
  actor_id: string;
  actor_name: string;
  actor_role: "gm" | "player" | string;
  character_id?: string | null;
  title: string;
  detail?: Record<string, unknown> | null;
  visibility: string;
  created_at: string;
  voided_at?: string | null;
};

export type WorkspaceTokenSheet = {
  marker?: string;
  role?: string;
  level?: number | null;
  armor_class?: number | null;
  initiative?: number | null;
  description?: string;
  attacks?: Array<{ name: string; damage?: string; bonus?: string | number; notes?: string }>;
  abilities?: string[];
  notes?: string;
  source?: { catalog_id: string; monster_id: string; url: string; license: string };
  hit_dice?: string;
  hit_points?: string;
  saving_throw?: number | null;
  morale?: number | null;
  experience_points?: number | null;
  treasure?: string;
  movement?: string;
  category?: string;
  size?: string;
  alignment?: string;
  habitat?: string;
};

export type MonsterCatalogAttack = { raw: string; count: number | null; name: string; bonus: number | null; damage: string };
export type MonsterCatalogAbility = { name: string; description: string };
export type MonsterCatalogEntry = {
  id: string; name: string; source_url: string; category: string; size: string; alignment: string; habitat: string;
  encounter: string; experience: string; experience_points: number | null; treasure: string; movement: string;
  hit_dice: string; hit_points: string; average_hp: number | null; armor_class: number | null; saving_throw: number | null; morale: number | null;
  attacks: MonsterCatalogAttack[]; abilities: MonsterCatalogAbility[];
  image_path?: string | null; image_attribution?: string | null; image_license?: string | null;
  image_license_url?: string | null; image_source_url?: string | null;
};
export type MonsterCatalogResponse = {
  catalog: { id: string; title: string; edition: string; source_url: string; license: string; license_url: string; attribution: string; retrieved_on: string };
  art_collection?: { id: string; title: string; creator: string; publisher: string; source_url: string; license: string; license_url: string; modifications: string };
  count: number; total: number; image_count: number; monsters: MonsterCatalogEntry[];
};

export type WorkspaceToken = {
  id: string;
  token_type: "character" | "monster" | "location";
  map_id?: string;
  character_id?: string | null;
  name: string;
  image_path?: string | null;
  visible_to_players: boolean;
  color: string;
  latitude: number;
  longitude: number;
  current_hp?: number | null;
  maximum_hp?: number | null;
  conditions: string[];
  sheet?: WorkspaceTokenSheet;
  created_at: string;
  updated_at: string;
};

export type AttackResolution = {
  resolution_id: string;
  request_id: string;
  actor_character_id: string;
  actor_name: string;
  attack_id: string;
  attack_name: string;
  target_type: "character" | "token";
  target_id: string;
  target_name: string;
  roll_mode: "digital" | "physical";
  d20: number;
  attack_bonus: number;
  attack_total: number;
  target_ac: number;
  result: "hit" | "miss";
  damage_formula: string;
  damage_rolls: number[];
  damage_modifier: number;
  damage_total: number;
  breakdown: {
    strikes?: Array<{ d20: number; attack_total: number; result: "hit" | "miss"; damage_total: number; damage_rolls: number[] }>;
    effects?: CombatEffect[];
    attack?: { base_bonus?: number; equipment_bonus?: number; effect_bonus?: number; total_bonus?: number };
    damage?: { weapon_formula?: string; effective_formula?: string; rolls?: number[]; modifier?: number };
    equipment?: Array<{ item_path: string; item_title: string; role: string }>;
  };
  status: "pending" | "confirmed";
  confirmed: boolean;
  created_at: string;
  expires_at: string;
  confirmed_at?: string | null;
  hp_before?: number | null;
  hp_after?: number | null;
  ledger_id?: number | null;
};

export type CombatEffect = { id: string; target_type: "character" | "token"; target_id: string; label: string; source: string; duration: string; rounds: number | null; modifiers: Record<string, number>; updated_at: string };
export type CombatEffectsState = { round: number; version: number; effects: CombatEffect[]; encounter?: { active?: boolean; title?: string; map_id?: string; participants?: Array<{target_type: string; target_id: string; name: string; initiative: number}> } };
export type CombatTestView = { profile_id: string; character_name: string; receives_combat: boolean; state: CombatEffectsState };
export type CombatTestViewsResponse = { enabled: boolean; table_mode: "digital" | "physical" | "test"; views: CombatTestView[] };
export async function getCombatEffects(): Promise<CombatEffectsState> { return worldRequest("/combat/effects"); }
export async function getCombatTestViews(): Promise<CombatTestViewsResponse> { return worldRequest("/gm/combat/test-views"); }
export async function sendCombatEffectCommand(payload: { request_id: string; expected_version: number; action: string; payload: Record<string, unknown> }): Promise<CombatEffectsState> {
  return worldRequest("/gm/combat/effects", { method: "POST", body: JSON.stringify(payload) });
}

export type SessionItem = {
  id: number;
  item_path: string;
  name: string;
  item_type: string;
  description?: string | null;
  effects: string[];
  effect_rules: ItemEffectRule[];
  mechanics: ItemMechanics;
  usable: boolean;
  image_path?: string | null;
  created_at: string;
  updated_at: string;
};

export type LootReward = {
  id: string;
  kind: string;
  name: string;
  quantity: number;
  description?: string | null;
  source_code?: string | null;
  editable?: boolean;
  requires_identification?: boolean;
  gm_notes?: string | null;
};

export type LootResolution = {
  resolution_id: string;
  request_id: string;
  source_type: "token" | "lair";
  source_id: string;
  source_name: string;
  treasure_code: string;
  treasure_scope: "carried" | "lair";
  roll_mode: "digital" | "quick" | "requested";
  rewards: LootReward[];
  rolls: Array<Record<string, unknown>>;
  status: "draft" | "revealed" | "distributed";
  created_at: string;
  revealed_at?: string | null;
  distributed_at?: string | null;
  allocations: Array<{ reward_id: string; character_id: string; quantity: number }>;
  pending_requests: Array<{ task_id: string; purpose: string; formula: string; roll_request_id: number; roller_character_id: string }>;
  finalized_at?: string | null;
};

export type WorkspaceIcon = {
  id: string;
  label: string;
  category: "map" | "items";
  path: string;
  created_at: string;
};

export type WorkspacePresence = {
  actor_id: string;
  actor_name: string;
  actor_role: "gm" | "player";
  character_id?: string | null;
  last_seen_at: string;
  online: boolean;
};

export type WorkspaceFogLayer = {
  enabled: boolean;
  revealed_cells: string[];
  mist_density: Record<string, number>;
  columns: number;
  rows: number;
  updated_at?: string | null;
};

export type WorkspaceFog = {
  exploration: WorkspaceFogLayer;
  battle: WorkspaceFogLayer;
};

export type WorkspaceSnapshot = {
  table_mode: "digital" | "physical" | "test";
  active_map_id?: string | null;
  map?: WorkspaceMap | null;
  messages: WorkspaceMessage[];
  presence: WorkspacePresence[];
  tokens: WorkspaceToken[];
  fog?: WorkspaceFog;
  view?: { zoom: number; scroll_left: number; scroll_top: number };
};

export type WorkspaceMap = {
  id: string;
  title: string;
  image_path: string;
  visible_to_players: boolean;
  updated_at: string;
};

export type CharacterEvent = {
  id: number;
  character_id: string;
  session_id?: string | null;
  actor_id: string;
  actor_role: string;
  event_type: string;
  field: string;
  before?: unknown;
  after?: unknown;
  reason?: string | null;
  created_at: string;
  reverted_at?: string | null;
  reverted_by?: string | null;
};

export type DiceVisibility = "table" | "gm" | "owner" | "private";
export type DiceRollEvent = {
  id: number;
  request_id: string;
  session_id?: string | null;
  campaign_id: string;
  character_id?: string | null;
  actor_id: string;
  actor_role: "gm" | "player";
  roll_type: string;
  label: string;
  formula: string;
  dice: string;
  modifier: number;
  individual_results: number[];
  subtotal: number;
  total: number;
  target_value?: number | null;
  target_hidden: boolean;
  outcome?: "success" | "failure" | null;
  visibility: DiceVisibility;
  source: string;
  source_id?: string | null;
  scene_id?: number | null;
  action_id?: number | null;
  reason?: string | null;
  created_at: string;
  voided: boolean;
  voided_at?: string | null;
  voided_by?: string | null;
  void_reason?: string | null;
};

export type DiceRollRequest = {
  id: number;
  request_id: string;
  session_id?: string | null;
  campaign_id: string;
  character_id: string;
  requested_by: string;
  roll_type: string;
  label: string;
  formula: string;
  visibility: DiceVisibility;
  source: string;
  source_id?: string | null;
  scene_id?: number | null;
  action_id?: number | null;
  target_value?: number | null;
  target_hidden: boolean;
  reason?: string | null;
  status: string;
  created_at: string;
  expires_at: string;
  completed_at?: string | null;
  completed_by?: string | null;
  completion_request_id?: string | null;
  roll_event_id?: number | null;
};

export type GameSession = {
  id: number; request_id: string; campaign_id: string; title: string; session_number?: number | null;
  status: string; started_at?: string | null; ended_at?: string | null; created_by: string;
  private_notes?: string | null; image_path?: string | null; public_summary?: string | null;
  public_chronicle?: string | null; gm_summary?: string | null; created_at: string; version: number;
};

export type CampaignNarrativeEntry = {
  title?: string;
  description?: string;
  status?: string;
  character_id?: string;
  name?: string;
  quantity?: number;
  holder_character_id?: string;
};

export type CampaignNarrative = {
  participants: Array<{ character_id?: string | null; name: string; portrait?: string | null }>;
  locations: CampaignNarrativeEntry[];
  missions: CampaignNarrativeEntry[];
  discoveries: CampaignNarrativeEntry[];
  rewards: CampaignNarrativeEntry[];
  items_acquired: CampaignNarrativeEntry[];
  world_events: CampaignNarrativeEntry[];
  character_events: CampaignNarrativeEntry[];
  open_threads: CampaignNarrativeEntry[];
  tags: string[];
};

export type CampaignSession = Omit<GameSession, "created_by" | "private_notes"> & {
  created_by?: string;
  private_notes?: string | null;
  narrative: CampaignNarrative;
  gm_analysis?: { source_status?: string; companion_feedback?: CampaignNarrativeEntry[] };
  source_refs?: Array<{ path: string; sha256: string; evidence: string[] }>;
};

export type SceneParticipant = {
  id: number; scene_id: number; participant_type: string; character_id?: string | null;
  npc_name?: string | null; npc_source?: string | null; public_label: string;
  public_status?: string | null; private_status?: string | null; visible_to_players: boolean;
  order_index: number;
  joined_at: string; left_at?: string | null; character?: PlayableCharacterSummary | null; npc?: NpcRecord | null;
};

export type SceneElement = {
  id: number; request_id: string; scene_id: number; element_type: string; title: string;
  public_description?: string | null; private_description?: string | null; status: string;
  visibility: DiceVisibility; discovered_at?: string | null; discovered_by?: string | null;
  created_by: string; created_at: string; version: number;
};

export type SceneAction = {
  id: number; request_id: string; scene_id: number; character_id?: string | null;
  actor_id: string; actor_role: "gm" | "player"; action_type: string; description: string;
  target_label?: string | null; status: string; visibility: DiceVisibility;
  requested_roll_id?: number | null; resulting_roll_id?: number | null; resolution?: string | null;
  created_at: string; resolved_at?: string | null; resolved_by?: string | null; rejection_reason?: string | null;
};

export type SceneEvent = {
  id: number; event_key?: string | null; scene_id: number; session_id?: number | null;
  actor_id: string; actor_role: "gm" | "player"; event_type: string; title: string;
  public_text?: string | null; private_text?: string | null; character_id?: string | null;
  roll_id?: number | null; character_event_id?: number | null; action_id?: number | null;
  visibility: DiceVisibility; created_at: string; voided: boolean; voided_at?: string | null;
  voided_by?: string | null; void_reason?: string | null; roll?: DiceRollEvent | null;
};

export type GameScene = {
  id: number; request_id: string; campaign_id: string; session_id?: number | null; title: string;
  location_name: string; location_source?: string | null; public_description?: string | null;
  objective?: string | null; private_notes?: string | null; resolution_summary?: string | null;
  image_path?: string | null;
  map_id?: string | null;
  checklist?: Record<string, boolean>;
  map_zoom?: number;
  map_scroll_left?: number;
  map_scroll_top?: number;
  status: string; visibility: DiceVisibility; created_by: string; created_at: string;
  activated_at?: string | null; closed_at?: string | null; order_index: number; version: number;
  participants: SceneParticipant[]; elements: SceneElement[]; actions: SceneAction[]; events: SceneEvent[];
  contract_links?: ContractSceneLink[];
};

export type ContractStatus = "draft" | "published" | "accepted" | "active" | "completed" | "failed" | "abandoned" | "cancelled";
export type ContractObjectiveStatus = "hidden" | "available" | "active" | "completed" | "failed" | "skipped";
export type ContractRewardType = "currency" | "item" | "reputation" | "information" | "favor" | "access" | "custom";
export type ContractRewardStatus = "proposed" | "approved" | "delivered" | "withheld" | "cancelled";

export type ContractObjective = {
  id: number; request_id: string; contract_id: number; title: string; public_description: string;
  private_description?: string | null; objective_type: string; status: ContractObjectiveStatus;
  required: boolean; order_index: number; progress_current?: number | null; progress_target?: number | null;
  revealed_to_players: boolean; completed_at?: string | null; completed_by?: string | null;
  created_at: string; version: number;
};

export type ContractAssignment = {
  id: number; request_id: string; contract_id: number; character_id: string; assigned_by?: string | null;
  assigned_at: string; status: string; left_at?: string | null; public_role?: string | null;
};

export type ContractSceneLink = {
  id: number; request_id: string; contract_id: number; scene_id: number; objective_id?: number | null;
  link_type: string; created_by: string; created_at: string; scene_title?: string | null; scene_status?: string | null;
  scene_visibility?: string | null; objective_title?: string | null; objective_revealed?: boolean | number | null;
  objective_status?: string | null; contract_title?: string | null; contract_status?: string | null;
};

export type ContractReward = {
  id: number; request_id: string; contract_id: number; reward_type: ContractRewardType; label: string;
  description?: string | null; quantity?: number | null; currency_type?: string | null; item_source?: string | null;
  item_name?: string | null; reputation_faction?: string | null; reputation_amount?: number | null;
  visibility: DiceVisibility; status: ContractRewardStatus; created_by: string; created_at: string;
  approved_at?: string | null; approved_by?: string | null; delivered_at?: string | null; version: number;
};

export type ContractEvent = {
  id: number; event_key?: string | null; contract_id: number; actor_id: string; actor_role: "gm" | "player";
  event_type: string; title: string; public_text?: string | null; private_text?: string | null;
  objective_id?: number | null; scene_id?: number | null; character_id?: string | null; reward_id?: number | null;
  visibility: DiceVisibility; created_at: string; voided_at?: string | null; voided_by?: string | null;
  void_reason?: string | null; voided?: boolean;
};

export type ContractRecord = {
  id: number; request_id: string; campaign_id: string; session_id?: number | null; title: string;
  slug?: string | null; contract_type: string; status: ContractStatus; issuer_name: string;
  issuer_type?: string | null; issuer_source?: string | null; location_name?: string | null; location_source?: string | null;
  public_summary: string; public_briefing: string; private_briefing?: string | null; risk_label: string;
  recommended_level?: string | null; deadline_text?: string | null; visibility: string; created_by: string;
  created_at: string; published_at?: string | null; accepted_at?: string | null; started_at?: string | null;
  resolved_at?: string | null; version: number; objectives: ContractObjective[]; assignments: ContractAssignment[];
  scene_links: ContractSceneLink[]; rewards: ContractReward[]; events: ContractEvent[];
  revealed_objective_count: number; assigned_character_ids: string[]; npcs?: NpcContractLink[];
};

/** Operational mission focus; published contracts remain available, not current. */
export function getCurrentOperationalContract(contracts: ContractRecord[]): ContractRecord | undefined {
  return contracts.find((contract) => contract.status === "active")
    || contracts.find((contract) => contract.status === "accepted");
}

export type NpcRelationship = {
  id: number; npc_id: number; target_type: "character" | "npc" | "faction" | "group";
  target_id?: string | null; target_label: string; public_label?: string | null; private_label?: string | null;
  attitude_value?: number | null; trust_value?: number | null; fear_value?: number | null; respect_value?: number | null;
  status: string; public_notes?: string | null; private_notes?: string | null; visible_to_players: boolean;
  created_at: string; updated_at: string; version: number;
};

export type NpcMemory = {
  id: number; npc_id: number; memory_type: string; title: string; summary: string; private_details?: string | null;
  subject_type?: string | null; subject_id?: string | null; subject_label?: string | null; scene_id?: number | null;
  contract_id?: number | null; character_id?: string | null; importance: "low" | "medium" | "high" | "critical";
  confidence: "confirmed" | "believed" | "suspected" | "doubtful" | "false_known_by_npc";
  visibility: DiceVisibility; status: string; occurred_at?: string | null; learned_at: string; forgotten_at?: string | null;
  created_at: string; updated_at: string; version: number; responsible_party?: string | null; beneficiary?: string | null;
  due_text?: string | null; fulfilled_at?: string | null; obligation_status?: string | null;
  linked_contract_id?: number | null; linked_scene_id?: number | null; contradicts_memory_id?: number | null;
};

export type NpcEncounter = {
  id: number; npc_id: number; scene_id: number; contract_id?: number | null; session_id?: number | null; title: string;
  public_summary?: string | null; private_summary?: string | null; occurred_at: string; created_at: string;
};

export type NpcEvent = {
  id: number; npc_id: number; actor_id: string; actor_role: string; event_type: string; title: string;
  public_text?: string | null; private_text?: string | null; relationship_id?: number | null; memory_id?: number | null;
  encounter_id?: number | null; scene_id?: number | null; contract_id?: number | null; character_id?: string | null;
  visibility: DiceVisibility; created_at: string; voided?: boolean; voided_at?: string | null; void_reason?: string | null;
};

export type NpcContractLink = {
  id: number; npc_id: number; contract_id: number; role?: string | null; visible_to_players: boolean;
  name?: string; portrait_path?: string | null; class_or_role?: string | null; occupation?: string | null; created_at: string;
};

export type NpcRecord = {
  id: number; campaign_id: string; source_path?: string | null; slug: string; name: string; aliases: string[];
  portrait_path?: string | null; race?: string | null; class_or_role?: string | null; occupation?: string | null;
  faction_names: string[]; public_description?: string | null; private_description?: string | null;
  canonical_status?: string | null; visible_to_players: boolean; current_location?: string | null; current_location_id?: number | null; active_journey_id?: number | null;
  public_status?: string | null; private_status?: string | null; disposition_summary?: string | null; active?: boolean;
  last_seen_at?: string | null; last_scene_id?: number | null; state_version?: number; version: number;
  relationships?: NpcRelationship[]; memories?: NpcMemory[]; encounters?: NpcEncounter[]; events?: NpcEvent[];
  contract_links?: NpcContractLink[];
};

export type WorldMapRecord = {
  id: number; title: string; source_path?: string | null; image_path?: string | null;
  map_type: string; width?: number | null; height?: number | null; coordinate_system: string;
  public_description?: string | null; private_description?: string | null;
  visibility: string; active: boolean; version: number;
};

export type WorldLocationRecord = {
  id: number; map_id?: number | null; source_path?: string | null; slug: string; name: string;
  aliases: string[]; location_type: string; parent_location_id?: number | null;
  territory_name?: string | null; public_description?: string | null; private_description?: string | null;
  portrait_or_cover_path?: string | null; marker_icon?: string | null; x?: number | null; y?: number | null;
  latitude?: number | null; longitude?: number | null; knowledge_level?: string;
  public_status?: string | null; private_status?: string | null; controlling_faction?: string | null;
  danger_label?: string | null; accessible?: boolean; current_scene_id?: number | null;
  visibility: string; active: boolean; version: number; state_version?: number;
};

export type TravelRouteRecord = {
  id: number; origin_location_id: number; destination_location_id: number; title: string;
  route_type: string; public_description?: string | null; distance_value?: number | null;
  distance_unit?: string | null; duration_value?: number | null; duration_unit?: string | null;
  difficulty_label?: string | null; danger_label?: string | null; public: boolean; version: number;
};

export type JourneyParticipantRecord = {
  id: number; journey_id: number; participant_type: string; character_id?: string | null;
  npc_id?: number | null; public_label: string; status: string;
};

export type JourneyEventRecord = {
  id: number; journey_id: number; event_type: string; title: string; public_text?: string | null;
  private_text?: string | null; visibility: string; created_at: string; voided?: boolean;
};

export type JourneyRecord = {
  id: number; route_id?: number | null; contract_id?: number | null; session_id?: number | null;
  origin_location_id: number; destination_location_id: number; title: string;
  status: "planned" | "active" | "paused" | "completed" | "cancelled" | "failed";
  visibility: string; planned_duration_value?: number | null; planned_duration_unit?: string | null;
  progress_current: number; progress_target: number; version: number;
  participants: JourneyParticipantRecord[]; scene_links: Array<Record<string, unknown>>;
  events?: JourneyEventRecord[];
};

export type ReputationLedger = {
  id: number; request_id: string; campaign_id: string; character_id?: string | null; party_id?: string | null;
  faction_name: string; delta: number; resulting_value: number; reason: string; contract_id?: number | null;
  actor_id: string; actor_role: "gm" | "player"; created_at: string; reverted_at?: string | null;
  reverted_by?: string | null; reverted?: boolean;
};

export function newDiceRequestId(prefix = "roll") {
  const suffix = typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `${prefix}-${suffix}`;
}

export async function getPlayerProfile(): Promise<PlayerProfile> {
  const response = await fetch(`${API_BASE}/player/profile`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao carregar perfil do jogador");
  return response.json();
}

export async function listPlayerDiscoveries(): Promise<PlayerDiscovery[]> {
  const response = await fetch(`${API_BASE}/player/discoveries`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao carregar descobertas");
  return response.json();
}

export async function listGmDiscoveries(): Promise<PlayerDiscovery[]> {
  const response = await fetch(`${API_BASE}/gm/discoveries`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao carregar descobertas dos jogadores");
  return response.json();
}

export async function revealPlayerDiscovery(profileId: string, noteId: number): Promise<PlayerDiscovery> {
  const response = await fetch(`${API_BASE}/gm/discoveries`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ profile_id: profileId, note_id: noteId }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao revelar descoberta");
  return response.json();
}

export async function revokePlayerDiscovery(discoveryId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/gm/discoveries/${discoveryId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error("Falha ao revogar descoberta");
}

export async function listPlayerFeed(): Promise<PlayerEvent[]> {
  const response = await fetch(`${API_BASE}/player/feed`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao carregar novidades");
  return response.json();
}

export async function markPlayerFeedRead(eventIds: number[]): Promise<void> {
  const response = await fetch(`${API_BASE}/player/feed/read`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ event_ids: eventIds }),
  });
  if (!response.ok) throw new Error("Falha ao marcar novidades como lidas");
}

export async function listPlayerQuests(): Promise<PlayerQuest[]> {
  const response = await fetch(`${API_BASE}/player/quests`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao carregar missões pessoais");
  return response.json();
}

export async function listGmQuests(): Promise<PlayerQuest[]> {
  const response = await fetch(`${API_BASE}/gm/quests`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao carregar progresso de missões");
  return response.json();
}

export async function updatePlayerQuest(payload: {
  profile_id: string;
  note_id: number;
  status: PlayerQuestStatus;
  progress?: string;
}): Promise<PlayerQuest> {
  const response = await fetch(`${API_BASE}/gm/quests`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao atualizar missão");
  return response.json();
}

export async function getEditableNote(path: string): Promise<EditableNote> {
  const response = await fetch(`${API_BASE}/gm/editor?path=${encodeURIComponent(path)}`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao abrir editor");
  return response.json();
}

export async function saveEditableNote(note: EditableNote): Promise<EditableNote> {
  const response = await fetch(`${API_BASE}/gm/editor`, {
    method: "PUT", headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ path: note.path, content: note.content, expected_hash: note.content_hash }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao salvar nota");
  return response.json();
}

export async function listPlayerInventory(): Promise<InventoryItem[]> {
  const response = await fetch(`${API_BASE}/player/inventory`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao carregar inventário");
  return response.json();
}

export async function listGmInventory(): Promise<InventoryItem[]> {
  const response = await fetch(`${API_BASE}/gm/inventory`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao carregar inventários");
  return response.json();
}

export async function updateInventory(payload: { profile_id: string; note_id: number; quantity: number; equipped: boolean; notes?: string }): Promise<InventoryItem> {
  const response = await fetch(`${API_BASE}/gm/inventory`, {
    method: "POST", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao atualizar inventário");
  return response.json();
}

export async function submitPlayerIdea(payload: { title: string; concept: string; appearance?: string; motivation?: string; world_connection?: string }): Promise<PlayerIdea> {
  const response = await fetch(`${API_BASE}/player/ideas`, { method: "POST", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload) });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao enviar ideia");
  return response.json();
}

export async function listGmIdeas(): Promise<PlayerIdea[]> {
  const response = await fetch(`${API_BASE}/gm/ideas`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao carregar ideias");
  return response.json();
}

export async function reviewPlayerIdea(id: number, status: string, feedback?: string): Promise<PlayerIdea> {
  const response = await fetch(`${API_BASE}/gm/ideas/${id}`, { method: "PATCH", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ status, feedback }) });
  if (!response.ok) throw new Error("Falha ao revisar ideia");
  return response.json();
}

export async function getPlayerCharacterSheet(): Promise<CharacterSheet> {
  const response = await fetch(`${API_BASE}/player/character-sheet`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar ficha");
  return response.json();
}

export async function savePlayerCharacterSheetStep(stepKey: string, fields: Record<string, string | number | null>): Promise<CharacterSheet> {
  const response = await fetch(`${API_BASE}/player/character-sheet`, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ step_key: stepKey, fields }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao salvar etapa");
  return response.json();
}

export async function submitPlayerCharacterSheet(): Promise<CharacterSheet> {
  const response = await fetch(`${API_BASE}/player/character-sheet/submit`, { method: "POST", headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao entregar ficha");
  return response.json();
}

export async function listGmCharacterSheets(): Promise<CharacterSheet[]> {
  const response = await fetch(`${API_BASE}/gm/character-sheets`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao carregar fichas dos jogadores");
  return response.json();
}

export async function reviewCharacterSheet(profileId: string, status: "approved" | "changes_requested", feedback?: string): Promise<CharacterSheet> {
  const response = await fetch(`${API_BASE}/gm/character-sheets/${encodeURIComponent(profileId)}`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ status, feedback }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao revisar ficha");
  return response.json();
}

export async function listPlayableCharacters(): Promise<PlayableCharacterSummary[]> {
  const response = await fetch(`${API_BASE}/characters`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar personagens");
  return response.json();
}

export async function sendPlayerNotification(payload: { profile_id: string; title: string; message: string }): Promise<PlayerEvent> {
  const response = await fetch(`${API_BASE}/gm/player-notifications`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao enviar notificação");
  return response.json();
}

export async function recordRuntimeEvent(eventType: string, payload: Record<string, unknown> = {}): Promise<void> {
  const response = await fetch(`${API_BASE}/player/runtime/events`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ event_id: `${eventType}:${Date.now()}:${crypto.randomUUID?.() || Math.random().toString(36).slice(2)}`, event_type: eventType, payload }),
  });
  if (!response.ok) throw new Error("Falha ao registrar navegação");
}

export async function getSessionWorkspace(mapId?: string): Promise<WorkspaceSnapshot> {
  const query = mapId ? `?map_id=${encodeURIComponent(mapId)}` : "";
  const response = await fetch(`${API_BASE}/workspace${query}`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar a mesa");
  return response.json();
}

export async function listSessionLedger(limit = 500): Promise<SessionLedgerEntry[]> {
  const response = await fetch(`${API_BASE}/workspace/ledger?limit=${Math.max(1, Math.min(1000, limit))}`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar registro da sessão");
  return response.json();
}

export async function connectSessionRealtime(onChange: (ledgerId: number) => void): Promise<() => void> {
  let stopped = false;
  let socket: WebSocket | null = null;
  let reconnectTimer = 0;
  let pingTimer = 0;

  const connect = async () => {
    if (stopped) return;
    try {
      const ticketResponse = await fetch(`${API_BASE}/workspace/realtime-ticket`, { method: "POST", headers: authHeaders() });
      if (!ticketResponse.ok) throw new Error("Ticket em tempo real indisponível");
      const { ticket } = await ticketResponse.json() as { ticket: string };
      const base = new URL(API_BASE || window.location.origin, window.location.href);
      const protocol = base.protocol === "https:" ? "wss:" : "ws:";
      const prefix = API_BASE ? base.pathname.replace(/\/$/, "") : "";
      socket = new WebSocket(`${protocol}//${base.host}${prefix}/ws/session?ticket=${encodeURIComponent(ticket)}`);
      socket.onopen = () => {
        window.clearInterval(pingTimer);
        pingTimer = window.setInterval(() => { if (socket?.readyState === WebSocket.OPEN) socket.send("ping"); }, 25_000);
      };
      socket.onmessage = (event) => {
        if (event.data === "pong") return;
        try {
          const payload = JSON.parse(String(event.data)) as { type?: string; ledger_id?: number };
          if (payload.type === "session_changed" && Number.isFinite(payload.ledger_id)) {
            window.dispatchEvent(new CustomEvent("omnisvera-session-changed", { detail: Number(payload.ledger_id) }));
            onChange(Number(payload.ledger_id));
          }
        } catch { /* Mensagens desconhecidas não interrompem a sessão. */ }
      };
      socket.onclose = () => {
        window.clearInterval(pingTimer);
        if (!stopped) reconnectTimer = window.setTimeout(() => void connect(), 1800);
      };
    } catch {
      if (!stopped) reconnectTimer = window.setTimeout(() => void connect(), 2500);
    }
  };
  await connect();
  return () => {
    stopped = true;
    window.clearTimeout(reconnectTimer);
    window.clearInterval(pingTimer);
    socket?.close();
  };
}

export async function heartbeatSessionWorkspace(): Promise<WorkspacePresence> {
  const response = await fetch(`${API_BASE}/workspace/heartbeat`, { method: "POST", headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao atualizar presença");
  return response.json();
}

export async function leaveSessionWorkspace(): Promise<void> {
  const response = await fetch(`${API_BASE}/workspace/leave`, { method: "POST", headers: authHeaders(), keepalive: true });
  if (!response.ok) throw new Error("Falha ao registrar saída da sessão");
}

export async function sendWorkspaceMessage(text: string, messageKind: "message" | "action" = "message"): Promise<WorkspaceMessage> {
  const response = await fetch(`${API_BASE}/workspace/messages`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ text, message_kind: messageKind }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao enviar mensagem");
  return response.json();
}

export async function uploadWorkspaceMap(payload: { title: string; filename: string; content_type: string; data_base64: string; visible_to_players: boolean }): Promise<WorkspaceMap> {
  const response = await fetch(`${API_BASE}/gm/workspace/map`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao trocar o mapa");
  return response.json();
}

export async function listWorkspaceMaps(): Promise<WorkspaceMap[]> {
  const response = await fetch(`${API_BASE}/workspace/maps`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar mapas");
  return response.json();
}

export async function listWorkspaceIcons(): Promise<WorkspaceIcon[]> {
  const response = await fetch(`${API_BASE}/workspace/icons`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar ícones");
  return response.json();
}

export async function uploadWorkspaceIcon(payload: { label: string; category: "map" | "items"; filename: string; content_type: string; data_base64: string }): Promise<WorkspaceIcon> {
  const response = await fetch(`${API_BASE}/gm/workspace/icons`, {
    method: "POST", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar ícone");
  return response.json();
}

export async function uploadWorkspaceIconFile(payload: { label: string; category: "map" | "items"; file: File }): Promise<WorkspaceIcon> {
  if (payload.file.size > 25 * 1024 * 1024) throw new Error("A imagem deve possuir no máximo 25 MB.");
  const query = new URLSearchParams({ label: payload.label, category: payload.category });
  const url = `${API_BASE}/gm/workspace/icons/file?${query}`;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const response = await fetch(url, {
        method: "POST", headers: authHeaders({ "Content-Type": payload.file.type || "application/octet-stream" }), body: payload.file,
      });
      if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar ícone");
      return response.json();
    } catch (reason) {
      if (!(reason instanceof TypeError) || attempt > 0) {
        if (reason instanceof TypeError) throw new Error("A conexão caiu durante o envio da imagem. Tente selecioná-la novamente.");
        throw reason;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 500));
    }
  }
  throw new Error("Não foi possível enviar a imagem.");
}

export async function selectWorkspaceMap(mapId: string): Promise<WorkspaceMap> {
  const response = await fetch(`${API_BASE}/gm/workspace/maps/active`, { method: "PATCH", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ map_id: mapId }) });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao trocar mapa");
  return response.json();
}

export async function updateWorkspaceMapVisibility(mapId: string, visibleToPlayers: boolean): Promise<WorkspaceMap> {
  const response = await fetch(`${API_BASE}/gm/workspace/maps/${encodeURIComponent(mapId)}/visibility`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ visible_to_players: visibleToPlayers }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao alterar a visibilidade do mapa");
  return response.json();
}

export async function updateWorkspaceView(payload: { zoom: number; scroll_left: number; scroll_top: number }): Promise<{ zoom: number; scroll_left: number; scroll_top: number }> {
  const response = await fetch(`${API_BASE}/gm/workspace/view`, {
    method: "PATCH", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao salvar a posição do mapa");
  return response.json();
}

export async function updateWorkspaceTableMode(tableMode: "digital" | "physical" | "test"): Promise<{ table_mode: "digital" | "physical" | "test" }> {
  const response = await fetch(`${API_BASE}/gm/workspace/table-mode`, {
    method: "PATCH", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ table_mode: tableMode }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao alterar o modo da mesa");
  return response.json();
}

export async function updateWorkspaceFog(payload: { map_id: string; layer: "exploration" | "battle"; enabled: boolean; revealed_cells: string[]; mist_density: Record<string, number> }): Promise<WorkspaceFogLayer> {
    const request = (method: "POST" | "PATCH") => fetch(`${API_BASE}/gm/workspace/fog`, {
      method, headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload),
    });
    let response = await request("POST");
    // Backends antigos expõem esta rota apenas como PATCH. Mantemos compatibilidade
    // durante a atualização do túnel, sem esconder outros erros de autenticação/validação.
    if (response.status === 405) response = await request("PATCH");
    if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao atualizar fog do mapa");
    return response.json();
  }

export async function createWorkspaceToken(payload: {
  token_type: "character" | "monster" | "location"; character_id?: string; name: string;
  map_id?: string;
  image_path?: string | null; image_filename?: string; image_data_base64?: string;
  visible_to_players?: boolean;
  color?: string; latitude?: number; longitude?: number; current_hp?: number; maximum_hp?: number;
  conditions?: string[]; sheet?: WorkspaceTokenSheet;
}): Promise<WorkspaceToken> {
  const response = await fetch(`${API_BASE}/gm/workspace/tokens`, {
    method: "POST", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao criar marcador");
  return response.json();
}

export async function moveWorkspaceToken(tokenId: string, latitude: number, longitude: number): Promise<WorkspaceToken> {
  const response = await fetch(`${API_BASE}/gm/workspace/tokens/${encodeURIComponent(tokenId)}/position`, {
    method: "PATCH", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ latitude, longitude }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao mover marcador");
  return response.json();
}

export async function updateWorkspaceToken(tokenId: string, fields: { name?: string; image_path?: string | null; visible_to_players?: boolean; color?: string; current_hp?: number; maximum_hp?: number; conditions?: string[]; sheet?: WorkspaceTokenSheet }): Promise<WorkspaceToken> {
  const response = await fetch(`${API_BASE}/gm/workspace/tokens/${encodeURIComponent(tokenId)}`, {
    method: "PATCH", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(fields),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao editar marcador");
  return response.json();
}

export async function removeWorkspaceToken(tokenId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/gm/workspace/tokens/${encodeURIComponent(tokenId)}`, { method: "DELETE", headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao remover marcador");
}

export async function listSessionItems(): Promise<SessionItem[]> {
  const response = await fetch(`${API_BASE}/gm/workspace/items`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar itens da sessão");
  return response.json();
}

export async function listWorkspaceTargetInventory(targetId: string): Promise<InventoryItem[]> {
  const response = await fetch(`${API_BASE}/gm/workspace/inventory/${encodeURIComponent(targetId)}`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar o inventário");
  return response.json();
}

export async function removeWorkspaceTargetItem(payload: { target_id: string; item_path: string; quantity: number }): Promise<InventoryItem[]> {
  const response = await fetch(`${API_BASE}/gm/workspace/inventory/remove`, {
    method: "POST", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao retirar o item");
  return response.json();
}

export async function listWorkspaceItemCatalog(): Promise<NoteSummary[]> {
  const response = await fetch(`${API_BASE}/gm/workspace/item-catalog`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar o catálogo de itens");
  return response.json();
}

export async function listWorkspaceMonsterCatalog(): Promise<MonsterCatalogResponse> {
  const response = await fetch(`${API_BASE}/gm/workspace/monster-catalog`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar o bestiário");
  return response.json();
}

export async function listWorkspaceLoot(): Promise<LootResolution[]> {
  const response = await fetch(`${API_BASE}/workspace/loot`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar espólios");
  return response.json();
}

export async function resolveWorkspaceLoot(payload: {
  request_id: string; token_id: string; scope: "carried" | "lair"; roll_mode: "digital" | "quick" | "requested"; lair_id?: string; roller_character_id?: string;
}): Promise<LootResolution> {
  const response = await fetch(`${API_BASE}/gm/workspace/loot/resolve`, {
    method: "POST", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao gerar espólio");
  return response.json();
}

export async function finalizeWorkspaceLootRolls(resolutionId: string): Promise<LootResolution> {
  const response = await fetch(`${API_BASE}/gm/workspace/loot/${encodeURIComponent(resolutionId)}/finalize-rolls`, { method: "POST", headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Ainda existem rolagens de tesouro pendentes");
  return response.json();
}

export async function updateWorkspaceLoot(resolutionId: string, rewards: LootReward[]): Promise<LootResolution> {
  const response = await fetch(`${API_BASE}/gm/workspace/loot/${encodeURIComponent(resolutionId)}`, {
    method: "PATCH", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ rewards }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao editar espólio");
  return response.json();
}

export async function revealWorkspaceLoot(resolutionId: string): Promise<LootResolution> {
  const response = await fetch(`${API_BASE}/gm/workspace/loot/${encodeURIComponent(resolutionId)}/reveal`, { method: "POST", headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao revelar espólio");
  return response.json();
}

export async function distributeWorkspaceLoot(resolutionId: string, payload: {
  request_id: string; allocations: Array<{ reward_id: string; character_id: string; quantity: number }>;
}): Promise<LootResolution> {
  const response = await fetch(`${API_BASE}/gm/workspace/loot/${encodeURIComponent(resolutionId)}/distribute`, {
    method: "POST", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao distribuir espólio");
  return response.json();
}

export async function saveSessionItem(payload: {
  name: string; item_type: string; description?: string; effects: string[]; effect_rules: ItemEffectRule[]; mechanics: ItemMechanics; usable: boolean; image_path?: string | null;
}, itemId?: number): Promise<SessionItem> {
  const response = await fetch(`${API_BASE}/gm/workspace/items${itemId ? `/${itemId}` : ""}`, {
    method: itemId ? "PATCH" : "POST", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao salvar item");
  return response.json();
}

export async function deleteSessionItem(itemId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/gm/workspace/items/${itemId}`, { method: "DELETE", headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao destruir item");
}

export async function grantSessionItem(payload: {
  character_id: string; item_id: number; quantity: number; equipped?: boolean; notes?: string;
}): Promise<{ item: SessionItem; character: PlayableCharacter }> {
  const response = await fetch(`${API_BASE}/gm/workspace/items/grant`, {
    method: "POST", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao conceder item");
  return response.json();
}

export async function rechargeSessionItems(cycle: "scene" | "dawn"): Promise<{ cycle: string; recharged: number }> {
  const response = await fetch(`${API_BASE}/gm/workspace/items/recharge/${cycle}`, {
    method: "POST", headers: authHeaders(),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao recarregar itens");
  return response.json();
}

export async function getPlayableCharacter(profileId: string): Promise<PlayableCharacter> {
  const response = await fetch(`${API_BASE}/characters/${encodeURIComponent(profileId)}`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar ficha de jogo");
  return response.json();
}

export type CharacterNotes = { character_id: string; content: string; version: number; updated_at: string | null };

export async function getCharacterNotes(profileId: string): Promise<CharacterNotes> {
  const response = await fetch(`${API_BASE}/characters/${encodeURIComponent(profileId)}/notes`, { headers: authHeaders(), cache: "no-store" });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Não foi possível carregar as anotações.");
  return response.json();
}

export async function saveCharacterNotes(profileId: string, content: string, version: number): Promise<CharacterNotes> {
  const response = await fetch(`${API_BASE}/characters/${encodeURIComponent(profileId)}/notes`, {
    method: "PUT", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ content, version }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Não foi possível salvar. Seu rascunho continua aqui.");
  return response.json();
}

export async function applyCharacterStateAction(
  profileId: string,
  action: string,
  payload: Record<string, unknown> = {},
  reason?: string,
): Promise<PlayableCharacter> {
  const response = await fetch(`${API_BASE}/characters/${encodeURIComponent(profileId)}/actions`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ action, payload, reason }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao atualizar ficha");
  return response.json();
}

export async function listCharacterEvents(profileId: string): Promise<CharacterEvent[]> {
  const response = await fetch(`${API_BASE}/characters/${encodeURIComponent(profileId)}/events`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar histórico");
  return response.json();
}

export async function updateCharacterDefinition(
  profileId: string,
  fields: Record<string, unknown>,
  reason?: string,
): Promise<PlayableCharacter> {
  const response = await fetch(`${API_BASE}/gm/characters/${encodeURIComponent(profileId)}/definition`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ fields, reason }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao atualizar definição");
  return response.json();
}

export async function revertCharacterEvent(profileId: string, eventId: number): Promise<PlayableCharacter> {
  const response = await fetch(`${API_BASE}/gm/characters/${encodeURIComponent(profileId)}/events/${eventId}/revert`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao reverter evento");
  return response.json();
}

export async function createFreeRoll(payload: {
  request_id: string; formula: string; label?: string; visibility?: DiceVisibility;
  character_id?: string; target_value?: number; hide_target?: boolean; reason?: string;
}): Promise<DiceRollEvent> {
  const response = await fetch(`${API_BASE}/rolls`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao realizar rolagem");
  return response.json();
}

export async function rollCharacterAction(profileId: string, payload: {
  request_id: string; roll_type: string; source_id?: string; label?: string;
  visibility?: DiceVisibility; target_value?: number; hide_target?: boolean; reason?: string;
}): Promise<DiceRollEvent> {
  const response = await fetch(`${API_BASE}/characters/${encodeURIComponent(profileId)}/rolls`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao realizar rolagem da ficha");
  return response.json();
}

export async function resolveCharacterAttack(profileId: string, payload: {
  request_id: string;
  attack_id: string;
  target_type: "character" | "token";
  target_id: string;
  roll_mode: "digital" | "physical";
  d20?: number;
  attack_count?: number;
  d20s?: number[];
}): Promise<AttackResolution> {
  const response = await fetch(`${API_BASE}/characters/${encodeURIComponent(profileId)}/attacks/resolve`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao resolver o ataque");
  return response.json();
}

export async function confirmCharacterAttack(resolutionId: string): Promise<AttackResolution> {
  const response = await fetch(`${API_BASE}/combat/attacks/${encodeURIComponent(resolutionId)}/confirm`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao confirmar o ataque");
  return response.json();
}

export async function listRollHistory(limit = 30): Promise<DiceRollEvent[]> {
  const response = await fetch(`${API_BASE}/rolls?limit=${Math.max(1, Math.min(limit, 100))}`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar histórico de rolagens");
  return response.json();
}

export async function listPendingRollRequests(): Promise<DiceRollRequest[]> {
  const response = await fetch(`${API_BASE}/roll-requests`, { headers: authHeaders() });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao carregar solicitações de rolagem");
  return response.json();
}

export async function completeRollRequest(rollRequestId: number, requestId: string): Promise<DiceRollEvent> {
  const response = await fetch(`${API_BASE}/roll-requests/${rollRequestId}/complete`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ request_id: requestId }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao concluir solicitação");
  return response.json();
}

export async function createRollRequest(payload: {
  request_id: string; character_id: string; roll_type: string; source_id?: string; formula?: string;
  label?: string; visibility?: DiceVisibility; target_value?: number; hide_target?: boolean; reason?: string;
}): Promise<DiceRollRequest> {
  const response = await fetch(`${API_BASE}/gm/roll-requests`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao solicitar rolagem");
  return response.json();
}

export async function voidDiceRoll(rollId: number, reason: string): Promise<DiceRollEvent> {
  const response = await fetch(`${API_BASE}/gm/rolls/${rollId}/void`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ reason }),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha ao anular rolagem");
  return response.json();
}

async function sceneRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: authHeaders(init?.body ? { "Content-Type": "application/json" } : undefined),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha na operação de cena");
  return response.json();
}

export function newSceneRequestId(prefix = "scene") { return newDiceRequestId(prefix); }
export async function listGameSessions(): Promise<GameSession[]> { return sceneRequest("/gm/sessions"); }
export async function listCampaignSessions(): Promise<CampaignSession[]> { return sceneRequest("/sessions"); }
export async function getCampaignSession(id: number): Promise<CampaignSession> { return sceneRequest(`/sessions/${id}`); }
export async function createGameSession(payload: { request_id: string; title: string; session_number?: number; private_notes?: string }): Promise<GameSession> { return sceneRequest("/gm/sessions", { method: "POST", body: JSON.stringify(payload) }); }
export async function updateGameSessionMetadata(id: number, payload: { played_on?: string | null; image_path?: string | null }): Promise<CampaignSession> { return sceneRequest(`/gm/sessions/${id}`, { method: "PATCH", body: JSON.stringify(payload) }); }
export async function uploadGameSessionImage(id: number, file: File): Promise<CampaignSession> {
  const response = await fetch(`${API_BASE}/gm/sessions/${id}/image`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": file.type || "application/octet-stream" }),
    body: file,
  });
  if (!response.ok) throw new Error(await response.text() || `Falha HTTP ${response.status}`);
  return response.json();
}
export async function updateGameSessionStatus(id: number, status: string): Promise<GameSession> { return sceneRequest(`/gm/sessions/${id}/status`, { method: "POST", body: JSON.stringify({ status }) }); }
export async function listScenes(): Promise<GameScene[]> { return sceneRequest("/scenes"); }
export async function getActiveScene(): Promise<GameScene | null> { return sceneRequest("/scenes/active"); }
export async function getScene(id: number): Promise<GameScene> { return sceneRequest(`/scenes/${id}`); }
export async function createScene(payload: Record<string, unknown>): Promise<GameScene> { return sceneRequest("/gm/scenes", { method: "POST", body: JSON.stringify(payload) }); }
export async function updateScene(id: number, expectedVersion: number, fields: Record<string, unknown>): Promise<GameScene> { return sceneRequest(`/gm/scenes/${id}`, { method: "PATCH", body: JSON.stringify({ expected_version: expectedVersion, fields }) }); }
export async function updateSceneStatus(id: number, status: string, summary?: string): Promise<GameScene> { return sceneRequest(`/gm/scenes/${id}/status`, { method: "POST", body: JSON.stringify({ status, summary }) }); }
export async function addSceneParticipant(sceneId: number, payload: Record<string, unknown>): Promise<GameScene> { return sceneRequest(`/gm/scenes/${sceneId}/participants`, { method: "POST", body: JSON.stringify(payload) }); }
export async function updateSceneParticipant(participantId: number, fields: Record<string, unknown>): Promise<SceneParticipant> { return sceneRequest(`/gm/scene-participants/${participantId}`, { method: "PATCH", body: JSON.stringify({ fields }) }); }
export async function removeSceneParticipant(participantId: number): Promise<SceneParticipant> { return sceneRequest(`/gm/scene-participants/${participantId}`, { method: "DELETE" }); }
export async function createSceneElement(sceneId: number, payload: Record<string, unknown>): Promise<GameScene> { return sceneRequest(`/gm/scenes/${sceneId}/elements`, { method: "POST", body: JSON.stringify(payload) }); }
export async function updateSceneElement(elementId: number, fields: Record<string, unknown>): Promise<SceneElement> { return sceneRequest(`/gm/scene-elements/${elementId}`, { method: "PATCH", body: JSON.stringify({ fields }) }); }
export async function revealSceneElement(elementId: number): Promise<SceneElement> { return sceneRequest(`/gm/scene-elements/${elementId}/reveal`, { method: "POST" }); }
export async function declareSceneAction(sceneId: number, payload: { request_id: string; character_id?: string; action_type: string; description: string; target_label?: string; visibility?: DiceVisibility }): Promise<SceneAction> { return sceneRequest(`/scenes/${sceneId}/actions`, { method: "POST", body: JSON.stringify(payload) }); }
export async function cancelSceneAction(actionId: number): Promise<SceneAction> { return sceneRequest(`/scenes/actions/${actionId}/cancel`, { method: "POST" }); }
export async function resolveSceneAction(actionId: number, resolution?: string): Promise<SceneAction> { return sceneRequest(`/gm/scenes/actions/${actionId}/resolve`, { method: "POST", body: JSON.stringify({ resolution }) }); }
export async function rejectSceneAction(actionId: number, resolution: string): Promise<SceneAction> { return sceneRequest(`/gm/scenes/actions/${actionId}/reject`, { method: "POST", body: JSON.stringify({ resolution }) }); }
export async function requestSceneActionRoll(actionId: number, payload: Record<string, unknown>): Promise<DiceRollRequest> { return sceneRequest(`/gm/scenes/actions/${actionId}/request-roll`, { method: "POST", body: JSON.stringify(payload) }); }
export async function applySceneConsequence(sceneId: number, payload: Record<string, unknown>): Promise<{ character_event: Record<string, unknown>; scene_event: SceneEvent; scene: GameScene }> { return sceneRequest(`/gm/scenes/${sceneId}/consequences`, { method: "POST", body: JSON.stringify(payload) }); }
export async function createSceneEvent(sceneId: number, payload: Record<string, unknown>): Promise<SceneEvent> { return sceneRequest(`/gm/scenes/${sceneId}/events`, { method: "POST", body: JSON.stringify(payload) }); }
export async function publishScene(sceneId: number, payload: { request_id: string; publication_type: string; title: string; public_text?: string; private_text?: string }): Promise<{ event: SceneEvent; created: boolean }> { return sceneRequest(`/gm/scenes/${sceneId}/publish`, { method: "POST", body: JSON.stringify(payload) }); }
export async function openSceneOnTable(sceneId: number, requestId: string): Promise<{ scene: GameScene; map?: { id: string; title: string; image_path: string } | null; event: SceneEvent; created: boolean }> { return sceneRequest(`/gm/scenes/${sceneId}/open-on-table`, { method: "POST", body: JSON.stringify({ request_id: requestId }) }); }
export async function voidSceneEvent(eventId: number, reason: string): Promise<SceneEvent> { return sceneRequest(`/gm/scene-events/${eventId}/void`, { method: "POST", body: JSON.stringify({ reason }) }); }

async function contractRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: authHeaders(init?.body ? { "Content-Type": "application/json" } : undefined),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha na operaÃ§Ã£o de contrato");
  return response.json();
}

export function newContractRequestId(prefix = "contract") { return newDiceRequestId(prefix); }
export async function listContracts(): Promise<ContractRecord[]> { return contractRequest("/contracts"); }
export async function getContract(id: number): Promise<ContractRecord> { return contractRequest(`/contracts/${id}`); }
export async function acceptContract(id: number, payload: { request_id: string; character_id?: string; public_role?: string }): Promise<ContractRecord> { return contractRequest(`/contracts/${id}/accept`, { method: "POST", body: JSON.stringify(payload) }); }
export async function createContract(payload: Record<string, unknown>): Promise<ContractRecord> { return contractRequest("/gm/contracts", { method: "POST", body: JSON.stringify(payload) }); }
export async function updateContract(id: number, expectedVersion: number, fields: Record<string, unknown>): Promise<ContractRecord> { return contractRequest(`/gm/contracts/${id}`, { method: "PATCH", body: JSON.stringify({ expected_version: expectedVersion, fields }) }); }
export async function transitionContract(id: number, action: "publish" | "accept" | "start" | "complete" | "fail" | "abandon" | "cancel", requestId: string, reason?: string): Promise<ContractRecord> { return contractRequest(`/gm/contracts/${id}/${action}`, { method: "POST", body: JSON.stringify({ request_id: requestId, reason }) }); }
export async function createContractObjective(contractId: number, payload: Record<string, unknown>): Promise<ContractObjective> { return contractRequest(`/gm/contracts/${contractId}/objectives`, { method: "POST", body: JSON.stringify(payload) }); }
export async function updateContractObjective(id: number, expectedVersion: number, fields: Record<string, unknown>): Promise<ContractObjective> { return contractRequest(`/gm/contract-objectives/${id}`, { method: "PATCH", body: JSON.stringify({ expected_version: expectedVersion, fields }) }); }
export async function setContractObjectiveStatus(id: number, status: ContractObjectiveStatus, requestId: string): Promise<ContractObjective> { return contractRequest(`/gm/contract-objectives/${id}/status`, { method: "POST", body: JSON.stringify({ request_id: requestId, status }) }); }
export async function reorderContractObjectives(contractId: number, order: number[]): Promise<ContractObjective[]> { return contractRequest(`/gm/contracts/${contractId}/objectives/order`, { method: "POST", body: JSON.stringify({ order }) }); }
export async function addContractAssignment(contractId: number, payload: { request_id: string; character_id: string; public_role?: string }): Promise<ContractAssignment> { return contractRequest(`/gm/contracts/${contractId}/assignments`, { method: "POST", body: JSON.stringify(payload) }); }
export async function removeContractAssignment(id: number, requestId: string, reason?: string): Promise<ContractAssignment> { return contractRequest(`/gm/contract-assignments/${id}`, { method: "DELETE", body: JSON.stringify({ request_id: requestId, reason }) }); }
export async function linkContractScene(contractId: number, payload: { request_id: string; scene_id: number; objective_id?: number; link_type?: string }): Promise<ContractSceneLink> { return contractRequest(`/gm/contracts/${contractId}/scene-links`, { method: "POST", body: JSON.stringify(payload) }); }
export async function unlinkContractScene(id: number): Promise<ContractSceneLink> { return contractRequest(`/gm/contract-scene-links/${id}`, { method: "DELETE" }); }
export async function createContractScene(contractId: number, payload: Record<string, unknown>): Promise<GameScene> { return contractRequest(`/gm/contracts/${contractId}/scenes`, { method: "POST", body: JSON.stringify(payload) }); }
export async function createContractReward(contractId: number, payload: Record<string, unknown>): Promise<ContractReward> { return contractRequest(`/gm/contracts/${contractId}/rewards`, { method: "POST", body: JSON.stringify(payload) }); }
export async function updateContractReward(id: number, expectedVersion: number, fields: Record<string, unknown>): Promise<ContractReward> { return contractRequest(`/gm/contract-rewards/${id}`, { method: "PATCH", body: JSON.stringify({ expected_version: expectedVersion, fields }) }); }
export async function approveContractReward(id: number, requestId: string): Promise<ContractReward> { return contractRequest(`/gm/contract-rewards/${id}/approve`, { method: "POST", body: JSON.stringify({ request_id: requestId }) }); }
export async function deliverContractReward(id: number, payload: { request_id: string; character_ids: string[] }): Promise<Record<string, unknown>> { return contractRequest(`/gm/contract-rewards/${id}/deliver`, { method: "POST", body: JSON.stringify(payload) }); }
export async function listReputation(params: { character_id?: string; party_id?: string } = {}): Promise<ReputationLedger[]> {
  const query = new URLSearchParams();
  if (params.character_id) query.set("character_id", params.character_id);
  if (params.party_id) query.set("party_id", params.party_id);
  return contractRequest(`/reputation${query.toString() ? `?${query.toString()}` : ""}`);
}
export async function applyReputation(payload: Record<string, unknown>): Promise<ReputationLedger> { return contractRequest("/gm/reputation", { method: "POST", body: JSON.stringify(payload) }); }
export async function revertReputation(id: number): Promise<ReputationLedger> { return contractRequest(`/gm/reputation/${id}/revert`, { method: "POST" }); }
export async function voidContractEvent(id: number, reason: string): Promise<ContractEvent> { return contractRequest(`/gm/contract-events/${id}/void`, { method: "POST", body: JSON.stringify({ reason }) }); }

async function npcRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: authHeaders(init?.body ? { "Content-Type": "application/json" } : undefined),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha na memória de NPCs");
  return response.json();
}

export function newNpcRequestId(prefix = "npc") { return newDiceRequestId(prefix); }
export async function listNpcs(filters: Record<string, string> = {}): Promise<NpcRecord[]> {
  const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => Boolean(value)));
  return npcRequest(`/npcs${query.size ? `?${query}` : ""}`);
}
export async function getNpc(id: number): Promise<NpcRecord> { return npcRequest(`/npcs/${id}`); }
export async function getNpcSummary(id: number): Promise<Record<string, unknown>> { return npcRequest(`/npcs/${id}/summary`); }
export async function createNpc(payload: Record<string, unknown>): Promise<NpcRecord> { return npcRequest("/gm/npcs", { method: "POST", body: JSON.stringify(payload) }); }
export async function importNpc(payload: { request_id: string; source_path: string; visible_to_players?: boolean }): Promise<NpcRecord> { return npcRequest("/gm/npcs/import", { method: "POST", body: JSON.stringify(payload) }); }
export async function updateNpc(id: number, expectedVersion: number, fields: Record<string, unknown>, reason = "Atualização administrativa"): Promise<NpcRecord> { return npcRequest(`/gm/npcs/${id}`, { method: "PATCH", body: JSON.stringify({ expected_version: expectedVersion, fields, reason }) }); }
export async function updateNpcState(id: number, expectedVersion: number, fields: Record<string, unknown>, reason = "Atualização de estado"): Promise<NpcRecord> { return npcRequest(`/gm/npcs/${id}/state`, { method: "PATCH", body: JSON.stringify({ expected_version: expectedVersion, fields, reason }) }); }
export async function createNpcRelationship(id: number, payload: Record<string, unknown>): Promise<NpcRelationship> { return npcRequest(`/gm/npcs/${id}/relationships`, { method: "POST", body: JSON.stringify(payload) }); }
export async function updateNpcRelationship(id: number, expectedVersion: number, fields: Record<string, unknown>, reason: string): Promise<NpcRelationship> { return npcRequest(`/gm/npc-relationships/${id}`, { method: "PATCH", body: JSON.stringify({ expected_version: expectedVersion, fields, reason }) }); }
export async function createNpcMemory(id: number, payload: Record<string, unknown>): Promise<NpcMemory> { return npcRequest(`/gm/npcs/${id}/memories`, { method: "POST", body: JSON.stringify(payload) }); }
export async function updateNpcMemory(id: number, expectedVersion: number, fields: Record<string, unknown>, reason: string): Promise<NpcMemory> { return npcRequest(`/gm/npc-memories/${id}`, { method: "PATCH", body: JSON.stringify({ expected_version: expectedVersion, fields, reason }) }); }
export async function contradictNpcMemory(id: number, payload: Record<string, unknown>): Promise<NpcMemory> { return npcRequest(`/gm/npc-memories/${id}/contradict`, { method: "POST", body: JSON.stringify(payload) }); }
export async function recordNpcEncounter(id: number, payload: Record<string, unknown>): Promise<NpcEncounter> { return npcRequest(`/gm/npcs/${id}/encounters`, { method: "POST", body: JSON.stringify(payload) }); }
export async function unlinkNpcEncounter(id: number, reason: string): Promise<NpcEncounter> { return npcRequest(`/gm/npc-encounters/${id}`, { method: "DELETE", body: JSON.stringify({ reason }) }); }
export async function linkNpcContract(id: number, payload: Record<string, unknown>): Promise<NpcContractLink> { return npcRequest(`/gm/npcs/${id}/contracts`, { method: "POST", body: JSON.stringify(payload) }); }
export async function listContractNpcs(id: number): Promise<NpcContractLink[]> { return npcRequest(`/contracts/${id}/npcs`); }
export async function voidNpcEvent(id: number, reason: string): Promise<NpcEvent> { return npcRequest(`/gm/npc-events/${id}/void`, { method: "POST", body: JSON.stringify({ reason }) }); }

async function worldRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: authHeaders(init?.body ? { "Content-Type": "application/json" } : undefined),
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || "Falha no mapa ou na viagem");
  return response.json();
}

export function newWorldRequestId(prefix = "world") { return newDiceRequestId(prefix); }
export async function listWorldMaps(): Promise<WorldMapRecord[]> { return worldRequest("/world/maps"); }
export async function getWorldMap(id: number): Promise<WorldMapRecord> { return worldRequest(`/world/maps/${id}`); }
export async function createWorldMap(payload: Record<string, unknown>): Promise<WorldMapRecord> { return worldRequest("/gm/world/maps", { method: "POST", body: JSON.stringify(payload) }); }
export async function previewWorldMapImport(payload: Record<string, unknown>): Promise<Record<string, unknown>> { return worldRequest("/gm/world/maps/import-preview", { method: "POST", body: JSON.stringify(payload) }); }
export async function importWorldMap(payload: Record<string, unknown>): Promise<WorldMapRecord> { return worldRequest("/gm/world/maps/import", { method: "POST", body: JSON.stringify(payload) }); }
export async function listWorldLocations(mapId?: number): Promise<WorldLocationRecord[]> { return worldRequest(`/world/locations${mapId ? `?map_id=${mapId}` : ""}`); }
export async function getWorldLocation(id: number): Promise<WorldLocationRecord> { return worldRequest(`/world/locations/${id}`); }
export async function createWorldLocation(payload: Record<string, unknown>): Promise<WorldLocationRecord> { return worldRequest("/gm/world/locations", { method: "POST", body: JSON.stringify(payload) }); }
export async function importWorldLocation(payload: Record<string, unknown>, mapId?: number): Promise<WorldLocationRecord> { return worldRequest(`/gm/world/locations/import${mapId ? `?map_id=${mapId}` : ""}`, { method: "POST", body: JSON.stringify(payload) }); }
export async function updateWorldLocation(id: number, expectedVersion: number, fields: Record<string, unknown>): Promise<WorldLocationRecord> { return worldRequest(`/gm/world/locations/${id}`, { method: "PATCH", body: JSON.stringify({ expected_version: expectedVersion, fields }) }); }
export async function updateWorldLocationState(id: number, expectedVersion: number, fields: Record<string, unknown>): Promise<WorldLocationRecord> { return worldRequest(`/gm/world/locations/${id}/state`, { method: "PATCH", body: JSON.stringify({ expected_version: expectedVersion, fields }) }); }
export async function discoverWorldLocation(id: number, payload: Record<string, unknown>): Promise<Record<string, unknown>> { return worldRequest(`/gm/world/locations/${id}/discoveries`, { method: "POST", body: JSON.stringify(payload) }); }
export async function listTravelRoutes(): Promise<TravelRouteRecord[]> { return worldRequest("/world/routes"); }
export async function createTravelRoute(payload: Record<string, unknown>): Promise<TravelRouteRecord> { return worldRequest("/gm/world/routes", { method: "POST", body: JSON.stringify(payload) }); }
export async function updateTravelRoute(id: number, expectedVersion: number, fields: Record<string, unknown>): Promise<TravelRouteRecord> { return worldRequest(`/gm/world/routes/${id}`, { method: "PATCH", body: JSON.stringify({ expected_version: expectedVersion, fields }) }); }
export async function discoverTravelRoute(id: number, payload: Record<string, unknown>): Promise<Record<string, unknown>> { return worldRequest(`/gm/world/routes/${id}/discoveries`, { method: "POST", body: JSON.stringify(payload) }); }
export async function listJourneys(): Promise<JourneyRecord[]> { return worldRequest("/world/journeys"); }
export async function getJourney(id: number): Promise<JourneyRecord> { return worldRequest(`/world/journeys/${id}`); }
export async function createJourney(payload: Record<string, unknown>): Promise<JourneyRecord> { return worldRequest("/gm/world/journeys", { method: "POST", body: JSON.stringify(payload) }); }
export async function updatePlannedJourney(id: number, expectedVersion: number, fields: Record<string, unknown>): Promise<JourneyRecord> { return worldRequest(`/gm/world/journeys/${id}`, { method: "PATCH", body: JSON.stringify({ expected_version: expectedVersion, fields }) }); }
export async function addJourneyParticipant(id: number, payload: Record<string, unknown>): Promise<JourneyParticipantRecord> { return worldRequest(`/gm/world/journeys/${id}/participants`, { method: "POST", body: JSON.stringify(payload) }); }
export async function removeJourneyParticipant(id: number, payload: { request_id: string; reason: string }): Promise<JourneyParticipantRecord> { return worldRequest(`/gm/world/journey-participants/${id}`, { method: "DELETE", body: JSON.stringify(payload) }); }
export async function transitionJourney(id: number, action: "start" | "pause" | "resume" | "complete" | "cancel" | "fail", payload: Record<string, unknown>): Promise<JourneyRecord> { return worldRequest(`/gm/world/journeys/${id}/transition/${action}`, { method: "POST", body: JSON.stringify(payload) }); }
export async function advanceJourney(id: number, payload: Record<string, unknown>): Promise<JourneyRecord> { return worldRequest(`/gm/world/journeys/${id}/advance`, { method: "POST", body: JSON.stringify(payload) }); }
export async function linkJourneyScene(id: number, payload: Record<string, unknown>): Promise<Record<string, unknown>> { return worldRequest(`/gm/world/journeys/${id}/scenes`, { method: "POST", body: JSON.stringify(payload) }); }
export async function linkSceneLocation(sceneId: number, payload: Record<string, unknown>): Promise<Record<string, unknown>> { return worldRequest(`/gm/world/scenes/${sceneId}/location`, { method: "POST", body: JSON.stringify(payload) }); }
export async function listSceneLocations(sceneId: number): Promise<Array<{ link: Record<string, unknown>; location: WorldLocationRecord }>> { return worldRequest(`/scenes/${sceneId}/locations`); }
export async function linkContractLocation(contractId: number, payload: Record<string, unknown>): Promise<Record<string, unknown>> { return worldRequest(`/gm/world/contracts/${contractId}/locations`, { method: "POST", body: JSON.stringify(payload) }); }
export async function listContractLocations(contractId: number): Promise<Array<{ link: Record<string, unknown>; location: WorldLocationRecord }>> { return worldRequest(`/contracts/${contractId}/locations`); }

export async function health() {
  const response = await fetch(`${API_BASE}/health`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao consultar /health");
  return response.json();
}

export async function rebuildIndex() {
  const response = await fetch(`${API_BASE}/index/rebuild`, { method: "POST", headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao reconstruir índice");
  return response.json();
}

export async function listNotes(): Promise<NoteSummary[]> {
  const response = await fetch(scoped("/notes"), { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao listar notas");
  return response.json();
}

export async function getNote(id: number): Promise<NoteDetail> {
  const response = await fetch(scoped(`/notes/${id}`), { headers: authHeaders() });
  if (!response.ok) throw new Error("Nota não encontrada");
  return response.json();
}

export async function resolveNote(target: string): Promise<NoteSummary | null> {
  const response = await fetch(`${scoped("/resolve")}?target=${encodeURIComponent(target)}`, { headers: authHeaders() });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Falha ao resolver wikilink");
  return response.json();
}

export async function searchNotes(query: string, limit = 10): Promise<SearchResult[]> {
  const response = await fetch(scoped("/search"), {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ query, limit }),
  });
  if (!response.ok) throw new Error("Falha na busca");
  return response.json();
}

export async function chatVault(question: string, limit = 6, contextNoteIds: number[] = [], sessionId?: string): Promise<ChatResult> {
  const response = await fetch(scoped("/chat"), {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ question, limit, context_note_ids: contextNoteIds.slice(-4), session_id: sessionId || null }),
  });
  if (!response.ok) throw new Error("Falha no chat");
  return response.json();
}

async function trainingRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}/gm/training${path}`, {
    ...options,
    headers: authHeaders({ "Content-Type": "application/json", ...((options.headers as Record<string, string>) || {}) }),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail || "Falha na curadoria da IA");
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export async function captureTrainingInteraction(payload: {
  interaction_id?: string | null;
  created_at?: string | null;
  session_id?: string | null;
  user_profile: "player" | "gm";
  question: string;
  raw_model_response?: string | null;
  final_response: string;
  verified_facts?: Array<Record<string, unknown>>;
  theories?: Array<Record<string, unknown>>;
  insufficient_information?: string[];
  retrieved_sources?: NoteSummary[];
  retrieval_mode?: string | null;
  model?: string | null;
  ollama_used?: boolean;
  response_time_ms?: number;
  validator_rejections?: Array<Record<string, unknown>>;
  warning?: string | null;
  behavior_memory_used?: boolean;
  behavioral_trace?: Record<string, unknown> | null;
  feedback_action: TrainingFeedbackAction;
  reason?: string;
  category?: string;
  persona_id_override?: string | null;
}): Promise<{ interaction: TrainingInteraction; example: TrainingExample; validation_errors: string[] }> {
  return trainingRequest("/interactions/capture", { method: "POST", body: JSON.stringify(payload) });
}

export async function listTrainingExamples(filters: Record<string, string> = {}): Promise<TrainingExample[]> {
  const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => Boolean(value)));
  return trainingRequest(`/examples${query.size ? `?${query}` : ""}`);
}

export async function getTrainingExample(id: string): Promise<TrainingExample> {
  return trainingRequest(`/examples/${encodeURIComponent(id)}`);
}

export async function updateTrainingExample(id: string, payload: Record<string, unknown>): Promise<{ example: TrainingExample; validation_errors: string[] }> {
  return trainingRequest(`/examples/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export async function approveTrainingExample(id: string, payload: { reviewer?: string; reason?: string; ideal_response?: string; quality?: number }): Promise<{ example: TrainingExample; validation_errors: string[] }> {
  return trainingRequest(`/examples/${encodeURIComponent(id)}/approve`, { method: "POST", body: JSON.stringify({ reviewer: "Sage", ...payload }) });
}

export async function rejectTrainingExample(id: string, reason?: string): Promise<TrainingExample> {
  return trainingRequest(`/examples/${encodeURIComponent(id)}/reject`, { method: "POST", body: JSON.stringify({ reviewer: "Sage", reason }) });
}

export async function markTrainingExample(id: string, flag: "hallucination" | "leak" | "incomplete" | "artificial" | "incorrect-source", detail?: string) {
  return trainingRequest(`/examples/${encodeURIComponent(id)}/mark-${flag}`, { method: "POST", body: JSON.stringify({ reviewer: "Sage", detail }) });
}

export async function deleteTrainingExample(id: string): Promise<void> {
  return trainingRequest(`/examples/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export async function duplicateTrainingExample(id: string): Promise<TrainingExample> {
  return trainingRequest(`/examples/${encodeURIComponent(id)}/duplicate`, { method: "POST", body: "{}" });
}

export async function exportTrainingReport(): Promise<Record<string, unknown>> {
  return trainingRequest("/export-sanitized");
}

export async function getTrainingStats(): Promise<TrainingStats> {
  return trainingRequest("/stats");
}

export async function validateTrainingBatch(exampleIds: string[], minimumQuality = 4): Promise<TrainingBatchValidation> {
  return trainingRequest("/examples/batch/validate", {
    method: "POST",
    body: JSON.stringify({ example_ids: exampleIds, reviewer: "Sage", minimum_quality: minimumQuality }),
  });
}

export async function approveTrainingBatch(payload: {
  example_ids: string[];
  reviewed: boolean;
  confirmation: string;
  reason?: string;
  minimum_quality?: number;
}): Promise<TrainingBatchValidation> {
  return trainingRequest("/examples/batch/approve", {
    method: "POST",
    body: JSON.stringify({ reviewer: "Sage", minimum_quality: 4, ...payload }),
  });
}

export async function playerDashboard(): Promise<PlayerDashboard> {
  const response = await fetch(`${API_BASE}/player/dashboard`, { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao carregar painel dos jogadores");
  return response.json();
}

export async function listPlayerActions(): Promise<PlayerAction[]> {
  const response = await fetch(scoped("/actions"), { headers: authHeaders() });
  if (!response.ok) throw new Error("Falha ao carregar ações");
  return response.json();
}

export async function submitPlayerAction(payload: {
  character_note_id: number;
  action_type: PlayerActionType;
  target_note_id: number;
  intent: string;
}): Promise<PlayerAction> {
  const response = await fetch(`${API_BASE}/player/actions`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail || "Falha ao enviar ação");
  }
  return response.json();
}

export async function updatePlayerAction(
  actionId: number,
  payload: { status: PlayerActionStatus; gm_response?: string | null },
): Promise<PlayerAction> {
  const response = await fetch(`${API_BASE}/gm/actions/${actionId}`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail || "Falha ao atualizar ação");
  }
  return response.json();
}
