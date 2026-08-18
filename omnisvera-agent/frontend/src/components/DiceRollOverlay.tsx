import { useEffect, useRef, useState } from "react";
import DicePhysicsCanvas, { DiceVisualRoll } from "./DicePhysicsCanvas";

function rollKey(roll: DiceVisualRoll) {
  return `${roll.id}:${roll.created_at || ""}`;
}

export default function DiceRollOverlay() {
  const [roll, setRoll] = useState<DiceVisualRoll | null>(null);
  const activeRef = useRef<DiceVisualRoll | null>(null);
  const queueRef = useRef<DiceVisualRoll[]>([]);
  const seenRef = useRef(new Map<string, number>());

  useEffect(() => { activeRef.current = roll; }, [roll]);

  useEffect(() => {
    const showRoll = (event: Event) => {
      const detail = (event as CustomEvent<DiceVisualRoll>).detail;
      if (!detail?.individual_results?.length) return;
      const now = Date.now();
      for (const [key, timestamp] of seenRef.current) if (now - timestamp > 60_000) seenRef.current.delete(key);
      const key = rollKey(detail);
      if (seenRef.current.has(key)) return;
      seenRef.current.set(key, now);
      if (activeRef.current) queueRef.current.push(detail);
      else { activeRef.current = detail; setRoll(detail); }
    };
    window.addEventListener("omnisvera-roll-created", showRoll);
    return () => {
      window.removeEventListener("omnisvera-roll-created", showRoll);
    };
  }, []);

  useEffect(() => {
    if (!roll) return;
    const timer = window.setTimeout(() => {
      const next = queueRef.current.shift() || null;
      activeRef.current = next;
      setRoll(next);
    }, 3400);
    return () => window.clearTimeout(timer);
  }, [roll]);

  if (!roll) return null;
  const math = `${roll.dice}: ${roll.individual_results.join(" + ")}${roll.modifier ? ` ${roll.modifier > 0 ? "+" : "−"} ${Math.abs(roll.modifier)}` : ""} = ${roll.total}`;
  return <div className="dice-roll-overlay" aria-live="assertive" aria-label={`${roll.label}: resultado ${roll.total}`}>
    <DicePhysicsCanvas roll={roll} />
    <div className="dice-roll-math"><small>{roll.label || "Rolagem de dados"}</small><strong>{roll.total}</strong><span>{math}</span></div>
  </div>;
}
