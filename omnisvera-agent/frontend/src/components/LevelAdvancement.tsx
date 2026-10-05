import { useRef, useState } from "react";
import { confirmLevel, previewLevel, type LevelPreview, type PlayableCharacter } from "../api";

export default function LevelAdvancement({ id, level, confirmedLevel, onApplied }: {
  id: string; level: number; confirmedLevel?: number | null; onApplied: (character: PlayableCharacter) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [roll, setRoll] = useState("");
  const [hpPolicy, setHpPolicy] = useState('preserve_wounds');
  const [plan, setPlan] = useState<LevelPreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(false);
  const targetLevel = level === 1 || confirmedLevel === level ? level + 1 : level;
  const hpRoll = roll.trim() ? Number(roll) : undefined;
  async function run(confirm = false) {
    if (pending.current || (confirm && plan?.status !== "ready")) return;
    pending.current = true; setBusy(true); setError("");
    try {
      if (confirm && plan) {
        const result = await confirmLevel(id, plan.fingerprint ?? "", hpRoll, targetLevel, hpPolicy);
        // Mark applied before refreshing: a refresh failure must not offer another grant.
        setPlan({ ...plan, status: "applied" });
        await onApplied(result.character);
      } else setPlan(await previewLevel(id, hpRoll, targetLevel, hpPolicy));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível conferir a progressão.");
    } finally { pending.current = false; setBusy(false); }
  }
  if (!["vezemir", "raziel", "morthak", "dorn7"].includes(id)) return null;
  const visibleChanges = (plan?.changes ?? []).filter(change => !change.noop);
  const hiddenCount = (plan?.changes ?? []).length - visibleChanges.length;
  return <>
    <button type="button" className="character-level-edit" onClick={() => { setOpen(true); void run(); }}>{targetLevel === level ? `Conferir nível ${targetLevel}` : `Subir para nível ${targetLevel}`}</button>
      {open && <div className="character-level-backdrop"><section className="character-level-dialog character-level-preview" role="dialog" aria-modal="true" aria-label={`Progressão ao nível ${targetLevel}`}>
      <h3>Progressão ao nível {targetLevel}</h3>
      {plan?.status !== 'applied' && <label>Vida ao avançar<select value={hpPolicy} disabled={busy} onChange={event => { setHpPolicy(event.target.value); setPlan(null); }}>
        <option value="preserve_wounds">Preservar ferimentos — regra da Sessão 6</option>
        <option value="preserve_current">Manter PV atuais (limita ao novo máximo)</option>
      </select></label>}
      {plan?.requires_hp_roll && plan.status !== "applied" && <label>Resultado natural do dado de vida{plan?.hit_die ? ` (d${plan.hit_die})` : ""}
        <input type="number" min={1} max={plan?.hit_die ?? 10} step={1} value={roll} disabled={busy} onChange={event => { setRoll(event.target.value); setPlan({ ...plan, status: 'blocked' }); }} />
      </label>}
      {plan && <><p>{plan.source}</p>
        {plan.xp_required != null && <p>Experiência: {plan.xp_current ?? "—"} / {plan.xp_required} para o nv{targetLevel}.</p>}
        {plan.status === "applied" ? <p role="status">Avanço registrado. Nenhum benefício será concedido novamente.</p> : <>
          {visibleChanges.length === 0
            ? <p role="status">Nenhuma alteração pendente{hiddenCount > 0 ? ` (${hiddenCount} conferidas sem mudança)` : ""}.</p>
            : <dl>{visibleChanges.map(change => <div key={change.field}><dt>{change.label}</dt><dd>{change.before} → {change.after}{change.current != null ? ` (atual: ${change.current})` : ""}{change.note ? ` — ${change.note}` : ""}</dd></div>)}</dl>}
        </>}
        {plan.warnings.map(message => <p key={message}>{message}</p>)}
        {plan.blockers.map(message => <p key={message} role="alert">{message}</p>)}
      </>}
      {error && <p role="alert">{error}</p>}
      {plan?.status !== "applied" && <button type="button" disabled={busy} onClick={() => void run()}>Atualizar prévia</button>}
      {plan?.status === "ready" && <button type="button" disabled={busy} onClick={() => void run(true)}>{hpPolicy === 'preserve_current' ? 'Confirmar avanço sem curar' : 'Confirmar avanço preservando ferimentos'}</button>}
      <button type="button" disabled={busy} onClick={() => setOpen(false)}>Fechar</button>
    </section></div>}
  </>;
}
