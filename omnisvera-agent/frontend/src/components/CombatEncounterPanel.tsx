import { useEffect, useRef, useState } from "react";
import type { SessionLedgerEntry } from '../api';
import ActiveEffectIcons from './ActiveEffectIcons';
import { CombatEffectsState, CombatTestView, getCombatEffects, getCombatTestViews, HttpError, newDiceRequestId, PlayableCharacterSummary, sendCombatEffectCommand, WorkspaceToken } from "../api";
import CombatEffectsPanel from "./CombatEffectsPanel";
import MonsterAttackPanel from "./MonsterAttackPanel";
import SummonControls from "./SummonControls";
import { listWorkspaceMaps, WorkspaceMap, updateWorkspaceToken } from '../api';

type Props = { ledger?: SessionLedgerEntry[]; confirmedState?: CombatEffectsState; mode: "gm" | "player"; tableMode?: "digital" | "physical" | "test"; mapId: string; characters: PlayableCharacterSummary[]; tokens: WorkspaceToken[]; onChange: () => Promise<void>; onPins?: () => void; onFollowMap?: (mapId: string) => void; gridded?: boolean; compact?: boolean };
export default function CombatEncounterPanel({ ledger = [], confirmedState, mode, tableMode, mapId, characters, tokens, onChange, onPins, onFollowMap, gridded = false, compact = false }: Props) {
  const [state, setState] = useState<CombatEffectsState>(confirmedState || { round: 1, version: 0, effects: [] });
  useEffect(() => {
    if (!confirmedState) return;
    setState(current => confirmedState.version >= current.version ? confirmedState : current);
  }, [confirmedState]);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [title, setTitle] = useState("Combate");
  const [maps, setMaps] = useState<WorkspaceMap[]>([]);
  const [arena, setArena] = useState('');
  useEffect(() => { if (mode === 'gm') void listWorkspaceMaps().then(setMaps).catch(() => {}); }, [mode, mapId]);
  const [error, setError] = useState("");
  const [syncError, setSyncError] = useState("");
  const [testViews, setTestViews] = useState<CombatTestView[]>([]);
  const [testError, setTestError] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const retry = useRef<{ key: string; id: string } | null>(null);
  const initialized = useRef(false);
  const encounterMapId = state.encounter?.map_id;
  const ownerId = characters.find(character => character.access_level === "owner")?.id;
  const current = state.encounter?.participants?.[state.encounter.turn_index ?? 0];
  const members = state.encounter?.participants || [];
  const battleCharacters = state.encounter?.battle_mode ? characters.filter(c => members.some(p => p.target_type === 'character' && p.target_id === c.id)) : characters;
  const battleTokens = state.encounter?.battle_mode ? tokens.filter(t => members.some(p => (p.target_type === 'token' && p.target_id === t.id) || (p.target_type === 'character' && p.target_id === t.character_id))) : tokens;
  const currentToken = tokens.find(token => token.id === current?.target_id);
  const controlledSummons = tokens.filter(token => token.sheet?.summon && members.some(member => member.target_type === 'token' && member.target_id === token.id) && (mode === 'gm' || token.sheet.summon.caster === ownerId));
  const myTurn = (current?.target_type === "character" && current.target_id === ownerId) || Boolean(ownerId && currentToken?.sheet?.summon?.caster === ownerId);
  const masterTurn = mode === "gm" && current?.target_type === "token";
  const participants = [...characters.map(c => ({ key: `character|${c.id}`, name: c.name })), ...tokens.filter(t => t.token_type === "monster").map(t => ({ key: `token|${t.id}`, name: t.name }))];
  useEffect(() => {
    let alive = true, pending = false;
    const load = async () => {
      if (!alive || pending) return;
      pending = true;
      try {
        const snapshot = await getCombatEffects();
        if (alive && !lock.current) {
          setState(current => snapshot.version >= current.version ? snapshot : current);
          setSyncError("");
        }
      } catch (e) { if (alive) setSyncError(e instanceof Error ? e.message : "Falha ao sincronizar combate"); }
      finally { pending = false; }
    };
    void load();
    window.addEventListener("omnisvera-session-changed", load);
    window.addEventListener("online", load);
    const resume = () => { if (document.visibilityState === 'visible') void load(); };
    document.addEventListener("visibilitychange", resume);
    const timer = window.setInterval(() => void load(), 3000);
    return () => { alive = false; clearInterval(timer); window.removeEventListener("omnisvera-session-changed", load); window.removeEventListener("online", load); document.removeEventListener("visibilitychange", resume); };
  }, []);
  useEffect(() => {
    if (mode !== "gm" || tableMode !== "test") { setTestViews([]); setTestError(""); return; }
    let alive = true;
    let pending = false;
    const load = async () => {
      if (!alive || pending) return;
      pending = true;
      try { const result = await getCombatTestViews(); if (alive) { setTestViews(result.views); setTestError(""); } }
      catch (e) { if (alive) setTestError(e instanceof Error ? e.message : "Falha ao carregar as prévias"); }
      finally { pending = false; }
    };
    void load();
    const changed = () => void load();
    window.addEventListener("omnisvera-session-changed", changed);
    const timer = window.setInterval(() => void load(), 3000);
    return () => { alive = false; window.removeEventListener("omnisvera-session-changed", changed); clearInterval(timer); };
  }, [mode, tableMode]);
  const orderCount = participants.length;
  const positionLabel = (position: number) => `${position}º`;
  useEffect(() => {
    if (!state.encounter?.active) { initialized.current = false; return; }
    if (initialized.current) return;
    initialized.current = true;
    setTitle(state.encounter.title || "Combate");
    // Converte iniciativas existentes em posições de ordem (maior primeiro).
    const ranked = [...(state.encounter.participants || [])].map((p, index) => ({ p, index }))
      .sort((a, b) => b.p.initiative - a.p.initiative || a.index - b.index);
    setDrafts(Object.fromEntries(ranked.map((entry, rank) => [`${entry.p.target_type}|${entry.p.target_id}`, String(rank + 1)])));
  }, [state.encounter]);
  useEffect(() => {
    if (!state.encounter?.active) return;
    setDrafts(previous => {
      const next = { ...previous };
      const members = state.encounter?.participants || [];
      for (const member of members) {
        const key = `${member.target_type}|${member.target_id}`;
        // Novato no combate entra depois de quem tem iniciativa maior.
        if (!(key in next)) next[key] = String(members.filter(other => other.initiative > member.initiative).length + 1);
      }
      return next;
    });
  }, [state.encounter?.participants]);
  async function save(action: "start" | "initiative" | "end" | "next_turn") {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError("");
    // Posição 1º = maior iniciativa; Fora (vazio) fica de fora do combate.
    const entries = participants.filter(p => drafts[p.key]?.trim()).map(p => { const [target_type, target_id] = p.key.split("|"); return { target_type, target_id, initiative: orderCount - Number(drafts[p.key]) + 1 }; });
    const payload = { title, map_id: action === 'start' ? arena || mapId : encounterMapId || mapId, participants: entries, battle_mode: true };
    const key = JSON.stringify([action, state.version, payload]);
    if (retry.current?.key !== key) retry.current = { key, id: newDiceRequestId("encounter") };
    let applied = false;
    try { setState(await sendCombatEffectCommand({ request_id: retry.current.id, expected_version: state.version, action, payload })); applied = true; retry.current = null; await onChange(); if (mode === "gm" && tableMode === "test") setTestViews((await getCombatTestViews()).views); }
    catch (e) {
      if (applied) setError("Ação aplicada. A atualização da tela falhou; a sincronização tentará novamente. Não repita a ação.");
      else if (e instanceof HttpError && e.status === 409) {
        setError("O combate mudou em outro acesso. Atualizando; confira o turno antes de tentar novamente.");
        try { const snapshot = await getCombatEffects(); setState(current => snapshot.version >= current.version ? snapshot : current); } catch { /* Retain confirmed state and let polling recover. */ }
      } else setError(e instanceof Error ? e.message : "Falha ao preparar combate");
    }
    finally { lock.current = false; setBusy(false); }
  }
  if ((mode === "player" || compact) && !state.encounter?.active) return null;
  return <section data-combat-version={state.version} className={mode === "player" || compact ? "workspace-combat-live" : "workspace-gm-tools"} role={mode === "player" || compact ? "status" : undefined} aria-live={mode === "player" || compact ? "polite" : undefined}>
    <header>{(mode === "player" || compact) && <span>COMBATE EM ANDAMENTO</span>}<strong>{state.encounter?.active ? state.encounter.title : "Preparar combate"}</strong><small>Rodada {state.round}</small></header>
    <details className="workspace-combat-content" open={mode==='gm'&&!compact?true:undefined}>
    <summary>{state.encounter?.active?`Turno: ${current?.name||'participante'} · controles`:'Controles de combate'}</summary>
    {state.encounter?.active && <div role="status" aria-live="polite" style={{ padding: "12px", border: "2px solid currentColor", borderRadius: "8px", marginBlock: "12px" }}>
      <strong>{myTurn ? "É o seu turno!" : masterTurn ? `Mestre, é sua vez: ${current?.name}` : `Turno: ${current?.name || "participante oculto"}`}</strong>
      {(mode === "gm" || myTurn) && current?.target_type === "token" && !currentToken?.sheet?.summon && tokens.filter(t => t.id === current.target_id).map(token => <MonsterAttackPanel key={`${token.id}:${state.encounter?.turn_sequence}`} token={token} combat={mode === 'gm' ? state : undefined} characters={battleCharacters} targets={battleTokens} physical={tableMode === "physical"} done={state.encounter?.action_committed} gridded={gridded} onChange={async () => {
        const snapshot = await getCombatEffects();
        setState(current => snapshot.version >= current.version ? snapshot : current);
        await onChange();
      }} />)}
      {state.encounter?.attack_limit != null && <p>Ataques restantes: {Math.max(0, state.encounter.attack_limit - (state.encounter.attacks_used || 0))}</p>}
      {(mode === "gm" || myTurn) && !currentToken?.sheet?.summon && <button disabled={busy} onClick={() => void save("next_turn")}>Concluir e passar turno →</button>}
    </div>}
    {mode === "player" && state.encounter?.active && encounterMapId && encounterMapId !== mapId && <button onClick={() => onFollowMap?.(encounterMapId)}>Ir ao mapa do combate</button>}
{state.encounter?.active && <ol>{state.encounter.participants?.map((p, index) => <li aria-current={index === (state.encounter?.turn_index ?? 0) ? "step" : undefined} className={index === (state.encounter?.turn_index ?? 0) ? "current" : ""} key={`${p.target_type}|${p.target_id}`}><b>{p.initiative}</b><span>{p.name}<ActiveEffectIcons state={state} targetId={p.target_id} targetType={p.target_type} /></span>{p.target_type === "character" && p.target_id === ownerId && <small>Você</small>}</li>)}</ol>}
    {state.encounter?.active && controlledSummons.map(token => <SummonControls key={token.id} token={token} mode={mode} characters={characters} tokens={tokens} state={state} physical={tableMode === 'physical'} onChange={async () => {
      const snapshot = await getCombatEffects();
      setState(current => snapshot.version >= current.version ? snapshot : current);
      await onChange();
    }} />)}
    {mode === "player" && <p>Escolha o alvo, role o ataque e confirme o resultado para aplicar o dano. Depois conclua seu turno.</p>}
    {mode === "gm" && !compact && <>
      <details className="workspace-gm-subsection" open={!state.encounter?.active}><summary>1 · Participantes e iniciativa</summary>
        {!state.encounter?.active && <label>Mapa de combate<select value={arena || mapId} onChange={e => setArena(e.target.value)}>{maps.filter(map => map.visible_to_players).map(map => <option key={map.id} value={map.id}>{map.title}</option>)}</select><small>Os participantes selecionados ficarão visíveis neste mapa. Ao encerrar, retornam às posições anteriores.</small></label>}
        <input aria-label="Nome do combate" value={title} onChange={e => setTitle(e.target.value)} maxLength={120} />
        <p>Escolha a ordem de entrada: 1º primeiro, 2º segundo e assim por diante. Fora deixa de fora do combate.</p>
        <div className="workspace-gm-numbers">{participants.map(p => <label key={p.key}>{p.name}<select aria-label={`Ordem de ${p.name}`} value={drafts[p.key] ?? ""} onChange={e => setDrafts({ ...drafts, [p.key]: e.target.value })}><option value="">Fora</option>{Array.from({ length: orderCount }, (_, index) => <option key={index + 1} value={String(index + 1)}>{positionLabel(index + 1)}</option>)}</select></label>)}</div>
        <button disabled={busy} onClick={() => void save(state.encounter?.active ? "initiative" : "start")}>{state.encounter?.active ? "Salvar ordem de iniciativa" : "Iniciar combate neste mapa"}</button>
      </details>
      {tableMode === "test" && <section className="workspace-combat-test-simulator">
        <header><div><small>SIMULAÇÃO SOLO</small><strong>Visão dos jogadores</strong></div><span>{testViews.filter(view => view.receives_combat).length}/{testViews.length} recebem</span></header>
        <p>Estas prévias usam o mesmo filtro dos acessos reais. Ações feitas aqui continuam alterando a sessão.</p>
        {!state.encounter?.active && <p role="status">Sem combate ativo — inicie acima para ver a prévia de cada jogador.</p>}
        <div>{state.encounter?.active && testViews.length ? testViews.map(view => {
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
        }) : (state.encounter?.active ? <p>Carregando prévias dos jogadores…</p> : null)}</div>
        {testError && <p role="alert">{testError}</p>}
      </section>}
      <button onClick={onPins}>2 · Posicionar / editar criaturas e pins</button>
      {tokens.some(token => token.token_type === 'monster' && token.current_hp === 0 && !token.sheet?.summon) && <details><summary>Cadáveres e reanimação</summary>
        {tokens.filter(token => token.token_type === 'monster' && token.current_hp === 0 && !token.sheet?.summon && !token.sheet?.reanimated_by).map(token => <div key={token.id}>
          <strong>{token.name}</strong><button disabled={busy || Boolean(token.sheet?.reanimation_allowed)} onClick={async () => {
            setBusy(true); setError('');
            try { await updateWorkspaceToken(token.id, { sheet: { ...token.sheet, reanimation_allowed: true } }); await onChange(); }
            catch (reason) { setError(reason instanceof Error ? reason.message : 'Falha ao autorizar reanimação'); }
            finally { setBusy(false); }
          }}>{token.sheet?.reanimation_allowed ? 'Reanimação autorizada' : 'Autorizar reanimação'}</button>
        </div>)}
      </details>}
      <p>3 · Jogadores narram e atacam nas próprias fichas. Confira o cálculo antes de aplicar dano. Espólios e distribuição ficam em Itens e loot.</p>
      {state.encounter?.active && <button disabled={busy} onClick={() => void save("end")}>Encerrar combate</button>}
    </>}
    {!compact && <CombatEffectsPanel mode={mode} characters={characters} tokens={tokens} onChange={async () => {
      const snapshot = await getCombatEffects();
      setState(current => snapshot.version >= current.version ? snapshot : current);
      await onChange();
    }} />}
    </details>
    {error && <p role="alert">{error}</p>}
    {syncError && <p role="status">{syncError} Mantendo o último turno confirmado.</p>}
  </section>;
}
