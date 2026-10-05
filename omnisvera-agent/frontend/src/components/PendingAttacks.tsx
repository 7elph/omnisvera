import { useEffect, useState } from "react";
import { AttackResolution, listPendingAttacks } from "../api";

export default function PendingAttacks({ onOpen, refreshKey }: {
  onOpen: (resolution: AttackResolution) => void; refreshKey?: string;
}) {
  const [items, setItems] = useState<AttackResolution[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    let loading = false;
    const load = async () => {
      if (loading) return;
      loading = true;
      try {
        const result = await listPendingAttacks();
        if (alive) { setItems(result); setError(""); }
      } catch {
        if (alive) setError("Não foi possível conferir ataques pendentes. Tentando novamente.");
      } finally { loading = false; }
    };
    void load();
    const timer = window.setInterval(() => void load(), 15000);
    window.addEventListener("online", load);
    window.addEventListener("omnisvera-session-changed", load);
    return () => { alive = false; window.clearInterval(timer); window.removeEventListener("online", load); window.removeEventListener("omnisvera-session-changed", load); };
  }, [refreshKey]);
  if (!items.length && !error) return null;
  return <details className="workspace-gm-subsection">
    <summary>Ataques aguardando confirmação ({items.length})</summary>
    <small>O dano ainda não foi aplicado. Reabra o resultado; não role novamente.</small>
    {items.map(item => <button type="button" key={item.resolution_id} onClick={() => onOpen(item)}>
      {item.actor_name} → {item.target_name} · {item.attack_name} · conferir
    </button>)}
    {error && <p role="status">{error}</p>}
  </details>;
}
