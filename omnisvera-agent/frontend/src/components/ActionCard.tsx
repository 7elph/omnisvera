import { useEffect, useRef, useState } from "react";
import { createCommandRetry } from '../commandRetry';
import { spellTargetOutcome } from '../spellOutcome';
import TargetSelect, { type TargetOption } from "./TargetSelect";
import { describeAction, executeActionRef, commandRecoveryOptions, newDiceRequestId, type DescribedAction, type SpellCastTarget, type SpellCastResult } from "../api";

function blockText(block: DescribedAction["blocks"][number]): string {
  switch (block.type) {
    case "attack": return `ataque ${block.bonus != null ? `+${block.bonus}` : "sem bônus"}${block.count && block.count > 1 ? ` ×${block.count}` : ""}`;
    case "save": return `JP ${block.jp || "?"} (${block.effect === "halves" ? "metade" : "anula"})`;
    case "damage": return `dano ${block.dice || "?"}${block.when ? ` ${block.when}` : ""}`;
    case "heal": return `cura ${block.dice || "?"}`;
    case "condition": return `condição: ${block.text || "?"}`;
    case "resource": return `custo: ${block.label || block.key}`;
    case "money": return `custo em PO`;
    default: return block.text || "manual";
  }
}

export default function ActionCard({ actionRef, targets = [], caster }: {
  actionRef: string; targets?: TargetOption[]; caster?: { type: "character" | "token"; id: string };
}) {
  const [action, setAction] = useState<DescribedAction | null>(null);
  const [target, setTarget] = useState("");
  const [die, setDie] = useState("");
  const [outcome, setOutcome] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const commands = useRef(createCommandRetry(() => newDiceRequestId('action-library'), commandRecoveryOptions('action-library')));

  useEffect(() => {
    let active = true;
    setAction(null); setOutcome(""); setError("");
    void describeAction(actionRef).then((result) => { if (active) setAction(result); }).catch((reason) => { if (active) setError(reason instanceof Error ? reason.message : "Falha"); });
    return () => { active = false; };
  }, [actionRef]);

  function parseTarget(value: string): SpellCastTarget {
    return value.startsWith("token:") ? { type: "token", id: value.slice(6) } : { type: "character", id: value };
  }

  async function run() {
    if (!action?.executable || commands.current.pending) return;
    setError(""); setOutcome("");
    setBusy(true);
    try {
      const payload: { targets: SpellCastTarget[]; roll_mode?: "digital" | "physical"; d20?: number[]; caster_type?: "character" | "token"; caster_id?: string } = { targets: target ? [parseTarget(target)] : [] };
      if (die.trim()) { payload.roll_mode = "physical"; payload.d20 = [Number(die)]; }
      if (caster) { payload.caster_type = caster.type; payload.caster_id = caster.id; }
      const result = await commands.current.run({ actionRef, payload }, request_id => executeActionRef(actionRef, { ...payload, request_id }));
      if (!result) return;
      const inner = result.result as { results?: SpellCastResult['results']; result?: string; damage_total?: number } | undefined;
      if (inner?.results) setOutcome(inner.results.map(spellTargetOutcome).join(" · "));
      else if (inner?.result) setOutcome(`${inner.result === "hit" ? "Acertou" : "Errou"} · dano ${inner.damage_total}`);
      else setOutcome("Executado.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao executar"); }
    finally { setBusy(false); }
  }

  if (error && !action) return <p><small>{error}</small></p>;
  if (!action) return <p><small>Carregando ação…</small></p>;
  return (
    <article>
      {error && <p role="alert"><small>{error}</small></p>}
      <div><strong>{action.name}</strong> <small>{action.kind}</small></div>
      {action.blocks.map((block, index) => <p key={index}><small>{block.type === "manual" ? block.text : `· ${blockText(block)}`}</small></p>)}
      {action.executable && targets.length > 0 && <>
        <TargetSelect label={`Alvo de ${action.name}`} value={target} onChange={setTarget} targets={targets} />
        <input value={die} onChange={(event) => setDie(event.target.value)} placeholder="d20 físico (opcional)" />
        <button type="button" disabled={busy || !target} onClick={() => void run()}>{busy ? 'Confirmando…' : 'Executar'}</button>
      </>}
      {action.executable && targets.length === 0 && action.execute?.endpoint && <p><small>Executável via {action.execute.method} {action.execute.endpoint}.</small></p>}
      {!action.executable && <p><small>{action.note || action.execute?.note || "Somente leitura."}</small></p>}
      {outcome && <p role="status"><small>{outcome}</small></p>}
    </article>
  );
}
