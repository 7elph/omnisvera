import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  contradictNpcMemory,
  createNpc,
  createNpcMemory,
  createNpcRelationship,
  getNpc,
  importNpc,
  linkNpcContract,
  listNpcs,
  mediaUrlFromVaultPath,
  newNpcRequestId,
  NpcMemory,
  NpcRecord,
  recordNpcEncounter,
  updateNpcMemory,
  updateNpcRelationship,
  updateNpcState,
  voidNpcEvent,
} from "../api";

type Props = { mode: "gm" | "player" };
type Tab = "summary" | "relationships" | "memories" | "encounters" | "obligations" | "history" | "gm";

const MEMORY_LABELS: Record<string, string> = {
  encounter: "Encontro", fact: "Fato confirmado", rumor: "Rumor", promise: "Promessa", debt: "Dívida",
  favor: "Favor", threat: "Ameaça", betrayal: "Traição", gift: "Presente", insult: "Insulto",
  secret: "Segredo", agreement: "Acordo", conflict: "Conflito", observation: "Observação", custom: "Personalizada",
};
const CONFIDENCE_LABELS: Record<string, string> = {
  confirmed: "Confirmado", believed: "NPC acredita", suspected: "Suspeita", doubtful: "Duvidoso",
  false_known_by_npc: "Crença falsa do NPC",
};
const OBLIGATION_TYPES = new Set(["promise", "debt", "favor", "agreement"]);

function portrait(npc?: NpcRecord | null) {
  const image = mediaUrlFromVaultPath(npc?.portrait_path);
  return image ? <img src={image} alt={`Retrato de ${npc?.name || "NPC"}`} /> : <span aria-hidden="true">◉</span>;
}

function formValue(form: FormData, key: string) { return String(form.get(key) || "").trim(); }

export default function NpcDirectory({ mode }: Props) {
  const [npcs, setNpcs] = useState<NpcRecord[]>([]);
  const [selected, setSelected] = useState<NpcRecord | null>(null);
  const [tab, setTab] = useState<Tab>("summary");
  const [query, setQuery] = useState("");
  const [faction, setFaction] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function refreshList(keepId = selected?.id) {
    const rows = await listNpcs({ query, faction });
    setNpcs(rows);
    if (keepId) {
      const next = rows.find((item) => item.id === keepId);
      if (!next) setSelected(null);
    }
  }

  async function openNpc(id: number) {
    setBusy(true); setMessage("");
    try { setSelected(await getNpc(id)); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Não foi possível abrir o NPC."); }
    finally { setBusy(false); }
  }

  async function reloadNpc() {
    if (!selected) return;
    const detail = await getNpc(selected.id);
    setSelected(detail);
    await refreshList(detail.id);
  }

  useEffect(() => {
    refreshList().catch((error) => setMessage(String(error)));
    const stored = Number(localStorage.getItem("omnisvera_selected_npc"));
    if (Number.isFinite(stored) && stored > 0) openNpc(stored);
  }, []);
  useEffect(() => {
    const listener = (event: Event) => {
      const id = Number((event as CustomEvent<number>).detail);
      if (Number.isFinite(id) && id > 0) openNpc(id);
    };
    window.addEventListener("omnisvera-open-npc-directory", listener);
    return () => window.removeEventListener("omnisvera-open-npc-directory", listener);
  }, []);

  const factions = useMemo(() => [...new Set(npcs.flatMap((npc) => npc.faction_names || []))].sort(), [npcs]);
  const obligations = (selected?.memories || []).filter((memory) => OBLIGATION_TYPES.has(memory.memory_type));

  async function submitCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const formElement = event.currentTarget; const form = new FormData(formElement); setBusy(true);
    try {
      const npc = await createNpc({
        request_id: newNpcRequestId("npc-create"), name: formValue(form, "name"),
        class_or_role: formValue(form, "role") || null, current_location: formValue(form, "location") || null,
        public_description: formValue(form, "description") || null, public_status: formValue(form, "status") || null,
        visible_to_players: form.get("visible") === "on",
      });
      formElement.reset(); await refreshList(npc.id); await openNpc(npc.id); setMessage("NPC criado no estado transacional do Companion.");
    } catch (error) { setMessage(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(false); }
  }

  async function submitImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const formElement = event.currentTarget; const form = new FormData(formElement); setBusy(true);
    try {
      const npc = await importNpc({ request_id: newNpcRequestId("npc-import"), source_path: formValue(form, "source_path") });
      formElement.reset(); await refreshList(npc.id); await openNpc(npc.id); setMessage("Referência do Vault importada em modo somente leitura.");
    } catch (error) { setMessage(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(false); }
  }

  async function submitState(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return; const form = new FormData(event.currentTarget); setBusy(true);
    try {
      await updateNpcState(selected.id, selected.state_version || 1, {
        current_location: formValue(form, "location") || null,
        public_status: formValue(form, "public_status") || null,
        private_status: formValue(form, "private_status") || null,
        disposition_summary: formValue(form, "disposition") || null,
        active: form.get("active") === "on",
      });
      await reloadNpc(); setMessage("Estado do NPC atualizado e auditado.");
    } catch (error) { setMessage(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(false); }
  }

  async function submitRelationship(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return; const formElement = event.currentTarget; const form = new FormData(formElement); setBusy(true);
    try {
      await createNpcRelationship(selected.id, {
        request_id: newNpcRequestId("npc-relation"), target_type: formValue(form, "target_type"),
        target_id: formValue(form, "target_id") || null, target_label: formValue(form, "target_label"),
        public_label: formValue(form, "public_label") || null, private_label: formValue(form, "private_label") || null,
        trust_value: formValue(form, "trust") ? Number(formValue(form, "trust")) : null,
        fear_value: formValue(form, "fear") ? Number(formValue(form, "fear")) : null,
        respect_value: formValue(form, "respect") ? Number(formValue(form, "respect")) : null,
        visible_to_players: form.get("visible") === "on", reason: formValue(form, "reason"),
      });
      formElement.reset(); await reloadNpc(); setMessage("Relação assimétrica registrada.");
    } catch (error) { setMessage(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(false); }
  }

  async function submitMemory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return; const formElement = event.currentTarget; const form = new FormData(formElement); setBusy(true);
    try {
      const memoryType = formValue(form, "memory_type");
      await createNpcMemory(selected.id, {
        request_id: newNpcRequestId("npc-memory"), memory_type: memoryType, title: formValue(form, "title"),
        summary: formValue(form, "summary"), private_details: formValue(form, "private_details") || null,
        importance: formValue(form, "importance"), confidence: formValue(form, "confidence"), visibility: formValue(form, "visibility"),
        scene_id: formValue(form, "scene_id") ? Number(formValue(form, "scene_id")) : null,
        contract_id: formValue(form, "contract_id") ? Number(formValue(form, "contract_id")) : null,
        character_id: formValue(form, "character_id") || null, responsible_party: formValue(form, "responsible_party") || null,
        beneficiary: formValue(form, "beneficiary") || null, due_text: formValue(form, "due_text") || null,
        obligation_status: OBLIGATION_TYPES.has(memoryType) ? "active" : null,
      });
      formElement.reset(); await reloadNpc(); setMessage("Memória registrada sem alterar o cânone do Vault.");
    } catch (error) { setMessage(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(false); }
  }

  async function submitEncounter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return; const formElement = event.currentTarget; const form = new FormData(formElement); setBusy(true);
    try {
      await recordNpcEncounter(selected.id, {
        request_id: newNpcRequestId("npc-encounter"), scene_id: Number(formValue(form, "scene_id")), title: formValue(form, "title"),
        public_summary: formValue(form, "public_summary") || null, private_summary: formValue(form, "private_summary") || null,
        contract_id: formValue(form, "contract_id") ? Number(formValue(form, "contract_id")) : null,
      });
      formElement.reset(); await reloadNpc(); setMessage("Encontro vinculado à cena.");
    } catch (error) { setMessage(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(false); }
  }

  async function submitContractLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return; const formElement = event.currentTarget; const form = new FormData(formElement); setBusy(true);
    try {
      await linkNpcContract(selected.id, { request_id: newNpcRequestId("npc-contract"), contract_id: Number(formValue(form, "contract_id")), role: formValue(form, "role") || null, visible_to_players: form.get("visible") === "on" });
      formElement.reset(); await reloadNpc(); setMessage("NPC vinculado ao contrato.");
    } catch (error) { setMessage(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(false); }
  }

  async function setObligation(memory: NpcMemory, status: string) {
    setBusy(true);
    try {
      await updateNpcMemory(memory.id, memory.version, { obligation_status: status, status: status === "active" ? "active" : "resolved", fulfilled_at: status === "fulfilled" ? new Date().toISOString() : null }, `Obrigação marcada como ${status}`);
      await reloadNpc();
    } catch (error) { setMessage(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(false); }
  }

  async function contradict(memory: NpcMemory) {
    const summary = window.prompt("Qual informação substitui a memória anterior?");
    if (!summary) return;
    setBusy(true);
    try {
      await contradictNpcMemory(memory.id, { request_id: newNpcRequestId("npc-contradict"), title: `Correção: ${memory.title}`, summary, confidence: "confirmed", visibility: memory.visibility, reason: "Contradição registrada pelo Mestre" });
      await reloadNpc();
    } catch (error) { setMessage(error instanceof Error ? error.message : String(error)); }
    finally { setBusy(false); }
  }

  return (
    <section className="npc-page" aria-busy={busy}>
      <header className="npc-hero">
        <div><small>CONTINUIDADE DE CAMPANHA</small><h2>Diretório de NPCs</h2><p>Relações, crenças, encontros e obrigações sem escrever no Vault.</p></div>
        <div className="npc-hero-stats"><span><strong>{npcs.length}</strong><small>registrados</small></span><span><strong>{npcs.filter((npc) => npc.active !== false).length}</strong><small>ativos</small></span></div>
      </header>
      {message && <p className="npc-message" role="status">{message}</p>}
      <div className="npc-layout">
        <aside className="npc-directory">
          <div className="npc-filters">
            <input aria-label="Buscar NPC" placeholder="Buscar por nome ou função" value={query} onChange={(event) => setQuery(event.target.value)} />
            <select aria-label="Filtrar por facção" value={faction} onChange={(event) => setFaction(event.target.value)}><option value="">Todas as facções</option>{factions.map((item) => <option key={item}>{item}</option>)}</select>
            <button onClick={() => refreshList()} disabled={busy}>Buscar</button>
          </div>
          {npcs.length === 0 ? <p className="empty-state">Nenhum NPC registrado. O Mestre pode criar um perfil local ou importar uma referência do Vault.</p> : <div className="npc-card-list">{npcs.map((npc) => <button key={npc.id} className={selected?.id === npc.id ? "active" : ""} onClick={() => openNpc(npc.id)}>{portrait(npc)}<span><strong>{npc.name}</strong><small>{npc.class_or_role || npc.occupation || "Função não informada"}</small><em>{npc.current_location || "Localização não informada"}</em></span></button>)}</div>}
          {mode === "gm" && <details className="npc-admin"><summary>Criar ou importar NPC</summary><form onSubmit={submitCreate}><input name="name" required placeholder="Nome" /><input name="role" placeholder="Função" /><input name="location" placeholder="Localização" /><textarea name="description" placeholder="Descrição pública" /><input name="status" placeholder="Estado público" /><label><input name="visible" type="checkbox" /> Visível aos jogadores</label><button disabled={busy}>Criar perfil local</button></form><form onSubmit={submitImport}><input name="source_path" required placeholder="Characters/Individual/Nome.md" /><button disabled={busy}>Importar referência do Vault</button></form></details>}
        </aside>

        {!selected ? <article className="npc-empty-detail"><h3>Selecione um NPC</h3><p>O detalhe completo só é carregado quando necessário.</p></article> : <article className="npc-profile">
          <header className="npc-profile-header">{portrait(selected)}<div><small>{selected.canonical_status || "Estado canônico não informado"}</small><h2>{selected.name}</h2><p>{[selected.race, selected.class_or_role, selected.occupation].filter(Boolean).join(" · ") || "Perfil em desenvolvimento"}</p><div className="npc-tags">{(selected.faction_names || []).map((item) => <span key={item}>{item}</span>)}</div></div><span className={selected.active === false ? "inactive" : "active"}>{selected.active === false ? "Inativo" : "Ativo"}</span></header>
          <nav className="npc-tabs" aria-label="Seções do NPC">{(["summary","relationships","memories","encounters","obligations","history",...(mode === "gm" ? ["gm"] : [])] as Tab[]).map((item) => <button key={item} className={tab === item ? "active" : ""} onClick={() => setTab(item)}>{({ summary:"Resumo",relationships:"Relações",memories:"Memórias",encounters:"Encontros",obligations:"Promessas e dívidas",history:"Histórico",gm:"Mestre" } as Record<Tab,string>)[item]}</button>)}</nav>

          {tab === "summary" && <div className="npc-section"><h3>Estado atual</h3><p>{selected.public_description || "Descrição pública ainda não informada."}</p><div className="npc-summary-grid"><span><small>Local</small><strong>{selected.current_location || "Não informado"}</strong></span><span><small>Estado</small><strong>{selected.public_status || "Não informado"}</strong></span><span><small>Último encontro</small><strong>{selected.last_seen_at ? new Date(selected.last_seen_at).toLocaleDateString("pt-BR") : "Não registrado"}</strong></span></div>{mode === "gm" && selected.private_description && <div className="npc-private"><strong>Descrição privada</strong><p>{selected.private_description}</p></div>}</div>}

          {tab === "relationships" && <div className="npc-section"><h3>Relações</h3>{!selected.relationships?.length ? <p className="empty-state">Nenhuma relação registrada.</p> : <div className="npc-memory-list">{selected.relationships.map((relation) => <article key={relation.id}><header><strong>{relation.target_label}</strong><span>{relation.public_label || relation.private_label || "Sem rótulo"}</span></header><p>{relation.public_notes || (mode === "gm" ? relation.private_notes : "") || "Sem observações."}</p>{mode === "gm" && <footer>{[["Confiança",relation.trust_value],["Medo",relation.fear_value],["Respeito",relation.respect_value]].map(([label,value]) => value !== null && value !== undefined ? <span key={String(label)}>{label}: {value}</span> : null)}<button onClick={() => { const next = Number(window.prompt("Nova confiança (-100 a 100)", String(relation.trust_value ?? 0))); const reason = window.prompt("Motivo da alteração"); if (reason && Number.isFinite(next)) updateNpcRelationship(relation.id, relation.version, { trust_value: next }, reason).then(reloadNpc).catch((error) => setMessage(String(error))); }}>Alterar confiança</button></footer>}</article>)}</div>}{mode === "gm" && <form className="npc-form" onSubmit={submitRelationship}><h4>Nova relação</h4><select name="target_type"><option value="character">Personagem</option><option value="npc">Outro NPC</option><option value="faction">Facção</option><option value="group">Grupo</option></select><input name="target_id" placeholder="ID opcional" /><input name="target_label" required placeholder="Nome do alvo" /><input name="public_label" placeholder="Rótulo público" /><input name="private_label" placeholder="Rótulo privado" /><input name="trust" type="number" min="-100" max="100" placeholder="Confiança" /><input name="fear" type="number" min="-100" max="100" placeholder="Medo" /><input name="respect" type="number" min="-100" max="100" placeholder="Respeito" /><input name="reason" required placeholder="Motivo" /><label><input name="visible" type="checkbox" /> Visível aos jogadores</label><button disabled={busy}>Registrar relação</button></form>}</div>}

          {tab === "memories" && <div className="npc-section"><h3>Memórias e crenças</h3>{!selected.memories?.length ? <p className="empty-state">Nenhuma memória registrada.</p> : <div className="npc-memory-list">{selected.memories.map((memory) => <article key={memory.id} className={`memory-${memory.importance}`}><header><strong>{memory.title}</strong><span>{MEMORY_LABELS[memory.memory_type] || memory.memory_type}</span></header><p>{memory.summary}</p><footer><span>{CONFIDENCE_LABELS[memory.confidence] || memory.confidence}</span><span>{memory.status}</span>{mode === "gm" && memory.status === "active" && <button onClick={() => contradict(memory)}>Contradizer</button>}</footer>{mode === "gm" && memory.private_details && <small>{memory.private_details}</small>}</article>)}</div>}</div>}

          {tab === "encounters" && <div className="npc-section"><h3>Encontros</h3>{!selected.encounters?.length ? <p className="empty-state">Nenhum encontro registrado.</p> : <div className="npc-memory-list">{selected.encounters.map((encounter) => <article key={encounter.id}><header><strong>{encounter.title}</strong><span>Cena #{encounter.scene_id}</span></header><p>{encounter.public_summary || (mode === "gm" ? encounter.private_summary : "") || "Resumo não revelado."}</p><small>{new Date(encounter.occurred_at).toLocaleString("pt-BR")}</small></article>)}</div>}{mode === "gm" && <form className="npc-form" onSubmit={submitEncounter}><h4>Registrar encontro</h4><input name="scene_id" type="number" min="1" required placeholder="ID da cena" /><input name="contract_id" type="number" min="1" placeholder="ID do contrato" /><input name="title" required placeholder="Título do encontro" /><textarea name="public_summary" placeholder="Resumo público" /><textarea name="private_summary" placeholder="Resumo privado" /><button disabled={busy}>Registrar encontro</button></form>}</div>}

          {tab === "obligations" && <div className="npc-section"><h3>Promessas, dívidas e favores</h3>{obligations.length === 0 ? <p className="empty-state">Nenhuma obrigação registrada.</p> : <div className="npc-memory-list">{obligations.map((memory) => <article key={memory.id}><header><strong>{memory.title}</strong><span>{memory.obligation_status || "active"}</span></header><p>{memory.summary}</p><small>{[memory.responsible_party && `Responsável: ${memory.responsible_party}`, memory.beneficiary && `Beneficiário: ${memory.beneficiary}`, memory.due_text].filter(Boolean).join(" · ")}</small>{mode === "gm" && memory.obligation_status === "active" && <footer><button onClick={() => setObligation(memory,"fulfilled")}>Cumprida</button><button onClick={() => setObligation(memory,"broken")}>Quebrada</button><button onClick={() => setObligation(memory,"forgiven")}>Perdoada</button></footer>}</article>)}</div>}</div>}

          {tab === "history" && <div className="npc-section"><h3>Histórico auditável</h3>{!selected.events?.length ? <p className="empty-state">Nenhum evento registrado.</p> : <div className="npc-event-list">{selected.events.map((event) => <article key={event.id} className={event.voided ? "voided" : ""}><strong>{event.title}</strong><p>{event.public_text || (mode === "gm" ? event.private_text : "") || event.event_type}</p><small>{new Date(event.created_at).toLocaleString("pt-BR")}</small>{mode === "gm" && !event.voided && <button onClick={() => { const reason = window.prompt("Motivo da anulação"); if (reason) voidNpcEvent(event.id,reason).then(reloadNpc).catch((error) => setMessage(String(error))); }}>Anular evento</button>}</article>)}</div>}</div>}

          {tab === "gm" && mode === "gm" && <div className="npc-section"><h3>Controles do Mestre</h3><form className="npc-form" onSubmit={submitState}><input name="location" defaultValue={selected.current_location || ""} placeholder="Localização atual" /><input name="public_status" defaultValue={selected.public_status || ""} placeholder="Estado público" /><textarea name="private_status" defaultValue={selected.private_status || ""} placeholder="Estado privado" /><textarea name="disposition" defaultValue={selected.disposition_summary || ""} placeholder="Disposição atual" /><label><input name="active" type="checkbox" defaultChecked={selected.active !== false} /> NPC ativo</label><button disabled={busy}>Salvar estado</button></form><form className="npc-form" onSubmit={submitMemory}><h4>Registrar memória</h4><select name="memory_type">{Object.entries(MEMORY_LABELS).map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select><input name="title" required placeholder="Título" /><textarea name="summary" required placeholder="O que o NPC sabe ou acredita" /><textarea name="private_details" placeholder="Detalhes exclusivos do Mestre" /><select name="confidence"><option value="confirmed">Confirmado</option><option value="believed">NPC acredita</option><option value="suspected">Suspeita</option><option value="doubtful">Duvidoso</option><option value="false_known_by_npc">Crença falsa</option></select><select name="importance"><option value="low">Baixa</option><option value="medium">Média</option><option value="high">Alta</option><option value="critical">Crítica</option></select><select name="visibility"><option value="gm">Somente Mestre</option><option value="table">Revelada à mesa</option></select><input name="character_id" placeholder="Personagem relacionado" /><input name="scene_id" type="number" min="1" placeholder="Cena" /><input name="contract_id" type="number" min="1" placeholder="Contrato" /><input name="responsible_party" placeholder="Responsável (promessa/dívida)" /><input name="beneficiary" placeholder="Beneficiário" /><input name="due_text" placeholder="Prazo ou condição" /><button disabled={busy}>Registrar memória</button></form><form className="npc-form" onSubmit={submitContractLink}><h4>Vincular contrato</h4><input name="contract_id" type="number" min="1" required placeholder="ID do contrato" /><input name="role" placeholder="Papel do NPC" /><label><input name="visible" type="checkbox" /> Vínculo visível</label><button disabled={busy}>Vincular</button></form></div>}
        </article>}
      </div>
    </section>
  );
}
