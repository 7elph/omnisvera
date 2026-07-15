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
export type InventoryItem = {
  id: number; profile_id: string; item_path: string; item_title: string;
  note_id?: number | null; thumbnail?: string | null; cover?: string | null;
  quantity: number; equipped: boolean; notes?: string | null; updated_at: string;
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
