import { useEffect, useRef, useState } from "react";
import { applyCharacterStateAction, PlayableCharacter } from "../api";
import SheetDetail from './SheetDetail';

const currencies = [
  ["copper", "Cobre", "copper_coins"], ["silver", "Prata", "silver_coins"],
  ["gold", "Ouro", "coins"], ["platinum", "Platina", "platinum_coins"],
] as const;

export default function CurrencyCounters({ character, onChange, summaryOnly = false, expanded = false }: {
  character: PlayableCharacter; onChange: (updated: PlayableCharacter) => Promise<void>; summaryOnly?: boolean; expanded?: boolean;
}) {
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const isGm = character.access_level === "gm";
  const editable = isGm || character.access_level === "owner";
  useEffect(() => { setDrafts({}); setError(""); }, [character.definition.id]);
  if (!character.state || !editable) return null;
  const balances = <span className="workspace-coin-strip">{currencies.map(([currency,label,field]) =>
    <span key={currency} title={label}><i className={`workspace-coin ${currency}`} aria-hidden="true">●</i><strong aria-label={`${label}: saldo`}>{Number(character.state?.[field] ?? 0)}</strong></span>
  )}</span>;
  if (summaryOnly || !isGm) return <section className="workspace-wallet" aria-label="Moedas">{isGm ? <SheetDetail title="Editar moedas" triggerLabel="Editar moedas" showIcon={false} description={<CurrencyCounters character={character} onChange={onChange} expanded />}>{balances}</SheetDetail> : balances}</section>;

  async function save(currency: string, label: string, value: number, balance: number) {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError("");
    try {
      const updated = await applyCharacterStateAction(character.definition.id, "set_currency",
        { currency, value, expected_balance: balance }, `${label}: ${balance} → ${value}`);
      setDrafts(current => { const next = { ...current }; delete next[currency]; return next; });
      await onChange(updated);
    } catch (e) { setError(e instanceof Error ? e.message : "Não foi possível salvar moedas"); }
    finally { lock.current = false; setBusy(false); }
  }

  return <details className="workspace-gm-subsection" aria-label="Moedas" open={expanded || undefined}>
    <summary>MOEDAS</summary>
    {balances}
    <section className="workspace-action-catalog">
    {currencies.map(([currency, label, field]) => {
      const balance = Number(character.state?.[field] ?? 0);
      const draft = drafts[currency] ?? String(balance);
      const value = Number(draft);
      const invalid = draft === "" || !Number.isInteger(value) || value < 0 || value > 2147483647 || (!isGm && value > balance);
      return <div key={currency} style={{ gridColumn: "1 / -1" }}>
        <label htmlFor={`coins-${character.definition.id}-${currency}`}>{label}</label>
        <div className="workspace-hp-quick-controls">
          <button type="button" aria-label={`Diminuir ${label}`} disabled={busy || value <= 0} onClick={() => setDrafts(current => ({ ...current, [currency]: String(Math.max(0, value - 1)) }))}>−</button>
          <input id={`coins-${character.definition.id}-${currency}`} aria-label={label} type="number" min={0} max={isGm ? 2147483647 : balance} step={1} inputMode="numeric" value={draft} disabled={busy} onChange={e => setDrafts(current => ({ ...current, [currency]: e.target.value }))} />
          {isGm ? <button type="button" aria-label={`Aumentar ${label}`} disabled={busy || value >= 2147483647} onClick={() => setDrafts(current => ({ ...current, [currency]: String(value + 1) }))}>+</button> : <span aria-hidden="true" />}
          <button type="button" aria-label={`Aplicar ${label}`} disabled={busy || invalid || value === balance} onClick={() => void save(currency, label, value, balance)} title={`Confirmar ${label}`}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /></svg></button>
        </div>
      </div>;
    })}
    {error && <p role="alert">{error}</p>}
    </section>
  </details>;
}
