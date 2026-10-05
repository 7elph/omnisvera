import { AttackResolution } from "../api";

export default function SpellResolution({ resolution, busy, onConfirm, onClose }: {
  resolution: AttackResolution; busy: boolean; onConfirm: () => void; onClose: () => void;
}) {
  return <div className="workspace-item-modal-backdrop" role="presentation">
    <section className="workspace-item-modal" role="dialog" aria-modal="true" aria-label="Resolução da magia">
      <header><h2>{resolution.actor_name} → {resolution.target_name}</h2><button onClick={onClose} aria-label="Fechar resolução">×</button></header>
      <strong>{resolution.attack_name} · acerto automático</strong>
      <p>{resolution.damage_formula} · dano {resolution.damage_total}</p>
      <p>Consumo: {resolution.breakdown.resource_cost?.amount || 1} uso. Não há rolagem de acerto.</p>
      {(resolution.breakdown.manual_effects || []).map(text => <p key={text}>{text}</p>)}
      {resolution.confirmed ? <><p>Aplicado · PV {resolution.hp_before} → {resolution.hp_after}</p><button onClick={onClose}>Concluído</button></>
        : <><p role="status">Prévia: vida e usos ainda não foram alterados.</p><button disabled={busy} onClick={onConfirm}>Confirmar uso e aplicar dano</button></>}
    </section>
  </div>;
}
