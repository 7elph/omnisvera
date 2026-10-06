import { useRef, useState } from "react";
import { CombatEffectsState, newDiceRequestId, PlayableCharacterSummary, sendCombatEffectCommand, WorkspaceToken } from "../api";
import MonsterAttackPanel from "./MonsterAttackPanel";

export default function SummonControls({ token, mode, characters, tokens, state, physical, onChange }: {
  token: WorkspaceToken; mode: "gm" | "player"; characters: PlayableCharacterSummary[];
  tokens: WorkspaceToken[]; state: CombatEffectsState; physical: boolean; onChange: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const lock = useRef(false);
  const retry = useRef<{ version: number; id: string } | null>(null);
  const caster = token.sheet?.summon?.caster;
  const owner = characters.find(character => character.access_level === "owner")?.id;
  if (!caster || (mode !== "gm" && caster !== owner)) return null;
  const encounter = state.encounter;
  const current = encounter?.participants?.[encounter.turn_index ?? 0];
  const active = Boolean(encounter?.active);
  const participating = encounter?.participants?.some(member => member.target_type === "token" && member.target_id === token.id);
  const itsTurn = active && current?.target_type === "token" && current.target_id === token.id;
  const alive = (token.current_hp ?? 0) > 0;
  const canAttack = alive && (!active || itsTurn);
  const targets = tokens.filter(target => target.map_id === token.map_id && (!encounter?.battle_mode || encounter.participants?.some(member => member.target_type === "token" ? member.target_id === target.id : member.target_id === target.character_id)));
  const targetCharacters = characters.filter(character => targets.some(target => target.character_id === character.id));

  async function nextTurn() {
    if (lock.current || !itsTurn) return;
    lock.current = true; setBusy(true); setError("");
    if (retry.current?.version !== state.version) retry.current = { version: state.version, id: newDiceRequestId("summon-turn") };
    try {
      await sendCombatEffectCommand({ request_id: retry.current.id, expected_version: state.version, action: "next_turn", payload: {} });
      retry.current = null;
      await onChange();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao passar turno."); }
    finally { lock.current = false; setBusy(false); }
  }

  return <details key={`${token.id}:${itsTurn ? 'active' : 'waiting'}`} open={itsTurn || !active} className="workspace-summon-controls" aria-label={`Controle de ${token.name}`}>
    <summary>{token.name} · {itsTurn ? 'Seu turno' : `${token.current_hp ?? 0}/${token.maximum_hp ?? '—'} PV`}</summary>
    <h3>{token.name} · Ações da invocação</h3>
    <p role="status">{!alive ? "Invocação sem PV: não pode atacar." : !active ? "Escolha um alvo para atacar." : itsTurn ? `É o turno de ${token.name}.` : !participating ? "Invocação fora deste combate." : `Aguarde seu turno. Agora: ${current?.name || "participante oculto"}.`}</p>
    <MonsterAttackPanel key={`${token.id}:${encounter?.turn_sequence ?? "outside"}`} token={token} characters={targetCharacters} targets={targets} physical={physical} blocked={!canAttack} done={itsTurn && encounter?.action_committed} onChange={onChange} />
    {itsTurn && <button type="button" disabled={busy} onClick={() => void nextTurn()}>Concluir e passar turno →</button>}
    {error && <p role="alert">{error}</p>}
  </details>;
}
