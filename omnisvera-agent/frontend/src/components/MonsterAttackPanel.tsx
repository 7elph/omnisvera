import { useRef, useState } from "react";
import { AttackResolution, confirmCharacterAttack, newDiceRequestId, PlayableCharacterSummary, resolveMonsterAttack, WorkspaceToken } from "../api";

export default function MonsterAttackPanel({ token, characters, targets = [], physical, done = false, onChange }: { token: WorkspaceToken; characters: PlayableCharacterSummary[]; targets?: WorkspaceToken[]; physical: boolean; done?: boolean; onChange: () => Promise<void> }) {
  const [target, setTargetValue] = useState("");
  const setTarget = (value: string) => {
    setTargetValue(value);
    window.dispatchEvent(new CustomEvent('omnisvera-attack-target', { detail: { actorId: token.id, targetId: value.replace(/^token:/, '') } }));
  };
  const [die, setDie] = useState("");
  const [result, setResult] = useState<AttackResolution | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const retry = useRef<{ key: string; id: string } | null>(null);
  async function act(index?: number) {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError("");
    try {
      if (index === undefined && result) {
        setResult(await confirmCharacterAttack(result.resolution_id));
        window.dispatchEvent(new CustomEvent('omnisvera-attack-target', { detail: {} }));
        await onChange();
      } else if (index !== undefined) {
        const targetToken = targets.find(t => t.id !== token.id && `token:${t.id}` === target);
        const payload = { attack_id: String(index), target_type: targetToken ? "token" as const : "character" as const, target_id: targetToken?.id || target, roll_mode: physical ? "physical" as const : "digital" as const, ...(physical ? { d20: Number(die) } : {}) };
        const key = JSON.stringify([token.id, payload]);
        if (retry.current?.key !== key) retry.current = { key, id: newDiceRequestId("monster") };
        setResult(await resolveMonsterAttack(token.id, { ...payload, request_id: retry.current.id }));
        retry.current = null;
      }
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha no ataque"); }
    finally { lock.current = false; setBusy(false); }
  }
  return <section className="workspace-action-catalog workspace-attack-catalog workspace-ally-attacks" aria-label={`Ataques de ${token.name}`}>
    <header><span>ATAQUES</span><small title="Bônus e dano vêm da ficha; confirme o resultado para aplicar dano.">{physical ? "d20 físico" : "Rolagem automática"}</small></header>
    <label>Alvo <select value={target} onChange={e => setTarget(e.target.value)}><option value="">Escolha um alvo</option>{characters.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}{targets.filter(t => t.token_type === "monster" && t.id !== token.id).map(t => <option key={t.id} value={`token:${t.id}`}>{t.name}</option>)}</select></label>
    {physical && <label>d20 físico <input type="number" min={1} max={20} value={die} onChange={e => setDie(e.target.value)} /></label>}
    {(token.sheet?.attacks || []).map((attack, index) => <article key={index}><div className="workspace-catalog-card-heading workspace-attack-card-heading"><strong>{attack.name}</strong></div><div className="workspace-catalog-card-summary"><small>{attack.damage || "Não configurado"}</small><b>{attack.bonus ?? "—"}</b></div><button disabled={done || busy || !target || !attack.damage || (result?.status === "pending")} onClick={() => void act(index)}>Atacar · rolar acerto e dano</button></article>)}
    {done && <p>Ação concluída. Use “Concluir e passar turno”.</p>}
    {!token.sheet?.attacks?.length && <p>Nenhum ataque configurado nesta criatura. Edite sua ficha.</p>}
    {result && <div role="status"><p>{result.attack_total} contra CA {result.target_ac} · {result.result === "hit" ? "Acertou" : "Errou"} · dano {result.damage_total}</p>{result.status === "pending" ? <button disabled={busy} onClick={() => void act()}>Confirmar resultado e aplicar dano</button> : <p>Resultado confirmado. Vida: {result.hp_before} → {result.hp_after}</p>}</div>}
    {error && <p role="alert">{error}</p>}
    {!!result?.breakdown?.manual_effects?.length && <p role="alert">Efeito adicional pendente: {result.breakdown.manual_effects.join(", ")}. O dano numérico foi calculado; resolva a proteção e as consequências descritas na ficha. Este efeito não foi aplicado automaticamente.</p>}
  </section>;
}
