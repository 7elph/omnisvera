import { useEffect, useRef, useState } from "react";
import { CombatEffectsState, CombatTestView, getCombatEffects, getCombatTestViews, newDiceRequestId, PlayableCharacterSummary, sendCombatEffectCommand, WorkspaceToken } from "../api";
import CombatEffectsPanel from "./CombatEffectsPanel";

type Props = { mode: "gm" | "player"; tableMode?: "digital" | "physical" | "test"; mapId: string; characters: PlayableCharacterSummary[]; tokens: WorkspaceToken[]; onChange: () => Promise<void>; onPins?: () => void; onFollowMap?: (mapId: string) => void };
export default function CombatEncounterPanel({ mode, tableMode, mapId, characters, tokens, onChange, onPins, onFollowMap }: Props) {
  const [state, setState] = useState<CombatEffectsState>({ round: 1, version: 0, effects: [] });
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [title, setTitle] = useState("Combate");
  const [error, setError] = useState("");
  const [testViews, setTestViews] = useState<CombatTestView[]>([]);
  const [testError, setTestError] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const retry = useRef<{ key: string; id: string } | null>(null);
  const initialized = useRef(false);
  const encounterMapId = state.encounter?.map_id;
  const ownerId = characters.find(character => character.access_level === "owner")?.id;
  const participants = [...characters.map(c => ({ key: `character|${c.id}`, name: c.name })), ...tokens.filter(t => t.token_type === "monster").map(t => ({ key: `token|${t.id}`, name: t.name }))];
  useEffect(() => { let alive = true; const load = () => getCombatEffects().then(s => { if (alive && !lock.current) setState(s); }).catch(e => { if (alive) setError(String(e)); }); void load(); const changed = () => void load(); window.addEventListener("omnisvera-session-changed", changed); const timer = window.setInterval(() => void load(), 3000); return () => { alive = false; window.removeEventListener("omnisvera-session-changed", changed); clearInterval(timer); }; }, []);
  useEffect(() => {
    if (mode !== "gm" || tableMode !== "test") { setTestViews([]); setTestError(""); return; }
    let alive = true;
    const load = () => getCombatTestViews().then(result => { if (alive) { setTestViews(result.views); setTestError(""); } }).catch(e => { if (alive) setTestError(e instanceof Error ? e.message : "Falha ao carregar as prévias"); });
    void load();
    const changed = () => void load();
    window.addEventListener("omnisvera-session-changed", changed);
    const timer = window.setInterval(() => void load(), 3000);
    return () => { alive = false; window.removeEventListener("omnisvera-session-changed", changed); clearInterval(timer); };
  }, [mode, tableMode]);
  useEffect(() => {
    if (!state.encounter?.active) { initialized.current = false; return; }
    if (initialized.current) return;
    initialized.current = true;
    setTitle(state.encounter.title || "Combate");
    setDrafts(Object.fromEntries((state.encounter.participants || []).map(p => [`${p.target_type}|${p.target_id}`, String(p.initiative)])));
  }, [state.encounter]);
  async function save(action: "start" | "initiative" | "end") {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError("");
    const entries = participants.filter(p => drafts[p.key]?.trim()).map(p => { const [target_type, target_id] = p.key.split("|"); return { target_type, target_id, initiative: Number(drafts[p.key]) }; });
    const payload = { title, map_id: mapId, participants: entries };
    const key = JSON.stringify([action, state.version, payload]);
    if (retry.current?.key !== key) retry.current = { key, id: newDiceRequestId("encounter") };
    try { setState(await sendCombatEffectCommand({ request_id: retry.current.id, expected_version: state.version, action, payload })); retry.current = null; await onChange(); if (mode === "gm" && tableMode === "test") setTestViews((await getCombatTestViews()).views); }
    catch (e) { setError(e instanceof Error ? e.message : "Falha ao preparar combate"); }
    finally { lock.current = false; setBusy(false); }
  }
  if (mode === "player" && !state.encounter?.active) return null;
  return <section className={mode === "player" ? "workspace-combat-live" : "workspace-gm-tools"} role={mode === "player" ? "status" : undefined} aria-live={mode === "player" ? "polite" : undefined}>
    <header>{mode === "player" && <span>COMBATE EM ANDAMENTO</span>}<strong>{state.encounter?.active ? state.encounter.title : "Preparar combate"}</strong><small>Rodada {state.round}</small></header>
    {mode === "player" && state.encounter?.active && encounterMapId && encounterMapId !== mapId && <button onClick={() => onFollowMap?.(encounterMapId)}>Ir ao mapa do combate</button>}
    {state.encounter?.active && <ol>{state.encounter.participants?.map(p => <li className={p.target_type === "character" && p.target_id === ownerId ? "current" : ""} key={`${p.target_type}|${p.target_id}`}><b>{p.initiative}</b><span>{p.name}</span>{p.target_type === "character" && p.target_id === ownerId && <small>Você</small>}</li>)}</ol>}
    {mode === "player" && <p>Use seus ataques e habilidades normalmente na ficha. A ordem e a rodada são atualizadas pelo Mestre.</p>}
    {mode === "gm" && <>
      <details className="workspace-gm-subsection" open={!state.encounter?.active}><summary>1 · Participantes e iniciativa</summary>
        <input aria-label="Nome do combate" value={title} onChange={e => setTitle(e.target.value)} maxLength={120} />
        <p>Preencha a iniciativa de quem participa; deixe vazio quem fica fora. Maior valor primeiro, empate segue a ordem desta lista.</p>
        <div className="workspace-gm-numbers">{participants.map(p => <label key={p.key}>{p.name}<input aria-label={`Iniciativa de ${p.name}`} type="number" min={-99} max={999} placeholder="Fora" value={drafts[p.key] ?? ""} onChange={e => setDrafts({ ...drafts, [p.key]: e.target.value })} /></label>)}</div>
        <button disabled={busy} onClick={() => void save(state.encounter?.active ? "initiative" : "start")}>{state.encounter?.active ? "Salvar ordem de iniciativa" : "Iniciar combate neste mapa"}</button>
      </details>
      {tableMode === "test" && <section className="workspace-combat-test-simulator">
        <header><div><small>SIMULAÇÃO SOLO</small><strong>Visão dos jogadores</strong></div><span>{testViews.filter(view => view.receives_combat).length}/{testViews.length} recebem</span></header>
        <p>Estas prévias usam o mesmo filtro dos acessos reais. Ações feitas aqui continuam alterando a sessão.</p>
        <div>{testViews.length ? testViews.map(view => {
          const encounter = view.state.encounter;
          return <article className={view.receives_combat ? "receives" : "excluded"} key={view.profile_id}>
            <header><strong>{view.character_name}</strong><span>{view.receives_combat ? "Recebeu" : "Fora do combate"}</span></header>
            {view.receives_combat ? <>
              <div className="workspace-combat-test-meta"><b>{encounter?.title || "Combate"}</b><small>Rodada {view.state.round}</small></div>
              <ol>{encounter?.participants?.map(participant => {
                const current = participant.target_type === "character" && participant.target_id === view.profile_id;
                return <li className={current ? "current" : ""} key={`${view.profile_id}|${participant.target_type}|${participant.target_id}`}><b>{participant.initiative}</b><span>{participant.name}</span>{current && <small>Você</small>}</li>;
              })}</ol>
              <small>{view.state.effects.length} efeito(s) visível(is)</small>
            </> : <p>Nenhum card aparece para este jogador.</p>}
          </article>;
        }) : <p>Carregando prévias dos jogadores…</p>}</div>
        {testError && <p role="alert">{testError}</p>}
      </section>}
      <button onClick={onPins}>2 · Posicionar / editar criaturas e pins</button>
      <p>3 · Jogadores narram e atacam nas próprias fichas. Confira o cálculo antes de aplicar dano. Espólios e distribuição ficam em Itens e loot.</p>
      {state.encounter?.active && <button disabled={busy} onClick={() => void save("end")}>Encerrar combate</button>}
    </>}
    <CombatEffectsPanel mode={mode} characters={characters} tokens={tokens} onChange={async () => { setState(await getCombatEffects()); await onChange(); }} />
    {error && <p role="alert">{error}</p>}
  </section>;
}
