import { mediaUrlFromVaultPath, PlayableCharacterSummary, WorkspaceToken, promoteCompanion } from "../api";
import { useState } from "react";
import MonsterAttackPanel from "./MonsterAttackPanel";
import TokenVitals from "./TokenVitals";

export default function CompanionAllySheet({ token, characters, targets, physical, onChange }: {
  token: WorkspaceToken; characters: PlayableCharacterSummary[]; targets: WorkspaceToken[];
  physical: boolean; onChange: () => Promise<void>;
}) {
  const sheet = token.sheet;
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return <section aria-label={`Ficha de ${token.name}`}>
    {error && <p role="alert">{error}</p>}
    <button type="button" disabled={busy} onClick={async () => {
      if (!window.confirm("Converter Dorn para a mesma ficha dos jogadores, preservando PV, condições e ataques? Nenhum acesso de jogador será criado automaticamente.")) return;
      setBusy(true); setError("");
      try { await promoteCompanion(token.id); await onChange(); window.dispatchEvent(new CustomEvent("omnisvera-companion-promoted")); }
      catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao converter ficha"); }
      finally { setBusy(false); }
    }}>Usar ficha de jogador</button>
    <header className="workspace-character-identity">{token.image_path && <img src={mediaUrlFromVaultPath(token.image_path)} alt={`Retrato de ${token.name}`} />}<div className="workspace-character-copy">
      <small>ALIADO · CONTROLE DO MESTRE</small><h2>{token.name}</h2><p>{sheet?.role}</p>
    </div></header>
    <section className="workspace-vitals"><div className="workspace-hp-heading"><span><small>VIDA</small><strong>{token.current_hp ?? "—"}<em>/ {token.maximum_hp ?? "—"}</em></strong></span><span className="workspace-armor-class"><small>CA</small><strong>{sheet?.armor_class ?? "—"}</strong></span></div><div className="workspace-hp-track"><i style={{ width: `${token.maximum_hp ? Math.max(0, Math.min(100, Number(token.current_hp || 0) / token.maximum_hp * 100)) : 0}%` }} /></div></section>
    <TokenVitals key={`${token.id}:${token.current_hp}:${token.maximum_hp}`} token={token} editable compact showPortrait={false} onChange={onChange} />
    <section className="workspace-conditions workspace-status-under-vitals"><p>STATUS - {token.conditions.length ? token.conditions.join(" · ") : "Nenhum"}</p></section>
    <section className="workspace-action-catalog"><header><span>DEFESAS E MOVIMENTO</span></header><article><span>Proteção</span><b>{sheet?.saving_throw ?? "—"}</b></article><article><span>Movimento</span><b>{sheet?.movement || "—"}</b></article></section>
    <MonsterAttackPanel key={token.id} token={token} characters={characters} targets={targets} physical={physical} onChange={onChange} />
    <section className="workspace-action-catalog"><header><span>HABILIDADES</span></header>
      {(sheet?.abilities || []).map(ability => <details key={ability}><summary>{ability.split(":")[0]}</summary><p>{ability}</p></details>)}
    </section>
    <details><summary>Descrição e regras do aliado</summary><p>{sheet?.description}</p><p>{sheet?.notes}</p></details>
  </section>;
}
