from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    backend: str
    vault_path: str
    database_path: str
    ollama_base_url: str
    ollama_model: str
    fast_model: str | None = None
    quality_model: str | None = None
    candidate_model: str | None = None
    production_model: str | None = None
    model_mode: str | None = None
    production_approved: bool = False
    embedding_model: str | None = None
    response_mode: str | None = None
    rag_mode: str | None = None
    semantic_index_path: str | None = None
    auto_refresh_index: bool = False
    auto_refresh_interval_seconds: int | None = None
    ollama_accessible: bool
    access_mode: str | None = None
    player_mode_available: bool = False
    player_profile_id: str | None = None
    player_character_path: str | None = None
    player_character_title: str | None = None
    training_capture_mode: str | None = None
    behavior_memory_enabled: bool = False
    behavior_memory_mode: str | None = None
    behavior_memory_ab_mode: str | None = None


class RebuildResponse(BaseModel):
    indexed_notes: int
    skipped_files: int
    vault_path: str


class NoteSummary(BaseModel):
    id: int
    path: str
    title: str
    aliases: list[str] = Field(default_factory=list)
    type: str | None = None
    visibility: str | None = None
    tags: list[str] = Field(default_factory=list)
    cover: str | None = None
    thumbnail: str | None = None
    status: str | None = None
    description: str | None = None
    updated_at: str


class NoteDetail(NoteSummary):
    content: str
    frontmatter: dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


class SearchResult(NoteSummary):
    score: int
    excerpt: str


class ChatRequest(BaseModel):
    question: str
    limit: int = 4
    context_paths: list[str] = Field(default_factory=list)
    context_note_ids: list[int] = Field(default_factory=list)
    session_id: str | None = Field(default=None, max_length=160)
    capture_for_training: bool = True


class ChatResponse(BaseModel):
    answer: str
    notes_used: list[NoteSummary]
    note_paths: list[str]
    insufficient_context: bool
    warning: str | None = None
    suggested_questions: list[str] = Field(default_factory=list)
    fatos_confirmados: list[dict[str, Any]] = Field(default_factory=list)
    teorias: list[dict[str, Any]] = Field(default_factory=list)
    informacoes_insuficientes: list[str] = Field(default_factory=list)
    fontes_usadas: list[str] = Field(default_factory=list)
    ollama_used: bool = False
    ollama_attempted: bool = False
    model: str | None = None
    retrieval_mode: str | None = None
    interaction_id: str | None = None
    created_at: str | None = None
    response_time_ms: int | None = None
    raw_model_response: str | None = None
    validator_rejections: list[dict[str, Any]] = Field(default_factory=list)
    behavior_memory_used: bool = False
    behavioral_trace: dict[str, Any] | None = None


class TrainingInteractionCapture(BaseModel):
    interaction_id: str | None = None
    session_id: str | None = None
    user_profile: str = "gm"
    player_id: str | None = None
    character_id: str | None = None
    persona_id: str | None = None
    question: str = Field(min_length=2, max_length=5000)
    raw_model_response: str | None = Field(default=None, max_length=20_000)
    final_response: str = Field(max_length=20_000)
    verified_facts: list[dict[str, Any]] = Field(default_factory=list)
    theories: list[dict[str, Any]] = Field(default_factory=list)
    insufficient_information: list[str] = Field(default_factory=list)
    retrieved_sources: list[dict[str, Any]] = Field(default_factory=list)
    retrieval_mode: str | None = None
    model: str | None = None
    ollama_used: bool = False
    response_time_ms: int = Field(default=0, ge=0)
    validator_rejections: list[dict[str, Any]] = Field(default_factory=list)
    warning: str | None = Field(default=None, max_length=2000)
    behavior_memory_used: bool = False
    behavioral_trace: dict[str, Any] | None = None
    feedback_action: str
    reason: str | None = Field(default=None, max_length=3000)
    category: str | None = None
    persona_id_override: str | None = None


class TrainingExamplePatch(BaseModel):
    category: str | None = None
    source_type: str | None = None
    persona_id: str | None = None
    ideal_response: str | None = Field(default=None, max_length=20_000)
    facts_expected: list[str] | None = None
    theories_allowed: list[str] | None = None
    insufficient_information_expected: bool | None = None
    requires_rag: bool | None = None
    contains_canon: bool | None = None
    contains_secret: bool | None = None
    notes: str | None = Field(default=None, max_length=5000)
    quality: int | None = Field(default=None, ge=1, le=5)
    hallucination_detected: bool | None = None
    leak_detected: bool | None = None
    incomplete_detected: bool | None = None
    artificial_detected: bool | None = None
    incorrect_source_detected: bool | None = None
    reason: str | None = Field(default=None, max_length=3000)


class TrainingDecisionRequest(BaseModel):
    reviewer: str = Field(default="Sage", min_length=2, max_length=120)
    reason: str | None = Field(default=None, max_length=3000)
    ideal_response: str | None = Field(default=None, max_length=20_000)
    quality: int | None = Field(default=None, ge=1, le=5)


class TrainingFlagRequest(BaseModel):
    reviewer: str = Field(default="Sage", min_length=2, max_length=120)
    detail: str | None = Field(default=None, max_length=3000)


class TrainingBatchRequest(BaseModel):
    example_ids: list[str] = Field(min_length=1, max_length=100)
    reviewer: str = Field(default="Sage", min_length=2, max_length=120)
    reviewed: bool = False
    confirmation: str = Field(default="", max_length=80)
    reason: str | None = Field(default=None, max_length=3000)
    minimum_quality: int = Field(default=4, ge=1, le=5)


class DashboardSection(BaseModel):
    kind: str | None = None
    title: str
    description: str | None = None
    cover: str | None = None
    prompt: str | None = None
    items: list[NoteSummary] = Field(default_factory=list)


class PlayerDashboardResponse(BaseModel):
    mode: str = "player"
    sections: list[DashboardSection] = Field(default_factory=list)


class PlayerActionCreate(BaseModel):
    character_note_id: int
    action_type: str
    target_note_id: int
    intent: str = Field(min_length=3, max_length=1200)


class PlayerActionUpdate(BaseModel):
    status: str
    gm_response: str | None = Field(default=None, max_length=2400)


class PlayerActionRecord(BaseModel):
    id: int
    character_path: str
    character_title: str
    action_type: str
    target_path: str
    target_title: str
    intent: str
    status: str
    gm_response: str | None = None
    created_at: str
    updated_at: str


class PlayerProfileResponse(BaseModel):
    profile_id: str | None = None
    character_path: str | None = None
    character_title: str | None = None
    character_note_id: int | None = None
    thumbnail: str | None = None
    cover: str | None = None
    character_class: str | None = None
    race: str | None = None
    level: str | int | None = None
    status: str | None = None
    location: str | None = None
    faction: str | None = None
    shared_access: bool = False


class PlayerDiscoveryCreate(BaseModel):
    profile_id: str
    note_id: int


class PlayerDiscoveryRecord(BaseModel):
    id: int
    profile_id: str
    note_path: str
    note_title: str
    created_at: str


class PlayerEventRecord(BaseModel):
    id: int
    profile_id: str
    kind: str
    title: str
    message: str
    note_path: str | None = None
    created_at: str
    read_at: str | None = None


class PlayerEventReadRequest(BaseModel):
    event_ids: list[int] = Field(default_factory=list)


class PlayerQuestUpdate(BaseModel):
    profile_id: str = "group"
    note_id: int
    status: str
    progress: str | None = Field(default=None, max_length=1200)


class PlayerQuestRecord(BaseModel):
    id: int
    profile_id: str
    note_path: str
    note_title: str
    status: str
    progress: str | None = None
    updated_at: str


class EditableNoteResponse(BaseModel):
    path: str
    content: str
    content_hash: str
    updated_at: str


class EditableNoteUpdate(BaseModel):
    path: str
    content: str = Field(max_length=500_000)
    expected_hash: str


class InventoryUpdate(BaseModel):
    profile_id: str
    note_id: int
    quantity: int = Field(default=1, ge=0, le=999)
    equipped: bool = False
    notes: str | None = Field(default=None, max_length=500)


class InventoryRecord(BaseModel):
    id: int
    profile_id: str
    item_path: str
    item_title: str
    note_id: int | None = None
    thumbnail: str | None = None
    cover: str | None = None
    damage_formula: str | None = None
    quantity: int
    equipped: bool
    notes: str | None = None
    updated_at: str


class PlayerIdeaCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    concept: str = Field(min_length=10, max_length=1800)
    appearance: str | None = Field(default=None, max_length=1000)
    motivation: str | None = Field(default=None, max_length=1000)
    world_connection: str | None = Field(default=None, max_length=1000)


class PlayerIdeaReview(BaseModel):
    status: str
    feedback: str | None = Field(default=None, max_length=1800)


class PlayerIdeaRecord(PlayerIdeaCreate):
    id: int
    author: str
    status: str
    gm_feedback: str | None = None
    created_at: str
    updated_at: str


class CharacterSheetStep(BaseModel):
    key: str
    title: str
    summary: str
    status: str
    fields: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    guide: dict[str, Any] = Field(default_factory=dict)


class CharacterSheetResponse(BaseModel):
    profile_id: str
    character_path: str
    character_title: str
    status: str
    completion_count: int
    total_steps: int
    steps: list[CharacterSheetStep] = Field(default_factory=list)
    submitted_at: str | None = None
    reviewed_at: str | None = None
    gm_feedback: str | None = None
    updated_at: str


class CharacterSheetStepUpdate(BaseModel):
    step_key: str
    fields: dict[str, Any] = Field(default_factory=dict)


class CharacterSheetReview(BaseModel):
    status: str
    feedback: str | None = Field(default=None, max_length=2400)


class CharacterResource(BaseModel):
    key: str
    label: str
    current: int = Field(ge=0)
    maximum: int = Field(ge=0)


class CharacterStateResponse(BaseModel):
    current_hp: int | None = None
    maximum_hp: int | None = None
    temporary_hp: int = 0
    conditions: list[str] = Field(default_factory=list)
    resources: list[CharacterResource] = Field(default_factory=list)
    coins: int | float | None = None
    location: str | None = None
    current_location_id: int | None = None
    active_journey_id: int | None = None
    session_notes: str = ""
    updated_at: str
    version: int


class CharacterDefinitionResponse(BaseModel):
    id: str
    slug: str
    name: str
    portrait: str | None = None
    cover: str | None = None
    epithet: str | None = None
    race: str | None = None
    class_name: str | None = None
    level: int | None = None
    player_name: str | None = None
    campaign: str | None = None
    attributes: dict[str, int | float | None] | None = None
    attribute_modifiers: dict[str, int | None] | None = None
    abilities: dict[str, str] | None = None
    attacks: list[dict[str, Any]] | None = None
    attack_notes: str | None = None
    defenses: dict[str, Any] | None = None
    progression: dict[str, Any] | None = None
    movement: str | None = None
    base_equipment: list[str] | None = None
    public_description: str | None = None
    history: str | None = None
    relationships: str | None = None
    physical_description: str | None = None
    personality: str | None = None
    goals: str | None = None
    location: str | None = None
    current_status: str | None = None
    canonical_state: str | None = None
    source_vault: str | None = None
    definition_updated_at: str | None = None
    gm_fields: dict[str, str] | None = None


class CharacterPermissions(BaseModel):
    view_private_mechanics: bool
    edit_state: bool
    edit_definition: bool
    view_gm_fields: bool
    revert_events: bool


class PlayableCharacterResponse(BaseModel):
    access_level: str
    definition: CharacterDefinitionResponse
    state: CharacterStateResponse | None = None
    inventory: list[InventoryRecord] = Field(default_factory=list)
    permissions: CharacterPermissions


class PlayableCharacterSummary(BaseModel):
    id: str
    name: str
    portrait: str | None = None
    epithet: str | None = None
    race: str | None = None
    class_name: str | None = None
    level: int | None = None
    current_hp: int | None = None
    maximum_hp: int | None = None
    armor_class: int | None = None
    initiative: int | None = None
    movement: str | None = None
    conditions: list[str] = Field(default_factory=list)
    resources: list[CharacterResource] = Field(default_factory=list)
    access_level: str


class CharacterStateAction(BaseModel):
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = Field(default=None, max_length=500)
    session_id: str | None = Field(default=None, max_length=120)


class CharacterDefinitionUpdate(BaseModel):
    fields: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = Field(default=None, max_length=500)


class CharacterEventResponse(BaseModel):
    id: int
    character_id: str
    session_id: str | None = None
    actor_id: str
    actor_role: str
    event_type: str
    field: str
    before: Any = None
    after: Any = None
    reason: str | None = None
    created_at: str
    reverted_at: str | None = None
    reverted_by: str | None = None


class DiceRollCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=120)
    formula: str = Field(min_length=3, max_length=32)
    label: str | None = Field(default=None, max_length=160)
    visibility: str = "table"
    character_id: str | None = Field(default=None, max_length=120)
    target_value: int | None = Field(default=None, ge=1, le=100_000)
    hide_target: bool = False
    reason: str | None = Field(default=None, max_length=500)
    session_id: str | None = Field(default=None, max_length=120)
    scene_id: int | None = Field(default=None, ge=1)
    action_id: int | None = Field(default=None, ge=1)


class CharacterRollCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=120)
    roll_type: str
    source_id: str | None = Field(default=None, max_length=500)
    label: str | None = Field(default=None, max_length=160)
    visibility: str = "table"
    target_value: int | None = Field(default=None, ge=1, le=100_000)
    hide_target: bool = False
    reason: str | None = Field(default=None, max_length=500)
    session_id: str | None = Field(default=None, max_length=120)
    scene_id: int | None = Field(default=None, ge=1)
    action_id: int | None = Field(default=None, ge=1)


class DiceRollEventResponse(BaseModel):
    id: int
    request_id: str
    session_id: str | None = None
    campaign_id: str
    character_id: str | None = None
    actor_id: str
    actor_role: str
    roll_type: str
    label: str
    formula: str
    dice: str
    modifier: int
    individual_results: list[int]
    subtotal: int
    total: int
    target_value: int | None = None
    target_hidden: bool = False
    outcome: str | None = None
    visibility: str
    source: str
    source_id: str | None = None
    scene_id: int | None = None
    action_id: int | None = None
    reason: str | None = None
    created_at: str
    voided: bool = False
    voided_at: str | None = None
    voided_by: str | None = None
    void_reason: str | None = None


class DiceRollVoidRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


class DiceRollRequestCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=120)
    character_id: str = Field(min_length=1, max_length=120)
    roll_type: str
    source_id: str | None = Field(default=None, max_length=500)
    formula: str | None = Field(default=None, max_length=32)
    label: str | None = Field(default=None, max_length=160)
    visibility: str = "owner"
    target_value: int | None = Field(default=None, ge=1, le=100_000)
    hide_target: bool = False
    reason: str | None = Field(default=None, max_length=500)
    session_id: str | None = Field(default=None, max_length=120)
    scene_id: int | None = Field(default=None, ge=1)
    action_id: int | None = Field(default=None, ge=1)
    expires_in_hours: int = Field(default=24, ge=1, le=168)


class DiceRollRequestResponse(BaseModel):
    id: int
    request_id: str
    session_id: str | None = None
    campaign_id: str
    character_id: str
    requested_by: str
    roll_type: str
    label: str
    formula: str
    visibility: str
    source: str
    source_id: str | None = None
    scene_id: int | None = None
    action_id: int | None = None
    target_value: int | None = None
    target_hidden: bool = False
    reason: str | None = None
    status: str
    created_at: str
    expires_at: str
    completed_at: str | None = None
    completed_by: str | None = None
    completion_request_id: str | None = None
    roll_event_id: int | None = None


class DiceRollRequestComplete(BaseModel):
    request_id: str = Field(min_length=8, max_length=120)


class GameSessionCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=120)
    title: str = Field(min_length=1, max_length=180)
    session_number: int | None = Field(default=None, ge=1, le=10_000)
    private_notes: str | None = Field(default=None, max_length=2_000)


class GameSessionStatusUpdate(BaseModel):
    status: str


class SceneCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=120)
    session_id: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1, max_length=180)
    location_name: str = Field(min_length=1, max_length=180)
    location_source: str | None = Field(default=None, max_length=500)
    public_description: str | None = Field(default=None, max_length=2_000)
    objective: str | None = Field(default=None, max_length=500)
    private_notes: str | None = Field(default=None, max_length=2_000)
    visibility: str = "table"


class SceneUpdate(BaseModel):
    expected_version: int = Field(ge=1)
    fields: dict[str, Any] = Field(default_factory=dict)


class SceneStatusUpdate(BaseModel):
    status: str
    summary: str | None = Field(default=None, max_length=2_000)


class SceneParticipantCreate(BaseModel):
    participant_type: str
    character_id: str | None = Field(default=None, max_length=120)
    npc_name: str | None = Field(default=None, max_length=180)
    npc_source: str | None = Field(default=None, max_length=500)
    public_label: str = Field(min_length=1, max_length=180)
    public_status: str | None = Field(default=None, max_length=180)
    private_status: str | None = Field(default=None, max_length=500)
    visible_to_players: bool = True


class SceneParticipantUpdate(BaseModel):
    fields: dict[str, Any] = Field(default_factory=dict)


class SceneElementCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=120)
    element_type: str
    title: str = Field(min_length=1, max_length=180)
    public_description: str | None = Field(default=None, max_length=2_000)
    private_description: str | None = Field(default=None, max_length=2_000)
    status: str
    visibility: str = "gm"


class SceneElementUpdate(BaseModel):
    fields: dict[str, Any] = Field(default_factory=dict)


class SceneActionCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=120)
    character_id: str | None = Field(default=None, max_length=120)
    action_type: str
    description: str = Field(min_length=1, max_length=600)
    target_label: str | None = Field(default=None, max_length=180)
    visibility: str = "table"


class SceneActionResolution(BaseModel):
    resolution: str | None = Field(default=None, max_length=1_200)


class SceneRollRequestCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=120)
    roll_type: str
    source_id: str | None = Field(default=None, max_length=500)
    formula: str | None = Field(default=None, max_length=32)
    label: str | None = Field(default=None, max_length=160)
    visibility: str = "owner"
    target_value: int | None = Field(default=None, ge=1, le=100_000)
    hide_target: bool = False
    reason: str | None = Field(default=None, max_length=500)


class SceneConsequenceCreate(BaseModel):
    character_id: str = Field(min_length=1, max_length=120)
    action_id: int | None = Field(default=None, ge=1)
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    title: str = Field(min_length=1, max_length=180)
    public_text: str | None = Field(default=None, max_length=2_000)
    private_text: str | None = Field(default=None, max_length=2_000)
    visibility: str = "table"


class SceneManualEventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    public_text: str | None = Field(default=None, max_length=2_000)
    private_text: str | None = Field(default=None, max_length=2_000)
    visibility: str = "table"


class SceneVoidRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


class ContractCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    session_id: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1, max_length=180)
    slug: str | None = Field(default=None, max_length=180)
    contract_type: str = "outro"
    issuer_name: str = Field(min_length=1, max_length=180)
    issuer_type: str | None = Field(default=None, max_length=120)
    issuer_source: str | None = Field(default=None, max_length=500)
    location_name: str | None = Field(default=None, max_length=180)
    location_source: str | None = Field(default=None, max_length=500)
    public_summary: str = Field(min_length=1, max_length=500)
    public_briefing: str = Field(min_length=1, max_length=3000)
    private_briefing: str | None = Field(default=None, max_length=3000)
    risk_label: str = Field(default="Não informado", max_length=120)
    recommended_level: str | None = Field(default=None, max_length=80)
    deadline_text: str | None = Field(default=None, max_length=180)
    visibility: str = "table"


class VersionedPatch(BaseModel):
    expected_version: int = Field(ge=1)
    fields: dict[str, Any] = Field(default_factory=dict)


class ContractTransitionRequest(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    reason: str | None = Field(default=None, max_length=500)


class ContractAcceptRequest(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    character_id: str | None = Field(default=None, max_length=120)
    public_role: str | None = Field(default=None, max_length=180)


class ContractObjectiveCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    title: str = Field(min_length=1, max_length=180)
    public_description: str = Field(min_length=1, max_length=3000)
    private_description: str | None = Field(default=None, max_length=3000)
    objective_type: str = "narrative"
    status: str = "hidden"
    required: bool = True
    order_index: int | None = Field(default=None, ge=0)
    progress_current: int | float | None = None
    progress_target: int | float | None = None
    revealed_to_players: bool = False


class ObjectiveStatusRequest(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    status: str


class ObjectiveOrderRequest(BaseModel):
    order: list[int] = Field(min_length=1)


class ContractAssignmentCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    character_id: str = Field(min_length=1, max_length=120)
    public_role: str | None = Field(default=None, max_length=180)


class ContractSceneLinkCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    scene_id: int = Field(ge=1)
    objective_id: int | None = Field(default=None, ge=1)
    link_type: str = "other"


class ContractLinkedSceneCreate(SceneCreate):
    objective_id: int | None = Field(default=None, ge=1)
    link_type: str = "other"


class ContractRewardCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    reward_type: str
    label: str = Field(min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=3000)
    quantity: int | float | None = None
    currency_type: str | None = Field(default=None, max_length=80)
    item_source: str | None = Field(default=None, max_length=500)
    item_name: str | None = Field(default=None, max_length=180)
    reputation_faction: str | None = Field(default=None, max_length=180)
    reputation_amount: int | None = None
    visibility: str = "table"


class RewardDeliveryRequest(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    character_ids: list[str] = Field(default_factory=list)


class ReputationApplyRequest(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    faction_name: str = Field(min_length=1, max_length=180)
    delta: int = Field(ge=-1000, le=1000)
    reason: str = Field(min_length=1, max_length=500)
    contract_id: int | None = Field(default=None, ge=1)
    character_id: str | None = Field(default=None, max_length=120)
    party_id: str | None = Field(default="group", max_length=120)


class ContractEventVoidRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


class NpcCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    name: str = Field(min_length=1, max_length=180)
    slug: str | None = Field(default=None, max_length=180)
    aliases: list[str] = Field(default_factory=list)
    portrait_path: str | None = Field(default=None, max_length=500)
    race: str | None = Field(default=None, max_length=120)
    class_or_role: str | None = Field(default=None, max_length=180)
    occupation: str | None = Field(default=None, max_length=180)
    faction_names: list[str] = Field(default_factory=list)
    public_description: str | None = Field(default=None, max_length=4000)
    private_description: str | None = Field(default=None, max_length=4000)
    canonical_status: str | None = Field(default=None, max_length=120)
    visible_to_players: bool = False
    current_location: str | None = Field(default=None, max_length=180)
    public_status: str | None = Field(default=None, max_length=300)
    private_status: str | None = Field(default=None, max_length=500)
    disposition_summary: str | None = Field(default=None, max_length=500)
    active: bool = True


class NpcImportRequest(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    source_path: str = Field(min_length=1, max_length=500)
    visible_to_players: bool | None = None


class NpcRelationshipCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    target_type: str
    target_id: str | None = Field(default=None, max_length=180)
    target_label: str = Field(min_length=1, max_length=180)
    public_label: str | None = Field(default=None, max_length=180)
    private_label: str | None = Field(default=None, max_length=180)
    attitude_value: int | None = Field(default=None, ge=-100, le=100)
    trust_value: int | None = Field(default=None, ge=-100, le=100)
    fear_value: int | None = Field(default=None, ge=-100, le=100)
    respect_value: int | None = Field(default=None, ge=-100, le=100)
    status: str = "active"
    public_notes: str | None = Field(default=None, max_length=4000)
    private_notes: str | None = Field(default=None, max_length=4000)
    visible_to_players: bool = False
    reason: str = Field(min_length=2, max_length=500)


class NpcVersionedUpdate(BaseModel):
    expected_version: int = Field(ge=1)
    fields: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(default="Atualização administrativa", min_length=2, max_length=500)


class NpcMemoryCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    memory_type: str
    title: str = Field(min_length=1, max_length=180)
    summary: str = Field(min_length=1, max_length=4000)
    private_details: str | None = Field(default=None, max_length=4000)
    subject_type: str | None = Field(default=None, max_length=80)
    subject_id: str | None = Field(default=None, max_length=180)
    subject_label: str | None = Field(default=None, max_length=180)
    scene_id: int | None = Field(default=None, ge=1)
    contract_id: int | None = Field(default=None, ge=1)
    character_id: str | None = Field(default=None, max_length=180)
    importance: str = "medium"
    confidence: str = "believed"
    visibility: str = "gm"
    status: str = "active"
    occurred_at: str | None = None
    learned_at: str | None = None
    responsible_party: str | None = Field(default=None, max_length=180)
    beneficiary: str | None = Field(default=None, max_length=180)
    due_text: str | None = Field(default=None, max_length=300)
    obligation_status: str | None = None
    linked_contract_id: int | None = Field(default=None, ge=1)
    linked_scene_id: int | None = Field(default=None, ge=1)


class NpcMemoryContradict(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    title: str = Field(min_length=1, max_length=180)
    summary: str = Field(min_length=1, max_length=4000)
    private_details: str | None = Field(default=None, max_length=4000)
    confidence: str = "confirmed"
    visibility: str = "gm"
    reason: str = Field(min_length=2, max_length=500)


class NpcEncounterCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    scene_id: int = Field(ge=1)
    contract_id: int | None = Field(default=None, ge=1)
    session_id: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1, max_length=180)
    public_summary: str | None = Field(default=None, max_length=4000)
    private_summary: str | None = Field(default=None, max_length=4000)
    occurred_at: str | None = None


class NpcContractLinkCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    contract_id: int = Field(ge=1)
    role: str | None = Field(default=None, max_length=180)
    visible_to_players: bool = False


class NpcEventVoidRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


class WorldMapCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    title: str = Field(min_length=1, max_length=180)
    source_path: str | None = Field(default=None, max_length=500)
    image_path: str | None = Field(default=None, max_length=500)
    map_type: str = "custom"
    width: float | None = Field(default=None, gt=0)
    height: float | None = Field(default=None, gt=0)
    coordinate_system: str = "percentage"
    public_description: str | None = Field(default=None, max_length=4000)
    private_description: str | None = Field(default=None, max_length=4000)
    visibility: str = "gm"
    active: bool = True


class WorldImportRequest(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    source_path: str = Field(min_length=1, max_length=500)
    visibility: str | None = None
    discovered_by_default: bool | None = None
    confirm: bool = False


class WorldVersionedUpdate(BaseModel):
    expected_version: int = Field(ge=1)
    fields: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(default="Atualização espacial", min_length=2, max_length=500)


class WorldLocationCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    map_id: int | None = Field(default=None, ge=1)
    source_path: str | None = Field(default=None, max_length=500)
    slug: str | None = Field(default=None, max_length=180)
    name: str = Field(min_length=1, max_length=180)
    aliases: list[str] = Field(default_factory=list)
    location_type: str = "unknown"
    parent_location_id: int | None = Field(default=None, ge=1)
    territory_name: str | None = Field(default=None, max_length=180)
    public_description: str | None = Field(default=None, max_length=4000)
    private_description: str | None = Field(default=None, max_length=4000)
    portrait_or_cover_path: str | None = Field(default=None, max_length=500)
    marker_icon: str | None = Field(default=None, max_length=100)
    x: float | None = Field(default=None, ge=0, le=100)
    y: float | None = Field(default=None, ge=0, le=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    discovered_by_default: bool = False
    visibility: str = "gm"
    canon_status: str | None = Field(default=None, max_length=120)
    active: bool = True
    public_status: str | None = Field(default=None, max_length=500)
    private_status: str | None = Field(default=None, max_length=500)
    controlling_faction: str | None = Field(default=None, max_length=180)
    danger_label: str | None = Field(default=None, max_length=180)
    accessible: bool = True
    current_scene_id: int | None = Field(default=None, ge=1)


class LocationDiscoveryCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    discoverer_type: str = "campaign"
    character_id: str | None = Field(default=None, max_length=180)
    party_id: str | None = Field(default="group", max_length=180)
    knowledge_level: str = "discovered"
    public_name_override: str | None = Field(default=None, max_length=180)
    source_scene_id: int | None = Field(default=None, ge=1)
    source_contract_id: int | None = Field(default=None, ge=1)
    notes: str | None = Field(default=None, max_length=4000)


class TravelRouteCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    origin_location_id: int = Field(ge=1)
    destination_location_id: int = Field(ge=1)
    reverse_route_id: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1, max_length=180)
    route_type: str = "custom"
    public_description: str | None = Field(default=None, max_length=4000)
    private_description: str | None = Field(default=None, max_length=4000)
    distance_value: float | None = Field(default=None, ge=0)
    distance_unit: str | None = Field(default=None, max_length=40)
    duration_value: float | None = Field(default=None, ge=0)
    duration_unit: str | None = Field(default=None, max_length=40)
    difficulty_label: str | None = Field(default=None, max_length=120)
    danger_label: str | None = Field(default=None, max_length=120)
    required_condition: str | None = Field(default=None, max_length=300)
    public: bool = False
    active: bool = True


class JourneyCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    session_id: int | None = Field(default=None, ge=1)
    contract_id: int | None = Field(default=None, ge=1)
    route_id: int | None = Field(default=None, ge=1)
    origin_location_id: int = Field(ge=1)
    destination_location_id: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=180)
    visibility: str = "table"
    planned_duration_value: float | None = Field(default=None, ge=0)
    planned_duration_unit: str | None = Field(default=None, max_length=40)
    progress_target: float = Field(default=1, gt=0)


class JourneyParticipantCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    participant_type: str
    character_id: str | None = Field(default=None, max_length=180)
    npc_id: int | None = Field(default=None, ge=1)
    public_label: str = Field(min_length=1, max_length=180)


class JourneyParticipantRemove(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    reason: str = Field(min_length=2, max_length=500)


class JourneyTransitionRequest(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    expected_version: int = Field(ge=1)
    reason: str | None = Field(default=None, max_length=500)


class JourneyAdvanceRequest(JourneyTransitionRequest):
    amount: float = Field(gt=0)


class JourneySceneLinkCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    scene_id: int = Field(ge=1)
    stage_label: str | None = Field(default=None, max_length=180)
    progress_value: float | None = Field(default=None, ge=0)


class LocationLinkCreate(BaseModel):
    request_id: str = Field(min_length=8, max_length=140)
    location_id: int = Field(ge=1)
    role: str = Field(default="related", max_length=80)
    public: bool = False
