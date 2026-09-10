import { useEffect, useMemo, useRef, useState } from "react";
import {
  completeRollRequest,
  createFreeRoll,
  createRollRequest,
  DiceRollEvent,
  DiceRollRequest,
  DiceVisibility,
  listPendingRollRequests,
  listPlayableCharacters,
  listRollHistory,
  mediaUrlFromVaultPath,
  newDiceRequestId,
  PlayableCharacterSummary,
  WorkspaceToken,
  voidDiceRoll,
} from "../api";

const COMMON_DICE = [4, 6, 8, 10, 12, 20, 100];
const ATTRIBUTES = [
  ["strength", "Força"], ["dexterity", "Destreza"], ["constitution", "Constituição"],
  ["intelligence", "Inteligência"], ["wisdom", "Sabedoria"], ["charisma", "Carisma"],
];

function signed(value: number) {
  return value > 0 ? `+${value}` : value < 0 ? String(value) : "";
}

function DiceGlyph({ sides }: { sides: number }) {
  return <span className={`dice-selector-glyph dice-selector-d${sides}`} aria-hidden="true"><i>{sides === 100 ? "%" : sides}</i></span>;
}

function RollCard({ roll, characters, mode, onVoid }: { roll: DiceRollEvent; characters: PlayableCharacterSummary[]; mode: "gm" | "player"; onVoid: (roll: DiceRollEvent) => void }) {
  const character = characters.find((item) => item.id === roll.character_id);
  const portrait = mediaUrlFromVaultPath(character?.portrait);
  return <article className={`dice-roll-card ${roll.voided ? "voided" : ""}`}>
    <header>{portrait ? <img src={portrait} alt="" /> : <span aria-hidden="true">⚄</span>}<div><strong>{roll.label}</strong><small>{character?.name || (roll.actor_role === "gm" ? "Mestre" : roll.actor_id)} · {new Date(roll.created_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</small></div><em>{roll.total}</em></header>
    <p><b>{roll.dice}:</b> {roll.individual_results.join(" + ")}{roll.modifier ? ` ${roll.modifier > 0 ? "+" : "−"} ${Math.abs(roll.modifier)}` : ""} = <strong>{roll.total}</strong></p>
    {roll.target_value != null && <p className={roll.outcome === "success" ? "roll-success" : "roll-failure"}>Dificuldade {roll.target_value} — {roll.outcome === "success" ? "Sucesso" : "Falha"}</p>}
    <footer><small>{roll.visibility === "table" ? "Mesa" : roll.visibility === "gm" ? "Somente Mestre" : roll.visibility === "owner" ? "Mestre e personagem" : "Privada"}</small>{roll.voided ? <strong>Anulada · {roll.void_reason}</strong> : mode === "gm" && <button className="secondary-button" onClick={() => onVoid(roll)}>Anular</button>}</footer>
  </article>;
}

export default function DiceTray({ mode, triggerHidden = false, targetTokens = [] }: { mode: "gm" | "player"; triggerHidden?: boolean; targetTokens?: WorkspaceToken[] }) {
  const [open, setOpen] = useState(false);
  const [requestPanelOpen, setRequestPanelOpen] = useState(false);
  const [sides, setSides] = useState(20);
  const [count, setCount] = useState(1);
  const [modifier, setModifier] = useState(0);
  const [label, setLabel] = useState("");
  const [visibility, setVisibility] = useState<DiceVisibility>("table");
  const [target, setTarget] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [syncError, setSyncError] = useState("");
  const [result, setResult] = useState<DiceRollEvent | null>(null);
  const [history, setHistory] = useState<DiceRollEvent[]>([]);
  const [pending, setPending] = useState<DiceRollRequest[]>([]);
  const [characters, setCharacters] = useState<PlayableCharacterSummary[]>([]);
  const [requestCharacter, setRequestCharacter] = useState("");
  const [requestType, setRequestType] = useState("attribute");
  const [requestSource, setRequestSource] = useState("strength");
  const [requestFormula, setRequestFormula] = useState("1d20");
  const [requestLabel, setRequestLabel] = useState("");
  const [requestTarget, setRequestTarget] = useState("");
  const [requestHideTarget, setRequestHideTarget] = useState(false);
  const [mapTargetId, setMapTargetId] = useState<string | null>(null);
  const [mapTargetOpen, setMapTargetOpen] = useState(false);
  const firstControl = useRef<HTMLButtonElement>(null);
  const requestControl = useRef<HTMLSelectElement>(null);
  const requestBusy = useRef(false);
  const refreshVersion = useRef(0);
  const pendingSubmission = useRef<{ fingerprint: string; requestId: string } | null>(null);

  async function refreshRoster() {
    const roster = await listPlayableCharacters();
    setCharacters(roster);
    setRequestCharacter((current) => current || roster.find((item) => item.access_level !== "public")?.id || "");
  }

  async function refresh() {
    const version = ++refreshVersion.current;
    try {
      const [rolls, requests] = await Promise.all([listRollHistory(20), listPendingRollRequests()]);
      if (version !== refreshVersion.current) return;
      setHistory(rolls); setPending(requests); setSyncError("");
    } catch (cause) {
      if (version === refreshVersion.current) setSyncError("Não foi possível atualizar as rolagens. Tentando reconectar…");
      throw cause;
    }
  }

  useEffect(() => {
    const show = (event: Event) => {
      const detail = (event as CustomEvent<{ panel?: string; characterId?: string }>).detail;
      const requestMode = mode === "gm" && detail?.panel === "request";
      setRequestPanelOpen(requestMode);
      if (requestMode && detail?.characterId) setRequestCharacter(detail.characterId);
      setOpen(true);
    };
    const update = () => void refresh().catch(() => undefined);
    window.addEventListener("omnisvera-open-dice-tray", show);
    window.addEventListener("omnisvera-roll-created", update);
    window.addEventListener("online", update);
    window.addEventListener("focus", update);
    const resume = () => { if (document.visibilityState === "visible") update(); };
    document.addEventListener("visibilitychange", resume);
    void refreshRoster().catch(() => undefined);
    void refresh().catch(() => undefined);
    // History must also recover when the Mesa realtime connection is unavailable.
    let polling = false;
    const timer = window.setInterval(() => {
      if (polling) return; // A slow network must not continuously supersede its own responses.
      polling = true;
      void refresh().catch(() => undefined).finally(() => { polling = false; });
    }, 3_000);
    return () => {
      ++refreshVersion.current;
      window.removeEventListener("omnisvera-open-dice-tray", show);
      window.removeEventListener("omnisvera-roll-created", update);
      window.removeEventListener("online", update); window.removeEventListener("focus", update);
      document.removeEventListener("visibilitychange", resume); window.clearInterval(timer);
    };
  }, []);

  useEffect(() => { if (open) { void refresh().catch(() => undefined); void refreshRoster().catch(() => undefined); const timer = window.setTimeout(() => (requestPanelOpen ? requestControl.current : firstControl.current)?.focus(), 50); return () => window.clearTimeout(timer); } }, [open, requestPanelOpen]);
  useEffect(() => {
    if (!open) return;
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [open]);
  useEffect(() => { if (mode === "player" && visibility === "gm") setVisibility("table"); }, [mode, visibility]);

  const formula = `${count}d${sides}${signed(modifier)}`;
  const characterMap = useMemo(() => new Map(characters.map((item) => [item.id, item])), [characters]);
  const selectedMapTarget = targetTokens.find((token) => token.id === mapTargetId);

  function chooseMapTarget(token: WorkspaceToken | null) {
    setMapTargetId(token?.id || null);
    setMapTargetOpen(false);
    if (token) setTarget(String(token.sheet?.armor_class ?? (token.character_id ? characterMap.get(token.character_id)?.armor_class ?? "" : "")));
    else setTarget("");
  }

  async function performFreeRoll() {
    if (busy) return;
    setBusy(true); setError("");
    try {
      const roll = await createFreeRoll({
        request_id: newDiceRequestId("free"), formula, label: label.trim() || "Rolagem livre", visibility,
        target_value: target ? Number(target) : undefined, hide_target: mode === "gm" && !!target,
      });
      setResult(roll); setHistory((items) => [roll, ...items.filter((item) => item.id !== roll.id)].slice(0, 20));
      window.dispatchEvent(new CustomEvent("omnisvera-roll-created", { detail: roll }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível rolar os dados."); }
    finally { setBusy(false); }
  }

  async function finishRequest(item: DiceRollRequest) {
    if (busy || requestBusy.current) return;
    requestBusy.current = true;
    setBusy(true); setError("");
    try {
      // The persisted request supplies a stable key even after reload/lost response.
      const roll = await completeRollRequest(item.id, `request:${item.id}:${item.request_id.slice(-80)}`);
      ++refreshVersion.current;
      setResult(roll);
      setPending((items) => items.filter((entry) => entry.id !== item.id));
      setHistory((items) => [roll, ...items.filter((entry) => entry.id !== roll.id)].slice(0, 20));
      window.dispatchEvent(new CustomEvent("omnisvera-roll-created", { detail: roll }));
      void refresh().catch(() => undefined);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível concluir a solicitação."); }
    finally { requestBusy.current = false; setBusy(false); }
  }

  async function requestRoll() {
    if (busy || requestBusy.current || !requestCharacter) return;
    requestBusy.current = true;
    setBusy(true); setError("");
    try {
      const payload = {
        character_id: requestCharacter, roll_type: requestType,
        source_id: requestType === "attribute" || requestType === "attack" ? requestSource : undefined,
        formula: requestType === "free" ? requestFormula : undefined, label: requestLabel || undefined,
        visibility: "owner" as const, target_value: requestTarget ? Number(requestTarget) : undefined, hide_target: requestHideTarget,
      };
      const fingerprint = JSON.stringify(payload);
      if (pendingSubmission.current?.fingerprint !== fingerprint) {
        pendingSubmission.current = { fingerprint, requestId: newDiceRequestId("ask") };
      }
      const created = await createRollRequest({ ...payload, request_id: pendingSubmission.current.requestId });
      pendingSubmission.current = null;
      ++refreshVersion.current;
      setPending((items) => [created, ...items.filter((entry) => entry.id !== created.id)]);
      setRequestLabel(""); setRequestTarget("");
      void refresh().catch(() => undefined);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível solicitar a rolagem."); }
    finally { requestBusy.current = false; setBusy(false); }
  }

  async function voidRoll(roll: DiceRollEvent) {
    const reason = window.prompt("Motivo da anulação:");
    if (!reason?.trim() || busy) return;
    setBusy(true); setError("");
    try { const updated = await voidDiceRoll(roll.id, reason); setHistory((items) => items.map((item) => item.id === updated.id ? updated : item)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível anular a rolagem."); }
    finally { setBusy(false); }
  }

  return <aside className={`dice-tray-shell ${open ? "open" : ""}`} aria-label="Bandeja global de dados">
    {!open && !triggerHidden && <button className="dice-tray-trigger" onClick={() => setOpen(true)} aria-label="Abrir bandeja de dados"><span>⚄</span><small>Dados</small>{pending.length > 0 && <b aria-label={`${pending.length} solicitações pendentes`}>{pending.length}</b>}</button>}
    {!open && triggerHidden && mode === "player" && pending.length > 0 && <button className="dice-tray-trigger" onClick={() => setOpen(true)} aria-label={`Abrir ${pending.length === 1 ? "solicitação de rolagem pendente" : `${pending.length} solicitações de rolagem pendentes`}`} aria-live="polite"><span>⚄</span><small>{pending.length === 1 ? "Rolagem pedida" : "Rolagens pedidas"}</small><b>{pending.length}</b></button>}
    {open && <div className="dice-tray-backdrop" onClick={(event) => { if (event.target === event.currentTarget) setOpen(false); }}><section className="dice-tray" role="dialog" aria-modal="true" aria-labelledby="dice-tray-title">
      <header><div><p className="eyebrow">Mesa determinística</p><h2 id="dice-tray-title">Bandeja de dados</h2></div><button aria-label="Fechar bandeja de dados" onClick={() => setOpen(false)}>×</button></header>
      {pending.length > 0 && <section className="pending-rolls"><h3>Solicitações pendentes</h3>{pending.map((item) => <article key={item.id}><div><strong>{item.label}</strong><small>{characterMap.get(item.character_id)?.name || item.character_id} · {item.formula}{item.target_value ? ` · Dificuldade ${item.target_value}` : ""}</small>{mode === "gm" && <small>Aguardando o jogador responder no próprio Companion.</small>}</div><button disabled={busy} onClick={() => void finishRequest(item)}>{mode === "gm" ? "Rolar pelo jogador" : "Confirmar e rolar"}</button></article>)}</section>}
      {mode === "gm" && <details className="roll-request-panel" open={requestPanelOpen} onToggle={(event) => setRequestPanelOpen(event.currentTarget.open)}><summary>Solicitar rolagem a um jogador</summary><div className="dice-form-grid"><label>Personagem<select ref={requestControl} value={requestCharacter} onChange={(event) => setRequestCharacter(event.target.value)}>{characters.filter((item) => item.access_level !== "public").map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Tipo<select value={requestType} onChange={(event) => { setRequestType(event.target.value); setRequestSource(event.target.value === "attack" ? "melee" : "strength"); }}><option value="attribute">Atributo</option><option value="saving_throw">Jogada de Proteção</option><option value="attack">Ataque</option><option value="free">Livre</option></select></label>{requestType === "attribute" && <label>Atributo<select value={requestSource} onChange={(event) => setRequestSource(event.target.value)}>{ATTRIBUTES.map(([key, name]) => <option key={key} value={key}>{name}</option>)}</select></label>}{requestType === "attack" && <label>Ataque<select value={requestSource} onChange={(event) => setRequestSource(event.target.value)}><option value="melee">Corpo a corpo</option><option value="ranged">À distância</option></select></label>}{requestType === "free" && <label>Fórmula<input value={requestFormula} onChange={(event) => setRequestFormula(event.target.value)} /></label>}<label>Rótulo<input value={requestLabel} onChange={(event) => setRequestLabel(event.target.value)} /></label><label>Dificuldade<input type="number" min="1" value={requestTarget} onChange={(event) => setRequestTarget(event.target.value)} /></label><label className="check-label"><input type="checkbox" checked={requestHideTarget} onChange={(event) => setRequestHideTarget(event.target.checked)} />Ocultar dificuldade</label></div><button disabled={busy || !requestCharacter} onClick={() => void requestRoll()}>Enviar solicitação</button></details>}
      <section className="free-roll-panel"><h3>Rolagem livre</h3><div className="common-dice" aria-label="Dados comuns">{COMMON_DICE.map((die) => <button ref={die === 20 ? firstControl : undefined} key={die} className={sides === die ? "active" : ""} onClick={() => setSides(die)} aria-label={`Selecionar d${die}`}><DiceGlyph sides={die} /><small>d{die}</small></button>)}</div><div className="dice-form-grid"><label>Quantidade<input type="number" min="1" max="20" value={count} onChange={(event) => setCount(Math.max(1, Math.min(20, Number(event.target.value))))} /></label><label>Modificador<input type="number" min="-1000" max="1000" value={modifier} onChange={(event) => setModifier(Math.max(-1000, Math.min(1000, Number(event.target.value))))} /></label><label className="span-2">Rótulo<input value={label} maxLength={160} placeholder="Ex.: Percepção na passagem" onChange={(event) => setLabel(event.target.value)} /></label><label>Visibilidade<select value={visibility} onChange={(event) => setVisibility(event.target.value as DiceVisibility)}><option value="table">Mesa</option><option value="private">Privada</option>{mode === "gm" && <option value="gm">Somente Mestre</option>}</select></label><div className="dice-target-picker"><span>Alvo no mapa atual</span><button type="button" onClick={() => setMapTargetOpen((open) => !open)}>{selectedMapTarget ? selectedMapTarget.name : "Selecionar alvo"}</button>{mapTargetOpen && <div className="dice-target-popover"><button type="button" onClick={() => chooseMapTarget(null)}>Sem alvo</button>{targetTokens.length ? targetTokens.map((token) => <button type="button" key={token.id} onClick={() => chooseMapTarget(token)}><strong>{token.name}</strong><small>{token.token_type === "monster" ? "Monstro / NPC" : "Personagem"} · CA {token.sheet?.armor_class ?? (token.character_id ? characterMap.get(token.character_id)?.armor_class ?? "—" : "—")}</small></button>) : <p>Nenhum alvo visível no mapa.</p>}</div>}</div><label>Dificuldade opcional<input type="number" min="1" max="100000" value={target} onChange={(event) => { setMapTargetId(null); setTarget(event.target.value); }} disabled={mode === "player" && visibility !== "private"} /></label></div><button className="primary-roll-button" disabled={busy} onClick={() => void performFreeRoll()}>{busy ? "Rolando..." : `Rolar ${formula}`}</button></section>
      {result && <section className="dice-tray-result" aria-live="assertive"><small>{result.label || "Última rolagem"}</small><strong>{result.total}</strong><span>{result.dice}: {result.individual_results.join(" + ")}{result.modifier ? ` ${signed(result.modifier)}` : ""} = {result.total}</span></section>}
      {error && <p className="warning-text" role="alert">{error}</p>}
      {syncError && <p className="warning-text" role="status">{syncError}</p>}
      <section className="roll-history"><header><h3>Rolagens recentes</h3><button className="secondary-button" onClick={() => void refresh().catch(() => undefined)}>Atualizar</button></header>{history.length ? history.map((roll) => <RollCard key={roll.id} roll={roll} characters={characters} mode={mode} onVoid={voidRoll} />) : <p className="sheet-empty">Nenhuma rolagem visível.</p>}</section>
    </section></div>}
  </aside>;
}
