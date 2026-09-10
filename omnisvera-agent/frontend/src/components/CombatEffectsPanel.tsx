import { FormEvent, useEffect, useRef, useState } from "react";
import { CombatEffect, CombatEffectsState, getCombatEffects, sendCombatEffectCommand, newDiceRequestId, PlayableCharacterSummary, WorkspaceToken, updateCharacterDefinition, getPlayableCharacter } from "../api";

type Props = { mode: "gm" | "player"; characters: PlayableCharacterSummary[]; tokens: WorkspaceToken[]; onChange: () => Promise<void> };
const modifiers = { attack_bonus: 0, damage_bonus: 0, armor_class_bonus: 0, extra_attacks: 0, hp_per_round: 0 };
const labels = { attack_bonus: "Ataque", damage_bonus: "Dano", armor_class_bonus: "CA", extra_attacks: "Ataques adicionais", hp_per_round: "PV por rodada (+ cura / − dano)" };
const blank = { id: "", label: "", source: "", duration: "rounds", rounds: 1, modifiers };

export default function CombatEffectsPanel({ mode, characters, tokens, onChange }: Props) {
  const [state, setState] = useState<CombatEffectsState>({ round: 1, version: 0, effects: [] });
  const [target, setTarget] = useState("");
  const [draft, setDraft] = useState(blank);
  const [count, setCount] = useState(1);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const retry = useRef<{ key: string; id: string } | null>(null);
  useEffect(() => {
    let alive = true;
    const load = () => getCombatEffects().then(s => { if (alive && !lock.current) setState(s); }).catch(e => { if (alive) setError(String(e)); });
    void load(); const changed = () => void load(); window.addEventListener("omnisvera-session-changed", changed); const timer = window.setInterval(() => void load(), 3000);
    return () => { alive = false; window.removeEventListener("omnisvera-session-changed", changed); window.clearInterval(timer); };
  }, []);
  const targets = [...characters.map(c => ({ key: `character|${c.id}`, name: c.name })), ...tokens.filter(t => t.token_type === "monster").map(t => ({ key: `token|${t.id}`, name: t.name }))];
  const [targetType, targetId] = target.split("|");
  useEffect(() => {
    let alive = true;
    if (mode === "gm" && targetType === "character") void getPlayableCharacter(targetId).then(c => { if (alive) setCount(c.definition.attacks?.[0]?.base_attack_count || 1); }).catch(e => setError(String(e)));
    return () => { alive = false; };
  }, [target, mode]);
  async function command(action: string, payload: Record<string, unknown>) {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError("");
    const key = JSON.stringify([action, payload, state.version]);
    if (retry.current?.key !== key) retry.current = { key, id: newDiceRequestId("effects") };
    try {
      const next = await sendCombatEffectCommand({ request_id: retry.current.id, expected_version: state.version, action, payload });
      setState(next); retry.current = null; setDraft(blank); await onChange();
    } catch (e) { setError(e instanceof Error ? e.message : "Falha ao atualizar efeitos"); }
    finally { lock.current = false; setBusy(false); }
  }
  function edit(effect: CombatEffect) {
    setTarget(`${effect.target_type}|${effect.target_id}`);
    setDraft({ id: effect.id, label: effect.label, source: effect.source, duration: effect.duration, rounds: effect.rounds || 1, modifiers: { ...modifiers, ...effect.modifiers } });
  }
  function apply(event: FormEvent) {
    event.preventDefault();
    void command("apply", { ...draft, id: draft.id || undefined, target_type: targetType, target_id: targetId });
  }
  if (mode === "player" && !state.effects.length) return null;
  return <details className="workspace-monster-catalog"><summary>{mode === "gm" ? "EFEITOS E MULTIATAQUE" : "EFEITOS SOBRE VOCÊ"} · Rodada {state.round}</summary>
    {state.effects.map(e => <article key={e.id}><strong>{targets.find(t => t.key === `${e.target_type}|${e.target_id}`)?.name || e.target_id}: {e.label}</strong><p>{e.source} · {e.duration === "rounds" ? `${e.rounds} rodada(s)` : ({ scene: "até encerrar cena", rest: "até descanso", manual: "até remover", next_attack: "próxima ação de ataque" } as Record<string, string>)[e.duration]}</p><small>{Object.entries(e.modifiers).filter(([, v]) => v).map(([k, v]) => `${labels[k as keyof typeof labels]} ${v > 0 ? "+" : ""}${v}`).join(" · ") || "Condição narrativa, sem modificador numérico"}</small>{mode === "gm" && <div><button disabled={busy} onClick={() => edit(e)}>Editar</button><button disabled={busy} onClick={() => void command("remove", { id: e.id })}>Remover</button></div>}</article>)}
    {mode === "gm" && <>
      <div className="workspace-monster-hp"><button disabled={busy} onClick={() => { if (window.confirm("Encerrar esta rodada? Aplica PV por rodada e reduz durações uma vez.")) void command("round", {}); }}>Encerrar rodada {state.round}</button><button disabled={busy} onClick={() => { if (window.confirm("Encerrar efeitos com duração de cena?")) void command("scene", {}); }}>Encerrar efeitos de cena</button></div>
      <select aria-label="Alvo do efeito" value={target} onChange={e => { setTarget(e.target.value); setDraft(blank); }}><option value="">Selecionar personagem ou criatura…</option>{targets.map(t => <option key={t.key} value={t.key}>{t.name}</option>)}</select>
      {targetType === "character" && <div className="workspace-monster-hp"><label>Ataques base por ação<input aria-label="Ataques base por ação" type="number" min={1} max={10} value={count} onChange={e => setCount(Number(e.target.value))} /></label><button disabled={busy} onClick={async () => { if (lock.current) return; lock.current = true; setBusy(true); try { await updateCharacterDefinition(targetId, { attack_count: count }, "Quantidade de ataques autorizada pelo mestre"); await onChange(); } catch (e) { setError(String(e)); } finally { lock.current = false; setBusy(false); } }}>Salvar quantidade</button></div>}
      <form className="workspace-monster-form" onSubmit={apply}>
        <input aria-label="Nome do efeito" placeholder="Efeito ou condição" value={draft.label} onChange={e => setDraft({ ...draft, label: e.target.value })} required maxLength={120} />
        <input aria-label="Origem do efeito" placeholder="Origem: habilidade, item ou decisão do mestre" value={draft.source} onChange={e => setDraft({ ...draft, source: e.target.value })} required maxLength={240} />
        <select aria-label="Duração do efeito" value={draft.duration} onChange={e => setDraft({ ...draft, duration: e.target.value })}><option value="rounds">Rodadas</option><option value="next_attack">Próxima ação de ataque</option><option value="scene">Até encerrar cena</option><option value="rest">Até descanso</option><option value="manual">Até remover</option></select>
        {draft.duration === "rounds" && <input aria-label="Rodadas restantes" type="number" min={1} max={999} value={draft.rounds} onChange={e => setDraft({ ...draft, rounds: Number(e.target.value) })} />}
        <div className="workspace-monster-sheet-grid">{Object.keys(modifiers).map(key => <label key={key}>{labels[key as keyof typeof labels]}<input aria-label={labels[key as keyof typeof labels]} type="number" min={key === "extra_attacks" ? 0 : -999} max={key === "extra_attacks" ? 9 : 999} value={draft.modifiers[key as keyof typeof modifiers]} onChange={e => setDraft({ ...draft, modifiers: { ...draft.modifiers, [key]: Number(e.target.value) } })} /></label>)}</div>
        <button disabled={busy || !target}>{draft.id ? "Salvar efeito" : "Aplicar efeito"}</button>
      </form>
      <button disabled={busy || !target} onClick={() => { if (window.confirm("Encerrar os efeitos de descanso deste alvo?")) void command("rest", { target_type: targetType, target_id: targetId }); }}>Encerrar efeitos de descanso do alvo</button>
    </>}
    {error && <p role="alert">{error}</p>}
  </details>;
}
