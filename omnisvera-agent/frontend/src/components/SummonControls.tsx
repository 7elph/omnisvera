import { useRef, useState } from "react";
import { CombatEffectsState, newDiceRequestId, PlayableCharacterSummary, sendCombatEffectCommand, useCharacterTechnique, WorkspaceToken } from "../api";
import MonsterAttackPanel from "./MonsterAttackPanel";

export default function SummonControls({ token, mode, characters, tokens, state, physical, onChange }: {
  token: WorkspaceToken; mode: "gm" | "player"; characters: PlayableCharacterSummary[];
  tokens: WorkspaceToken[]; state: CombatEffectsState; physical: boolean; onChange: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const lock = useRef(false);
  const dismissalId = useRef<string | null>(null);
  const [dismissed,setDismissed]=useState(false);
  const retry = useRef<{ version: number; id: string } | null>(null);
  const confirmedTurnVersion = useRef<number | null>(null);
  const caster = token.sheet?.summon?.caster;
  const owner = characters.find(character => character.access_level === "owner")?.id;
  if (!caster || (mode !== "gm" && caster !== owner)) return null;
  const encounter = state.encounter;
  const current = encounter?.participants?.[encounter.turn_index ?? 0];
  const active = Boolean(encounter?.active);
  const participating = encounter?.participants?.some(member => member.target_type === "token" && member.target_id === token.id);
  const itsTurn = active && current?.target_type === "token" && current.target_id === token.id;
  const alive = (token.current_hp ?? 0) > 0;
  const awaitingTurnSync = confirmedTurnVersion.current === state.version;
  const canAttack = alive && (!active || itsTurn) && !awaitingTurnSync;
  const targets = tokens.filter(target => target.map_id === token.map_id && (!encounter?.battle_mode || encounter.participants?.some(member => member.target_type === "token" ? member.target_id === target.id : member.target_id === target.character_id)));
  const targetCharacters = characters.filter(character => targets.some(target => target.character_id === character.id));

  async function nextTurn() {
    if (lock.current || !itsTurn || confirmedTurnVersion.current === state.version) return;
    lock.current = true; setBusy(true); setError("");
    if (retry.current?.version !== state.version) retry.current = { version: state.version, id: newDiceRequestId("summon-turn") };
    let applied = false;
    try {
      await sendCombatEffectCommand({ request_id: retry.current.id, expected_version: state.version, action: "next_turn", payload: {} });
      applied = true;
      confirmedTurnVersion.current = state.version;
      retry.current = null;
      await onChange();
    } catch (reason) { if (!applied) setError(reason instanceof Error ? reason.message : "Falha ao passar turno."); }
    finally { lock.current = false; setBusy(false); }
  }
  async function dismiss(){
    if(lock.current || !caster || !window.confirm(`Dispensar ${token.name}? O uso diário não será devolvido.`))return;
    lock.current=true;setBusy(true);setError('');dismissalId.current ||= newDiceRequestId('summon-dismiss');
    try{await useCharacterTechnique(caster,'dispensar-invocacao',{request_id:dismissalId.current,target_type:'token',target_id:token.id});setDismissed(true);await onChange();}
    catch(reason){setError(reason instanceof Error?reason.message:'Falha ao dispensar');}
    finally{lock.current=false;setBusy(false);}
  }
  if(dismissed)return <p role="status">Invocação dispensada. O uso diário não foi devolvido.</p>;

  return <details key={`${token.id}:${itsTurn ? 'active' : 'waiting'}`} open={itsTurn || !active} className="workspace-summon-controls" aria-label={`Controle de ${token.name}`}>
    <summary>{token.name} · {itsTurn ? 'Seu turno' : `${token.current_hp ?? 0}/${token.maximum_hp ?? '—'} PV`}</summary>
    <h3>{token.name} · Ações da invocação</h3>
    <p role="status">{awaitingTurnSync ? "Turno confirmado. Aguardando sincronização; não repita a ação." : !alive ? "Invocação sem PV: não pode atacar." : !active ? "Escolha um alvo para atacar." : itsTurn ? `É o turno de ${token.name}.` : !participating ? "Invocação fora deste combate." : `Aguarde seu turno. Agora: ${current?.name || "participante oculto"}.`}</p>
    <MonsterAttackPanel key={`${token.id}:${encounter?.turn_sequence ?? "outside"}`} token={token} combat={state} characters={targetCharacters} targets={targets} gridded={Boolean(token.grid_position)} physical={physical} blocked={!canAttack} done={itsTurn && encounter?.action_committed} onChange={onChange} />
    {itsTurn && <button type="button" disabled={busy || awaitingTurnSync} onClick={() => void nextTurn()}>Concluir e passar turno →</button>}
    {alive && token.sheet?.summon?.technique && token.sheet.summon.technique!=='clonagem' && <button type="button" disabled={busy} onClick={()=>void dismiss()}>Dispensar</button>}
    {error && <p role="alert">{error}</p>}
  </details>;
}
