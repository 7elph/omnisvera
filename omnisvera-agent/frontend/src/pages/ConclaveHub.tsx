import { useEffect, useMemo, useState } from "react";
import {
  acceptContract,
  AccessMode,
  addContractAssignment,
  approveContractReward,
  ContractObjective,
  ContractObjectiveStatus,
  ContractRecord,
  ContractReward,
  createContract,
  createContractObjective,
  createContractReward,
  createContractScene,
  deliverContractReward,
  GameScene,
  getCurrentOperationalContract,
  getContract,
  linkContractScene,
  listContracts,
  listPlayableCharacters,
  listNpcs,
  listReputation,
  listScenes,
  mediaUrlFromVaultPath,
  newContractRequestId,
  PlayableCharacterSummary,
  NpcRecord,
  linkNpcContract,
  ReputationLedger,
  revertReputation,
  setContractObjectiveStatus,
  transitionContract,
  updateContract,
  voidContractEvent,
} from "../api";

const CONTRACT_TYPES = ["investigação", "escolta", "recuperação", "caça", "proteção", "exploração", "negociação", "entrega", "resgate", "outro"];
const LINK_TYPES = ["preparation", "investigation", "encounter", "resolution", "aftermath", "other"];
const REWARD_TYPES = ["currency", "item", "reputation", "information", "favor", "access", "custom"];

const STATUS_LABEL: Record<string, string> = {
  draft: "Rascunho",
  published: "Disponível",
  accepted: "Aceito",
  active: "Em andamento",
  completed: "Concluído",
  failed: "Falhou",
  abandoned: "Abandonado",
  cancelled: "Cancelado",
  hidden: "Oculto",
  available: "Revelado",
  skipped: "Pulado",
  proposed: "Proposta",
  approved: "Aprovada",
  delivered: "Entregue",
  withheld: "Retida",
};

const SECTION_STATUS = [
  { key: "available", title: "Disponíveis", statuses: ["published"] },
  { key: "accepted", title: "Aceitos", statuses: ["accepted"] },
  { key: "active", title: "Em andamento", statuses: ["active"] },
  { key: "history", title: "Histórico", statuses: ["completed", "failed", "abandoned", "cancelled"] },
];

function label(value?: string | null) {
  if (!value) return "Não informado";
  return STATUS_LABEL[value] || value;
}

function progress(objective: ContractObjective) {
  if (objective.progress_current == null || objective.progress_target == null) return "Narrativo";
  return `${objective.progress_current}/${objective.progress_target}`;
}

function rewardSummary(rewards: ContractReward[]) {
  const visible = rewards.filter((item) => item.visibility === "table");
  if (!visible.length) return "Recompensa ainda não revelada.";
  return visible.map((item) => item.quantity ? `${item.label} (${item.quantity})` : item.label).join(" · ");
}

function time(value?: string | null) {
  if (!value) return "";
  return new Date(value).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export default function ConclaveHub({
  mode,
  onOpenScene,
  embedded = false,
}: {
  mode: AccessMode;
  onOpenScene: (sceneId?: number) => void;
  embedded?: boolean;
}) {
  const isGm = mode === "gm";
  const [contracts, setContracts] = useState<ContractRecord[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(() => {
    const stored = Number(localStorage.getItem("omnisvera_selected_contract") || "");
    return Number.isFinite(stored) && stored > 0 ? stored : null;
  });
  const [contract, setContract] = useState<ContractRecord | null>(null);
  const [characters, setCharacters] = useState<PlayableCharacterSummary[]>([]);
  const [npcs, setNpcs] = useState<NpcRecord[]>([]);
  const [scenes, setScenes] = useState<GameScene[]>([]);
  const [reputation, setReputation] = useState<ReputationLedger[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const [createDraft, setCreateDraft] = useState({
    title: "",
    issuer_name: "Administração do Conclave",
    contract_type: "outro",
    location_name: "",
    risk_label: "Não informado",
    public_summary: "",
    public_briefing: "",
    private_briefing: "",
    deadline_text: "",
  });
  const [editDraft, setEditDraft] = useState({
    title: "",
    issuer_name: "",
    location_name: "",
    risk_label: "",
    public_summary: "",
    public_briefing: "",
    private_briefing: "",
    deadline_text: "",
  });
  const [objectiveDraft, setObjectiveDraft] = useState({
    title: "",
    public_description: "",
    private_description: "",
    objective_type: "narrative",
    status: "hidden",
    required: true,
    progress_current: "",
    progress_target: "",
    revealed_to_players: false,
  });
  const [assignmentDraft, setAssignmentDraft] = useState({ character_id: "", public_role: "" });
  const [npcDraft, setNpcDraft] = useState({ npc_id: "", role: "", visible_to_players: false });
  const [sceneLinkDraft, setSceneLinkDraft] = useState({ scene_id: "", objective_id: "", link_type: "investigation" });
  const [linkedSceneDraft, setLinkedSceneDraft] = useState({
    title: "",
    location_name: "",
    objective: "",
    public_description: "",
    private_notes: "",
    objective_id: "",
    link_type: "encounter",
  });
  const [rewardDraft, setRewardDraft] = useState({
    reward_type: "currency",
    label: "Recompensa técnica",
    description: "",
    quantity: "1",
    currency_type: "moeda",
    item_source: "",
    item_name: "",
    reputation_faction: "Conclave dos Errantes",
    reputation_amount: "1",
    visibility: "table",
  });
  const [rewardTargets, setRewardTargets] = useState<Record<number, string>>({});

  async function refresh(preferredId?: number | null) {
    const all = await listContracts();
    setContracts(all);
    const stored = Number(localStorage.getItem("omnisvera_selected_contract") || "");
    const storedId = Number.isFinite(stored) && stored > 0 ? stored : null;
    const wanted = preferredId ?? selectedId ?? storedId ?? all[0]?.id ?? null;
    if (wanted) {
      const detail = await getContract(wanted);
      setContract(detail);
      setSelectedId(detail.id);
      localStorage.setItem("omnisvera_selected_contract", String(detail.id));
    } else {
      setContract(null);
      setSelectedId(null);
    }
    setCharacters(await listPlayableCharacters());
    setNpcs(await listNpcs());
    setScenes(await listScenes());
    setReputation(await listReputation(isGm ? { party_id: "group" } : {}));
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    refresh()
      .catch((cause) => !cancelled && setError(cause instanceof Error ? cause.message : "Não foi possível carregar contratos."))
      .finally(() => !cancelled && setLoading(false));
    const openContract = (event: Event) => {
      const id = Number((event as CustomEvent<number>).detail);
      if (!Number.isFinite(id)) return;
      void refresh(id);
    };
    const refreshContracts = () => void refresh();
    window.addEventListener("omnisvera-open-contract", openContract);
    window.addEventListener("omnisvera-contract-updated", refreshContracts);
    return () => {
      cancelled = true;
      window.removeEventListener("omnisvera-open-contract", openContract);
      window.removeEventListener("omnisvera-contract-updated", refreshContracts);
    };
  }, [mode]);

  useEffect(() => {
    if (!contract) return;
    setEditDraft({
      title: contract.title || "",
      issuer_name: contract.issuer_name || "",
      location_name: contract.location_name || "",
      risk_label: contract.risk_label || "",
      public_summary: contract.public_summary || "",
      public_briefing: contract.public_briefing || "",
      private_briefing: contract.private_briefing || "",
      deadline_text: contract.deadline_text || "",
    });
    const firstAssigned = contract.assigned_character_ids?.[0] || "";
    setRewardTargets((current) => {
      const next = { ...current };
      for (const reward of contract.rewards) if (!next[reward.id]) next[reward.id] = firstAssigned;
      return next;
    });
  }, [contract?.id, contract?.version]);

  const grouped = useMemo(() => {
    const result: Record<string, ContractRecord[]> = {};
    for (const section of SECTION_STATUS) {
      result[section.key] = contracts.filter((item) => section.statuses.includes(item.status));
    }
    if (isGm) {
      result.available = [...contracts.filter((item) => item.status === "draft"), ...result.available];
    }
    return result;
  }, [contracts, isGm]);

  const characterById = useMemo(() => new Map(characters.map((item) => [item.id, item])), [characters]);
  const activeContract = getCurrentOperationalContract(contracts);
  const activeObjective = contract?.objectives.find((item) => item.status === "active") || contract?.objectives.find((item) => item.status === "available");

  async function run(operation: () => Promise<unknown>, message: string, preferredId?: number | null) {
    if (busy) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await operation();
      setNotice(message);
      await refresh(preferredId ?? contract?.id ?? selectedId);
      window.dispatchEvent(new CustomEvent("omnisvera-contract-updated"));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "A operação de contrato falhou.");
    } finally {
      setBusy(false);
    }
  }

  async function submitContract() {
    await run(async () => {
      const created = await createContract({
        request_id: newContractRequestId("contract-create"),
        ...createDraft,
        public_summary: createDraft.public_summary || createDraft.public_briefing,
        visibility: "table",
      });
      setCreateDraft({ title: "", issuer_name: "Administração do Conclave", contract_type: "outro", location_name: "", risk_label: "Não informado", public_summary: "", public_briefing: "", private_briefing: "", deadline_text: "" });
      localStorage.setItem("omnisvera_selected_contract", String(created.id));
      setSelectedId(created.id);
    }, "Contrato criado.", null);
  }

  async function submitEdit() {
    if (!contract) return;
    await run(() => updateContract(contract.id, contract.version, editDraft), "Contrato atualizado.", contract.id);
  }

  async function playerAccept() {
    if (!contract) return;
    const owner = characters.find((item) => item.access_level === "owner")?.id;
    await run(() => acceptContract(contract.id, { request_id: newContractRequestId("contract-accept"), character_id: owner, public_role: "Contratante aceito" }), "Contrato aceito.", contract.id);
  }

  async function submitObjective() {
    if (!contract) return;
    await run(() => createContractObjective(contract.id, {
      request_id: newContractRequestId("objective"),
      ...objectiveDraft,
      progress_current: objectiveDraft.progress_current === "" ? undefined : Number(objectiveDraft.progress_current),
      progress_target: objectiveDraft.progress_target === "" ? undefined : Number(objectiveDraft.progress_target),
    }), "Objetivo criado.", contract.id);
    setObjectiveDraft({ title: "", public_description: "", private_description: "", objective_type: "narrative", status: "hidden", required: true, progress_current: "", progress_target: "", revealed_to_players: false });
  }

  async function submitAssignment() {
    if (!contract || !assignmentDraft.character_id) return;
    await run(() => addContractAssignment(contract.id, { request_id: newContractRequestId("assignment"), ...assignmentDraft }), "Personagem atribuído.", contract.id);
    setAssignmentDraft({ character_id: "", public_role: "" });
  }

  async function submitNpcLink() {
    if (!contract || !npcDraft.npc_id) return;
    await run(() => linkNpcContract(Number(npcDraft.npc_id), { request_id: newContractRequestId("npc-contract"), contract_id: contract.id, role: npcDraft.role || null, visible_to_players: npcDraft.visible_to_players }), "NPC vinculado ao contrato.", contract.id);
    setNpcDraft({ npc_id: "", role: "", visible_to_players: false });
  }

  async function submitSceneLink() {
    if (!contract || !sceneLinkDraft.scene_id) return;
    await run(() => linkContractScene(contract.id, {
      request_id: newContractRequestId("scene-link"),
      scene_id: Number(sceneLinkDraft.scene_id),
      objective_id: sceneLinkDraft.objective_id ? Number(sceneLinkDraft.objective_id) : undefined,
      link_type: sceneLinkDraft.link_type,
    }), "Cena vinculada.", contract.id);
  }

  async function submitLinkedScene() {
    if (!contract) return;
    await run(() => createContractScene(contract.id, {
      request_id: newContractRequestId("contract-scene"),
      title: linkedSceneDraft.title,
      location_name: linkedSceneDraft.location_name,
      objective: linkedSceneDraft.objective,
      public_description: linkedSceneDraft.public_description,
      private_notes: linkedSceneDraft.private_notes,
      visibility: "table",
      objective_id: linkedSceneDraft.objective_id ? Number(linkedSceneDraft.objective_id) : undefined,
      link_type: linkedSceneDraft.link_type,
    }), "Cena criada e vinculada.", contract.id);
    setLinkedSceneDraft({ title: "", location_name: "", objective: "", public_description: "", private_notes: "", objective_id: "", link_type: "encounter" });
  }

  async function submitReward() {
    if (!contract) return;
    await run(() => createContractReward(contract.id, {
      request_id: newContractRequestId("reward"),
      ...rewardDraft,
      quantity: rewardDraft.quantity === "" ? undefined : Number(rewardDraft.quantity),
      reputation_amount: rewardDraft.reputation_amount === "" ? undefined : Number(rewardDraft.reputation_amount),
    }), "Recompensa proposta.", contract.id);
  }

  async function deliverReward(reward: ContractReward) {
    if (!contract || busy) return;
    if (!window.confirm(`Confirmar entrega de "${reward.label}"?`)) return;
    const target = rewardTargets[reward.id] || contract.assigned_character_ids[0] || "";
    const character_ids = reward.reward_type === "reputation" ? [] : [target].filter(Boolean);
    await run(() => deliverContractReward(reward.id, { request_id: newContractRequestId("reward-delivery"), character_ids }), "Recompensa entregue.", contract.id);
    window.dispatchEvent(new CustomEvent("omnisvera-character-state"));
  }

  function openCharacter(characterId: string) {
    window.dispatchEvent(new CustomEvent("omnisvera-open-character", { detail: characterId }));
  }

  if (loading) return <section className={`panel conclave-page ${embedded ? "conclave-page-embedded" : ""}`}><p className="muted">Carregando o quadro de contratos...</p></section>;

  return <section className={`panel conclave-page ${embedded ? "conclave-page-embedded" : ""}`}>
    <header className="conclave-hero">
      <div>
        <p className="eyebrow">Hub de campanha</p>
        <h2>Conclave dos Errantes</h2>
        <p>Quadro de contratos, objetivos, cenas vinculadas, recompensas e reputação auditável.</p>
      </div>
      <div className="conclave-stats" aria-label="Resumo da campanha">
        <span><small>Cena ativa</small><strong>{scenes.find((item) => item.status === "active")?.title || "Sem cena ativa"}</strong></span>
        <span><small>Contratos ativos</small><strong>{contracts.filter((item) => item.status === "active").length}</strong></span>
        <span><small>Reputação do grupo</small><strong>{reputation.find((item) => item.party_id === "group")?.resulting_value ?? 0}</strong></span>
      </div>
    </header>

    {notice && <p className="success-text" role="status">{notice}</p>}
    {error && <p className="warning-text" role="alert">{error}</p>}

    {isGm && <details className="conclave-admin" open={!contracts.length}>
      <summary>Criar contrato</summary>
      <div className="conclave-form-grid">
        <label>Título<input value={createDraft.title} onChange={(event) => setCreateDraft({ ...createDraft, title: event.target.value })} /></label>
        <label>Contratante<input value={createDraft.issuer_name} onChange={(event) => setCreateDraft({ ...createDraft, issuer_name: event.target.value })} /></label>
        <label>Tipo<select value={createDraft.contract_type} onChange={(event) => setCreateDraft({ ...createDraft, contract_type: event.target.value })}>{CONTRACT_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <label>Local<input value={createDraft.location_name} onChange={(event) => setCreateDraft({ ...createDraft, location_name: event.target.value })} /></label>
        <label>Risco<input value={createDraft.risk_label} onChange={(event) => setCreateDraft({ ...createDraft, risk_label: event.target.value })} /></label>
        <label>Prazo textual<input value={createDraft.deadline_text} onChange={(event) => setCreateDraft({ ...createDraft, deadline_text: event.target.value })} /></label>
        <label className="span-2">Resumo público<textarea value={createDraft.public_summary} onChange={(event) => setCreateDraft({ ...createDraft, public_summary: event.target.value })} /></label>
        <label className="span-2">Briefing público<textarea value={createDraft.public_briefing} onChange={(event) => setCreateDraft({ ...createDraft, public_briefing: event.target.value })} /></label>
        <label className="span-2">Briefing privado do Mestre<textarea value={createDraft.private_briefing} onChange={(event) => setCreateDraft({ ...createDraft, private_briefing: event.target.value })} /></label>
        <button disabled={busy || !createDraft.title || !createDraft.public_briefing} onClick={() => void submitContract()}>Criar rascunho</button>
      </div>
    </details>}

    <div className="conclave-layout">
      <div className="contract-board">
        {SECTION_STATUS.map((section) => {
          const items = grouped[section.key] || [];
          if (!items.length) return null;
          return <section key={section.key} className="contract-section">
            <header><h3>{section.title}</h3><span>{items.length}</span></header>
            {items.map((item) => <button key={`${section.key}-${item.id}`} className={`contract-card ${selectedId === item.id ? "active" : ""}`} onClick={() => void refresh(item.id)}>
              <strong>{item.title}</strong>
              <small>{item.issuer_name} · {item.contract_type} · {label(item.status)}</small>
              <span>{item.location_name || "Local não informado"} · Risco: {item.risk_label}</span>
              <p>{item.public_summary}</p>
              <em>{rewardSummary(item.rewards)}</em>
              <footer><span>{item.revealed_objective_count} objetivos revelados</span><span>{item.assigned_character_ids.length} personagens</span></footer>
            </button>)}
          </section>;
        })}
        {!contracts.length && <p className="sheet-empty">{isGm ? "Nenhuma missão cadastrada." : "Nenhuma missão disponível no momento."}</p>}
      </div>

      <aside className="contract-detail" aria-live="polite">
        {!contract ? <div className="contract-empty-detail">
          <h3>Nenhum contrato selecionado</h3>
          <p>{isGm ? "Crie ou selecione um contrato no quadro." : "Nenhum contrato disponível no momento."}</p>
        </div> : <>
          <header>
            <div>
              <small>{label(contract.status)} · {contract.contract_type}</small>
              <h3>{contract.title}</h3>
              <p>{contract.issuer_name} · {contract.location_name || "Local não informado"}</p>
            </div>
            <span>{contract.risk_label}</span>
          </header>
          <p>{contract.public_briefing}</p>
          <button className="secondary-button" onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-map"))}>Abrir local e planejar viagem</button>
          <div className="contract-meta-grid">
            <span><small>Prazo</small><strong>{contract.deadline_text || "Sem prazo"}</strong></span>
            <span><small>Recompensa pública</small><strong>{rewardSummary(contract.rewards)}</strong></span>
            <span><small>Progresso</small><strong>{activeObjective ? `${activeObjective.title}: ${progress(activeObjective)}` : "Sem objetivo ativo"}</strong></span>
          </div>
          {isGm && contract.private_briefing && <section className="contract-private"><strong>Privado do Mestre</strong><p>{contract.private_briefing}</p></section>}

          <div className="contract-actions">
            {!isGm && contract.status === "published" && <button disabled={busy} onClick={() => void playerAccept()}>Aceitar contrato</button>}
            {isGm && contract.status === "draft" && <button disabled={busy} onClick={() => void run(() => transitionContract(contract.id, "publish", newContractRequestId("contract-publish")), "Contrato publicado.", contract.id)}>Publicar</button>}
            {isGm && contract.status === "published" && <button disabled={busy} onClick={() => void run(() => acceptContract(contract.id, { request_id: newContractRequestId("contract-gm-accept") }), "Contrato aceito.", contract.id)}>Aceitar pelo grupo</button>}
            {isGm && contract.status === "accepted" && <button disabled={busy} onClick={() => void run(() => transitionContract(contract.id, "start", newContractRequestId("contract-start")), "Contrato iniciado.", contract.id)}>Iniciar</button>}
            {isGm && contract.status === "active" && <button disabled={busy} onClick={() => window.confirm("Concluir este contrato?") && void run(() => transitionContract(contract.id, "complete", newContractRequestId("contract-complete")), "Contrato concluído.", contract.id)}>Concluir</button>}
            {isGm && contract.status === "active" && <button className="danger-button subtle" disabled={busy} onClick={() => window.confirm("Marcar contrato como falho?") && void run(() => transitionContract(contract.id, "fail", newContractRequestId("contract-fail"), "Falha registrada pelo Mestre."), "Contrato marcado como falho.", contract.id)}>Falhar</button>}
            {isGm && contract.status === "active" && <button className="danger-button subtle" disabled={busy} onClick={() => window.confirm("Abandonar este contrato?") && void run(() => transitionContract(contract.id, "abandon", newContractRequestId("contract-abandon"), "Abandono registrado pelo Mestre."), "Contrato abandonado.", contract.id)}>Abandonar</button>}
            {isGm && ["draft", "published", "accepted"].includes(contract.status) && <button className="danger-button subtle" disabled={busy} onClick={() => window.confirm("Cancelar este contrato?") && void run(() => transitionContract(contract.id, "cancel", newContractRequestId("contract-cancel"), "Cancelado pelo Mestre."), "Contrato cancelado.", contract.id)}>Cancelar</button>}
          </div>

          {isGm && <details className="conclave-admin"><summary>Editar contrato</summary><div className="conclave-form-grid">
            <label>Título<input value={editDraft.title} onChange={(event) => setEditDraft({ ...editDraft, title: event.target.value })} /></label>
            <label>Contratante<input value={editDraft.issuer_name} onChange={(event) => setEditDraft({ ...editDraft, issuer_name: event.target.value })} /></label>
            <label>Local<input value={editDraft.location_name} onChange={(event) => setEditDraft({ ...editDraft, location_name: event.target.value })} /></label>
            <label>Risco<input value={editDraft.risk_label} onChange={(event) => setEditDraft({ ...editDraft, risk_label: event.target.value })} /></label>
            <label className="span-2">Resumo público<textarea value={editDraft.public_summary} onChange={(event) => setEditDraft({ ...editDraft, public_summary: event.target.value })} /></label>
            <label className="span-2">Briefing público<textarea value={editDraft.public_briefing} onChange={(event) => setEditDraft({ ...editDraft, public_briefing: event.target.value })} /></label>
            <label className="span-2">Briefing privado<textarea value={editDraft.private_briefing} onChange={(event) => setEditDraft({ ...editDraft, private_briefing: event.target.value })} /></label>
            <button disabled={busy} onClick={() => void submitEdit()}>Salvar edição</button>
          </div></details>}

          <section className="contract-subsection">
            <header><h4>Personagens atribuídos</h4></header>
            <div className="contract-character-list">{contract.assignments.length ? contract.assignments.map((assignment) => {
              const character = characterById.get(assignment.character_id);
              const portrait = mediaUrlFromVaultPath(character?.portrait);
              return <button key={assignment.id} onClick={() => openCharacter(assignment.character_id)}>
                {portrait ? <img src={portrait} alt="" /> : <span aria-hidden="true">P</span>}
                <strong>{character?.name || assignment.character_id}</strong>
                <small>{character?.class_name || "Classe não informada"} · {assignment.public_role || "Sem papel"}</small>
              </button>;
            }) : <p className="sheet-empty">Nenhum personagem atribuído.</p>}</div>
            {isGm && <div className="contract-inline-form">
              <select aria-label="Personagem do contrato" value={assignmentDraft.character_id} onChange={(event) => setAssignmentDraft({ ...assignmentDraft, character_id: event.target.value })}>
                <option value="">Adicionar personagem...</option>{characters.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
              <input aria-label="Papel público" placeholder="Papel público" value={assignmentDraft.public_role} onChange={(event) => setAssignmentDraft({ ...assignmentDraft, public_role: event.target.value })} />
              <button disabled={busy || !assignmentDraft.character_id} onClick={() => void submitAssignment()}>Atribuir</button>
            </div>}
          </section>

          <section className="contract-subsection">
            <header><h4>NPCs relacionados</h4></header>
            <div className="contract-character-list">{contract.npcs?.length ? contract.npcs.map((link) => <button key={link.id} onClick={() => window.dispatchEvent(new CustomEvent("omnisvera-open-npc", { detail: link.npc_id }))}>
              {mediaUrlFromVaultPath(link.portrait_path) ? <img src={mediaUrlFromVaultPath(link.portrait_path)!} alt="" /> : <span aria-hidden="true">N</span>}
              <strong>{link.name || `NPC ${link.npc_id}`}</strong><small>{link.role || link.class_or_role || link.occupation || "Papel não informado"}</small>
            </button>) : <p className="sheet-empty">Nenhum NPC vinculado.</p>}</div>
            {isGm && <div className="contract-inline-form"><select aria-label="NPC relacionado" value={npcDraft.npc_id} onChange={(event) => setNpcDraft({ ...npcDraft, npc_id: event.target.value })}><option value="">Adicionar NPC...</option>{npcs.map((npc) => <option key={npc.id} value={npc.id}>{npc.name}</option>)}</select><input aria-label="Papel do NPC" placeholder="Contratante, contato, alvo..." value={npcDraft.role} onChange={(event) => setNpcDraft({ ...npcDraft, role: event.target.value })} /><label><input type="checkbox" checked={npcDraft.visible_to_players} onChange={(event) => setNpcDraft({ ...npcDraft, visible_to_players: event.target.checked })} /> Visível</label><button disabled={busy || !npcDraft.npc_id} onClick={() => void submitNpcLink()}>Vincular NPC</button></div>}
          </section>

          <section className="contract-subsection">
            <header><h4>Objetivos</h4></header>
            <div className="objective-list">{contract.objectives.length ? contract.objectives.map((objective) => <article key={objective.id} className={`objective-card ${objective.status}`}>
              <header><strong>{objective.title}</strong><span>{label(objective.status)}</span></header>
              <p>{objective.public_description}</p>
              {isGm && objective.private_description && <small>Privado: {objective.private_description}</small>}
              <footer><span>{objective.required ? "Obrigatório" : "Opcional"}</span><span>{progress(objective)}</span></footer>
              {isGm && !["completed", "failed", "skipped"].includes(objective.status) && <div className="objective-actions">
                {(["available", "active", "completed", "failed", "skipped", "hidden"] as ContractObjectiveStatus[]).map((status) => <button key={status} disabled={busy || (status === "skipped" && objective.required)} onClick={() => void run(() => setContractObjectiveStatus(objective.id, status, newContractRequestId("objective-status")), `Objetivo: ${label(status)}.`, contract.id)}>{label(status)}</button>)}
              </div>}
            </article>) : <p className="sheet-empty">Nenhum objetivo revelado.</p>}</div>
            {isGm && <details className="conclave-admin"><summary>Criar objetivo</summary><div className="conclave-form-grid">
              <label>Título<input value={objectiveDraft.title} onChange={(event) => setObjectiveDraft({ ...objectiveDraft, title: event.target.value })} /></label>
              <label>Status<select value={objectiveDraft.status} onChange={(event) => setObjectiveDraft({ ...objectiveDraft, status: event.target.value })}><option value="hidden">Oculto</option><option value="available">Revelado</option><option value="active">Ativo</option></select></label>
              <label>Progresso atual<input type="number" value={objectiveDraft.progress_current} onChange={(event) => setObjectiveDraft({ ...objectiveDraft, progress_current: event.target.value })} /></label>
              <label>Progresso alvo<input type="number" value={objectiveDraft.progress_target} onChange={(event) => setObjectiveDraft({ ...objectiveDraft, progress_target: event.target.value })} /></label>
              <label className="check-label"><input type="checkbox" checked={objectiveDraft.required} onChange={(event) => setObjectiveDraft({ ...objectiveDraft, required: event.target.checked })} />Obrigatório</label>
              <label className="check-label"><input type="checkbox" checked={objectiveDraft.revealed_to_players} onChange={(event) => setObjectiveDraft({ ...objectiveDraft, revealed_to_players: event.target.checked })} />Revelar aos jogadores</label>
              <label className="span-2">Descrição pública<textarea value={objectiveDraft.public_description} onChange={(event) => setObjectiveDraft({ ...objectiveDraft, public_description: event.target.value })} /></label>
              <label className="span-2">Descrição privada<textarea value={objectiveDraft.private_description} onChange={(event) => setObjectiveDraft({ ...objectiveDraft, private_description: event.target.value })} /></label>
              <button disabled={busy || !objectiveDraft.title || !objectiveDraft.public_description} onClick={() => void submitObjective()}>Criar objetivo</button>
            </div></details>}
          </section>

          <section className="contract-subsection">
            <header><h4>Cenas relacionadas</h4></header>
            {contract.scene_links.length ? contract.scene_links.map((link) => <article key={link.id} className="scene-link-card">
              <strong>{link.scene_title || `Cena ${link.scene_id}`}</strong>
              <small>{label(link.scene_status)} · {link.link_type}{link.objective_title ? ` · ${link.objective_title}` : ""}</small>
              <button onClick={() => onOpenScene(link.scene_id)}>Abrir painel da cena</button>
            </article>) : <p className="sheet-empty">Nenhuma cena vinculada.</p>}
            {isGm && <details className="conclave-admin"><summary>Vincular ou criar cena</summary>
              <div className="contract-inline-form">
                <select aria-label="Cena existente" value={sceneLinkDraft.scene_id} onChange={(event) => setSceneLinkDraft({ ...sceneLinkDraft, scene_id: event.target.value })}><option value="">Cena existente...</option>{scenes.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
                <select aria-label="Objetivo da cena" value={sceneLinkDraft.objective_id} onChange={(event) => setSceneLinkDraft({ ...sceneLinkDraft, objective_id: event.target.value })}><option value="">Sem objetivo</option>{contract.objectives.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
                <select aria-label="Tipo de vínculo" value={sceneLinkDraft.link_type} onChange={(event) => setSceneLinkDraft({ ...sceneLinkDraft, link_type: event.target.value })}>{LINK_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}</select>
                <button disabled={busy || !sceneLinkDraft.scene_id} onClick={() => void submitSceneLink()}>Vincular</button>
              </div>
              <div className="conclave-form-grid">
                <label>Título da cena<input value={linkedSceneDraft.title} onChange={(event) => setLinkedSceneDraft({ ...linkedSceneDraft, title: event.target.value })} /></label>
                <label>Local<input value={linkedSceneDraft.location_name} onChange={(event) => setLinkedSceneDraft({ ...linkedSceneDraft, location_name: event.target.value })} /></label>
                <label>Objetivo da cena<input value={linkedSceneDraft.objective} onChange={(event) => setLinkedSceneDraft({ ...linkedSceneDraft, objective: event.target.value })} /></label>
                <label>Vínculo<select value={linkedSceneDraft.link_type} onChange={(event) => setLinkedSceneDraft({ ...linkedSceneDraft, link_type: event.target.value })}>{LINK_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
                <label className="span-2">Descrição pública<textarea value={linkedSceneDraft.public_description} onChange={(event) => setLinkedSceneDraft({ ...linkedSceneDraft, public_description: event.target.value })} /></label>
                <label className="span-2">Notas privadas<textarea value={linkedSceneDraft.private_notes} onChange={(event) => setLinkedSceneDraft({ ...linkedSceneDraft, private_notes: event.target.value })} /></label>
                <button disabled={busy || !linkedSceneDraft.title || !linkedSceneDraft.location_name} onClick={() => void submitLinkedScene()}>Criar cena vinculada</button>
              </div>
            </details>}
          </section>

          <section className="contract-subsection">
            <header><h4>Recompensas</h4></header>
            {contract.rewards.length ? contract.rewards.map((reward) => <article key={reward.id} className="reward-card">
              <header><strong>{reward.label}</strong><span>{label(reward.status)}</span></header>
              <p>{reward.description || "Sem descrição adicional."}</p>
              <small>{reward.reward_type} · {reward.quantity ?? reward.reputation_amount ?? "sem quantidade"}{reward.reputation_faction ? ` · ${reward.reputation_faction}` : ""}</small>
              {isGm && reward.item_source && <small>Fonte do item: {reward.item_source}</small>}
              {isGm && reward.status === "proposed" && <button disabled={busy} onClick={() => void run(() => approveContractReward(reward.id, newContractRequestId("reward-approve")), "Recompensa aprovada.", contract.id)}>Aprovar</button>}
              {isGm && reward.status === "approved" && ["completed", "failed", "abandoned"].includes(contract.status) && <div className="contract-inline-form">
                {reward.reward_type !== "reputation" && <select aria-label="Destinatário da recompensa" value={rewardTargets[reward.id] || ""} onChange={(event) => setRewardTargets({ ...rewardTargets, [reward.id]: event.target.value })}>
                  <option value="">Destinatário...</option>{contract.assigned_character_ids.map((id) => <option key={id} value={id}>{characterById.get(id)?.name || id}</option>)}
                </select>}
                <button disabled={busy || (reward.reward_type !== "reputation" && !(rewardTargets[reward.id] || contract.assigned_character_ids[0]))} onClick={() => void deliverReward(reward)}>Confirmar entrega</button>
              </div>}
            </article>) : <p className="sheet-empty">Recompensa ainda não revelada.</p>}
            {isGm && <details className="conclave-admin"><summary>Propor recompensa</summary><div className="conclave-form-grid">
              <label>Tipo<select value={rewardDraft.reward_type} onChange={(event) => setRewardDraft({ ...rewardDraft, reward_type: event.target.value })}>{REWARD_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
              <label>Rótulo<input value={rewardDraft.label} onChange={(event) => setRewardDraft({ ...rewardDraft, label: event.target.value })} /></label>
              <label>Quantidade<input type="number" value={rewardDraft.quantity} onChange={(event) => setRewardDraft({ ...rewardDraft, quantity: event.target.value })} /></label>
              <label>Moeda/Fonte<input value={rewardDraft.currency_type} onChange={(event) => setRewardDraft({ ...rewardDraft, currency_type: event.target.value })} /></label>
              <label>Item conhecido ou caminho<input value={rewardDraft.item_source} onChange={(event) => setRewardDraft({ ...rewardDraft, item_source: event.target.value })} /></label>
              <label>Nome do item<input value={rewardDraft.item_name} onChange={(event) => setRewardDraft({ ...rewardDraft, item_name: event.target.value })} /></label>
              <label>Facção<input value={rewardDraft.reputation_faction} onChange={(event) => setRewardDraft({ ...rewardDraft, reputation_faction: event.target.value })} /></label>
              <label>Delta reputação<input type="number" value={rewardDraft.reputation_amount} onChange={(event) => setRewardDraft({ ...rewardDraft, reputation_amount: event.target.value })} /></label>
              <label>Visibilidade<select value={rewardDraft.visibility} onChange={(event) => setRewardDraft({ ...rewardDraft, visibility: event.target.value })}><option value="table">Pública</option><option value="gm">Privada</option></select></label>
              <label className="span-2">Descrição<textarea value={rewardDraft.description} onChange={(event) => setRewardDraft({ ...rewardDraft, description: event.target.value })} /></label>
              <button disabled={busy || !rewardDraft.label} onClick={() => void submitReward()}>Propor recompensa</button>
            </div></details>}
          </section>

          <section className="contract-subsection">
            <header><h4>Reputação e histórico</h4></header>
            <div className="reputation-list">{reputation.slice(0, 6).map((entry) => <article key={entry.id} className={entry.reverted_at ? "voided" : ""}>
              <strong>{entry.faction_name}: {entry.delta > 0 ? `+${entry.delta}` : entry.delta}</strong>
              <small>Resultado {entry.resulting_value} · {time(entry.created_at)}</small>
              <p>{entry.reason}</p>
              {isGm && !entry.reverted_at && <button disabled={busy} onClick={() => void run(() => revertReputation(entry.id), "Reputação revertida.", contract.id)}>Reverter</button>}
            </article>)}</div>
            <div className="contract-event-list">{contract.events.length ? contract.events.map((event) => <article key={event.id} className={event.voided ? "voided" : ""}>
              <strong>{event.title}</strong>
              <p>{event.public_text || (isGm ? event.private_text : "")}</p>
              <small>{label(event.visibility)} · {time(event.created_at)}</small>
              {isGm && !event.voided && <button disabled={busy} onClick={() => void run(() => voidContractEvent(event.id, "Anulado pelo Mestre."), "Evento anulado.", contract.id)}>Anular</button>}
            </article>) : <p className="sheet-empty">Nenhum evento registrado.</p>}</div>
          </section>
        </>}
      </aside>
    </div>

    {activeContract && <footer className="conclave-current">
      <strong>Contrato ativo:</strong> {activeContract.title}
      <button onClick={() => void refresh(activeContract.id)}>Abrir detalhe</button>
    </footer>}
  </section>;
}
