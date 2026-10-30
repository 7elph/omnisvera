import ParasiteControl from './ParasiteControl';
import type { RustContactChoice } from './RustContactOptions';
import type { MonsterContactPreview } from '../api';
import { useEffect, useRef, useState } from "react";
import TargetSelect from './TargetSelect';
import { activateCard } from './cardActivation';
import { monsterBreathOutcomeText } from '../attackOutcome';
import SheetDetail from './SheetDetail';
import { createCommandRetry } from '../commandRetry';
import { spellTargetOutcome } from '../spellOutcome';
import { sendCombatEffectCommand, type MonsterBreathPreview } from '../api';
import { updateWorkspaceToken } from '../api';
import { AttackResolution, castCompendiumSpell, commandRecoveryOptions, CombatEffectsState, confirmCharacterAttack, executeTokenAction, getWorkspaceTokenActions, listCompendiumSpells, newDiceRequestId, PlayableCharacterSummary, resolveMonsterAttack, SpellCastResult, WorkspaceToken, type CompendiumSpellsResponse, type MonsterActionMap } from "../api";

function ConjurePicker({ tradition, tokenId, target, die, physical, disabled, gridded, onArm, onDone }: {
  tradition: string; tokenId: string; target: string; die: string; physical: boolean; disabled: boolean;
  gridded: boolean; onArm: (spellId: string, spellName: string) => void;
  onDone: (name: string, result: SpellCastResult) => void | Promise<void>;
}) {
  const [grimoire, setGrimoire] = useState<CompendiumSpellsResponse | null>(null);
  const [circle, setCircle] = useState("");
  const [spellId, setSpellId] = useState("");
  const [error, setError] = useState("");
  const [casting, setCasting] = useState(false);
  const commands = useRef(createCommandRetry(() => newDiceRequestId("monster-grimoire"), commandRecoveryOptions("monster-grimoire")));
  useEffect(() => {
    let active = true;
    void listCompendiumSpells().then((catalog) => { if (active) setGrimoire(catalog); }).catch(() => {});
    return () => { active = false; };
  }, []);
  const options = (grimoire?.spells || []).filter((spell) =>
    (!tradition || spell.tradition === tradition) && (!circle || String(spell.circle) === circle));
  const chosen = options.find((spell) => spell.id === spellId) || null;
  async function castSelected() {
    if (!chosen || chosen.automation?.status === 'blocked' || disabled || commands.current.pending) return;
    if (gridded) { onArm(chosen.id, chosen.name); return; }
    setCasting(true); setError("");
    const targetToken = target.startsWith("token:") ? target.slice(6) : null;
    const manualDice = physical && !['healing_hp', 'condition_cure'].includes(chosen.automation?.family || '');
    const payload = { caster_type: "token" as const, caster_id: tokenId,
      targets: [{ type: targetToken ? "token" as const : "character" as const, id: targetToken || target }],
      roll_mode: manualDice ? "physical" as const : "digital" as const,
      ...(manualDice ? { d20: [Number(die)] } : {}) };
    try {
      await commands.current.run({ spellId: chosen.id, payload }, async request_id => {
        const result = await castCompendiumSpell(chosen.id, { ...payload, request_id });
        await onDone(chosen.name, result);
        return result;
      });
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao conjurar"); }
    finally { setCasting(false); }
  }
  return <div>
    <select aria-label="Círculo" value={circle} onChange={(event) => { setCircle(event.target.value); setSpellId(""); }}>
      <option value="">Círculo…</option>
      {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((level) => <option key={level} value={String(level)}>{level}º</option>)}
    </select>
    <select aria-label="Magia do grimório" value={spellId} onChange={(event) => setSpellId(event.target.value)}>
      <option value="">Magia… ({options.length})</option>
      {options.slice(0, 400).map((spell) => <option key={spell.id} value={spell.id}>{spell.name} · {spell.circle}º</option>)}
    </select>
    {chosen?.automation && <small>{chosen.automation.note}</small>}
    <button type="button" disabled={disabled || casting || !chosen || chosen.automation?.status === 'blocked' || (!gridded && (!target || (physical && !die && !['healing_hp', 'condition_cure'].includes(chosen?.automation?.family || ''))))} onClick={() => void castSelected()}>{casting ? "Confirmando…" : gridded ? "Mirar magia no grid" : "Conjurar do grimório"}</button>
    {error && <p role="alert">{error}</p>}
  </div>;
}

export default function MonsterAttackPanel({ token, characters, targets = [], physical, done = false, blocked: externallyBlocked = false, combat, gridded = false, onChange }: { token: WorkspaceToken; characters: PlayableCharacterSummary[]; targets?: WorkspaceToken[]; physical: boolean; done?: boolean; blocked?: boolean; combat?: CombatEffectsState; gridded?: boolean; onChange: () => Promise<void> }) {
  function spellBudget(id:string){const entry=token.sheet?.spell_repertoire?.find(s=>s.spell_id===id);return entry?{remaining:Math.max(0,entry.daily_uses-Number(token.sheet?.monster_runtime?.usage?.['spell:'+id]||0)),maximum:entry.daily_uses}:null;}
  const spellBlocked=(id:string)=>Boolean(token.sheet?.spell_repertoire&&(!spellBudget(id)||!Number.isFinite(spellBudget(id)!.remaining)||spellBudget(id)!.remaining<=0));
  const spellCounter=(id:string)=>{const budget=spellBudget(id);return budget?` · ${budget.remaining}/${budget.maximum}`:'';};
  const condition=combat?.effects?.find(e=>e.monster_condition&&e.blocks_actions&&((e.target_type==='token'&&e.target_id===token.id)||(e.target_type==='character'&&e.target_id===token.character_id)));
  const blocked=externallyBlocked||Boolean(condition);
  const [target, setTargetValue] = useState("");
  const setTarget = (value: string) => {
    setTargetValue(value);
    window.dispatchEvent(new CustomEvent('omnisvera-attack-target', { detail: { actorId: token.id, targetId: value.replace(/^token:/, '') } }));
  };
  const [die, setDie] = useState("");
  const [result, setResult] = useState<AttackResolution | null>(null);
  const [actions, setActions] = useState<MonsterActionMap | null>(null);
  const [execResult, setExecResult] = useState<{ name: string; result: SpellCastResult; outcome?:ReturnType<typeof monsterBreathOutcomeText> } | null>(null);
  const [pending, setPending] = useState<null | { kind: "attack"; index: number; label: string; armId: string } | { kind: "usable"; name: string; armId: string } | { kind: "spell"; spellId: string; entryName: string; spellName: string; armId: string }>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    setActions(null); setExecResult(null);
    void getWorkspaceTokenActions(token.id).then((map) => { if (active) setActions(map); }).catch(() => {});
    return () => { active = false; };
  }, [token.id,token.name,JSON.stringify(token.sheet?.attacks),JSON.stringify(token.sheet?.abilities),token.sheet?.source?.monster_id]);
  const lock = useRef(false);
  const retry = useRef<{ key: string; id: string } | null>(null);
  const genericCommands = useRef(createCommandRetry(() => newDiceRequestId("monster-action"), commandRecoveryOptions("monster-action")));
  type RingRange = { mode: string; range_m?: number; range_cells?: number } | null;
  function arm(actionRef: string, actionLabel: string) {
    const armId = crypto.randomUUID();
    window.dispatchEvent(new CustomEvent('omnisvera-targeting-arm', { detail: { actionRef, actionLabel, attackerTokenId: token.id, armId } }));
    return armId;
  }
  function disarm() {
    setPending(null);
    window.dispatchEvent(new CustomEvent('omnisvera-targeting-clear'));
  }
  function splitTarget(targetId: string): { type: "token" | "character"; id: string } {
    if (targets.some(t => t.id === targetId)) return {type:'token',id:targetId};
    const targetToken = targets.find(t => t.id !== token.id && `token:${t.id}` === targetId);
    if (targetToken) return { type: "token", id: targetToken.id };
    return targetId.startsWith("token:") ? { type: "token", id: targetId.slice(6) } : { type: "character", id: targetId };
  }
  const selectedToken = targets.find(t => `token:${t.id}` === target);
  async function act(index?: number, targetId?: string, range?: RingRange) {
    if (lock.current || blocked) return;
    lock.current = true; setBusy(true); setError("");
    let applied = false;
    try {
      if (index === undefined && result) {
        setResult(await confirmCharacterAttack(result.resolution_id));
        applied = true;
        window.dispatchEvent(new CustomEvent('omnisvera-attack-target', { detail: {} }));
        await onChange();
      } else if (index !== undefined) {
        const picked = targetId || target;
        const split = splitTarget(picked);
        const manualDice = physical && !range;
        const payload = { attack_id: String(index), target_type: split.type, target_id: split.id, roll_mode: manualDice ? "physical" as const : "digital" as const, ...(manualDice ? { d20: Number(die) } : {}), ...(range?.mode === "ranged" && range.range_m != null ? { range_m: range.range_m } : {}), ...(range && range.mode !== "ranged" ? { range_cells: 1 } : {}) };
        const key = JSON.stringify([token.id, payload]);
        if (retry.current?.key !== key) retry.current = { key, id: newDiceRequestId("monster") };
        const resolution = await resolveMonsterAttack(token.id, { ...payload, request_id: retry.current.id });
        setResult(resolution);
        if(range){setResult(await confirmCharacterAttack(resolution.resolution_id));applied=true;}
        retry.current = null;
        await onChange();
      }
      if(applied)setActions(await getWorkspaceTokenActions(token.id));
    } catch (reason) { setError(applied ? "Ataque confirmado. A atualização da tela falhou; não repita o ataque." : reason instanceof Error ? reason.message : "Falha no ataque"); }
    finally { lock.current = false; setBusy(false); }
  }
  async function conjureNamed(entryName: string, spellId: string, spellName: string, targetId?: string, range?: RingRange) {
    if (lock.current || blocked || done) return;
    lock.current = true; setBusy(true); setError("");
    try {
      const picked = targetId || target;
      const split = splitTarget(picked);
      const manualDice = physical && !range;
      const payload = {
        caster_type: "token", caster_id: token.id,
        targets: [split],
        roll_mode: manualDice ? "physical" as const : "digital" as const, ...(manualDice ? { d20: [Number(die)] } : {}),
        ...(range?.mode === "ranged" && range.range_m != null ? { range_m: range.range_m } : {}),
        ...(range && range.mode !== "ranged" ? { range_cells: 1 } : {}),
      };
      await genericCommands.current.run({ spellId, payload, turn: [combat?.encounter?.started_at, combat?.encounter?.turn_sequence] }, async request_id => {
        const outcome = await castCompendiumSpell(spellId, { ...payload, caster_type: "token", request_id });
        setExecResult({ name: `${entryName} · ${spellName}`, result: outcome });
        await onChange();
        return outcome;
      });
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao conjurar"); }
    finally { lock.current = false; setBusy(false); }
  }
  async function executeUsable(name: string, targetId?: string, range?: RingRange) {
    if (lock.current || blocked || done) return;
    lock.current = true; setBusy(true); setError("");
    try {
      const picked = targetId || target;
      const split = splitTarget(picked);
      const manualDice = physical && !range;
      const payload = {
        ability_name: name,
        targets: [split],
        roll_mode: manualDice ? "physical" as const : "digital" as const, ...(manualDice ? { d20: [Number(die)] } : {}),
        ...(range?.mode === "ranged" && range.range_m != null ? { range_m: range.range_m } : {}),
        ...(range && range.mode !== "ranged" ? { range_cells: 1 } : {}),
      };
      await genericCommands.current.run({ tokenId: token.id, payload, turn: [combat?.encounter?.started_at, combat?.encounter?.turn_sequence] }, async request_id => {
        const outcome = await executeTokenAction(token.id, { ...payload, request_id });
        setExecResult({ name, result: outcome });
        await onChange();
        return outcome;
      });
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha na ação"); }
    finally { lock.current = false; setBusy(false); }
  }
  async function executeContact(preview:MonsterContactPreview,choice?:RustContactChoice){
    if(lock.current)return;
    lock.current=true;setBusy(true);setError('');
    try{
      const payload={token_id:token.id,target_pin_id:preview.target_pin_id,fingerprint:preview.fingerprint,...(choice||{})};
      const key=JSON.stringify(['contact',payload]);
      if(retry.current?.key!==key)retry.current={key,id:newDiceRequestId('monster-contact')};
      await sendCombatEffectCommand({request_id:retry.current.id,expected_version:preview.version,action:'monster_contact',payload});
      retry.current=null;await onChange();setActions(await getWorkspaceTokenActions(token.id));
    }catch(reason){setError(reason instanceof Error?reason.message:'Falha no contato');}
    finally{lock.current=false;setBusy(false);}
  }
  async function executeBreath(name:string,aimId:string,preview:MonsterBreathPreview){
    if(lock.current||blocked||done)return;
    lock.current=true;setBusy(true);setError('');
    const payload={token_id:token.id,ability_name:name,aim_token_id:aimId,definition_revision:preview.contract.revision,area_fingerprint:preview.contract.area_fingerprint,
      ...(preview.contract.requires_eye_contact?{eye_contact_confirmed:true}:{})};
    const key=JSON.stringify(payload);
    if(retry.current?.key!==key)retry.current={key,id:newDiceRequestId('monster-breath')};
    let applied=false;
    try{
      const response=await sendCombatEffectCommand({request_id:retry.current.id,expected_version:preview.version,action:'monster_breath',payload});
      applied=true;
      const result=response.protocol_result as unknown as {label:string;results:SpellCastResult['results'];damage_roll:Parameters<typeof monsterBreathOutcomeText>[0]['roll']};
      setExecResult({name,outcome:monsterBreathOutcomeText({roll:result.damage_roll,results:result.results}),result:{label:name,caster:token.name,mechanic:{save:null,save_effect:null,damage:null},results:result.results,manual_note:null}});
      retry.current=null;await onChange();
      setActions(await getWorkspaceTokenActions(token.id));
    }catch(reason){setError(applied?'Baforada aplicada. A atualização da tela falhou; não repita a ação.':reason instanceof Error?reason.message:'Falha na baforada');}
    finally{lock.current=false;setBusy(false);}
  }
  useEffect(() => {
    const confirm = (event: Event) => {
      const detail = (event as CustomEvent).detail || {};
      if (!pending || !detail.targetId || detail.armId !== pending.armId) return;
      const range = (detail.range || null) as RingRange;
      if (pending.kind === "attack") { if(detail.contact)void executeContact(detail.contact,detail.rustChoice); else void act(pending.index, detail.targetId, range); }
      else if (pending.kind === "usable") {
        if(detail.breath)void executeBreath(pending.name,detail.targetId,detail.breath);
        else void executeUsable(pending.name, detail.targetId, range);
      }
      else void conjureNamed(pending.entryName, pending.spellId, pending.spellName, detail.targetId, range);
      setPending(null);
      window.dispatchEvent(new CustomEvent('omnisvera-targeting-clear'));
    };
    window.addEventListener('omnisvera-targeting-confirm', confirm);
    const clear = (event: Event) => {
      const detail = (event as CustomEvent).detail || {};
      if (!detail.armId || (pending && detail.armId === pending.armId)) setPending(null);
    };
    window.addEventListener('omnisvera-targeting-clear', clear);
    return () => { window.removeEventListener('omnisvera-targeting-confirm', confirm); window.removeEventListener('omnisvera-targeting-clear', clear); };
  });
  const usableEntries=actions?[...actions.active_abilities,...(token.sheet?.spell_repertoire?[]:actions.spellcasting.filter(entry=>!actions.active_abilities.some(other=>other.name===entry.name)))]:[];
  return <section className="workspace-action-catalog workspace-attack-catalog workspace-ally-attacks" aria-label={`Ataques de ${token.name}`}>
    <header><span>ATAQUES</span><small title="Bônus e dano vêm da ficha; confirme o resultado para aplicar dano.">{physical && !gridded ? "d20 físico" : "Rolagem automática"}</small></header>
    {condition&&<p role="status">{condition.label}: não pode agir neste estado.</p>}
    <fieldset disabled={blocked && !token.sheet?.statless} style={{ border: 0, padding: 0, margin: 0 }}>
    {Object.keys(token.sheet?.movement_modes||{}).length>1&&<label>Movimento <select aria-label={`Modo de movimento de ${token.name}`} value={token.sheet?.movement_mode||'walk'} disabled={busy} onChange={async e=>{
      if(lock.current)return;lock.current=true;setBusy(true);setError('');
      try{await updateWorkspaceToken(token.id,{sheet:{...token.sheet,movement_mode:e.target.value}});await onChange();}
      catch(reason){setError(reason instanceof Error?reason.message:'Não foi possível selecionar o movimento.');}
      finally{lock.current=false;setBusy(false);}
    }}>{Object.entries(token.sheet?.movement_modes||{}).map(([key,speed])=><option key={key} value={key}>{({walk:'Terrestre',fly:'Voo',swim:'Natação',climb:'Escalada',burrow:'Escavação'} as Record<string,string>)[key]||key} · {speed} m</option>)}</select></label>}
    {!gridded && <label>Alvo <TargetSelect label={`Alvo de ${token.name}`} value={target} onChange={setTarget} disabled={busy || (blocked && !token.sheet?.statless)} targets={[...characters.map(character => ({ id: character.id, name: character.name })), ...targets.filter(item => item.token_type === 'monster' && item.id !== token.id).map(item => ({ id: `token:${item.id}`, name: item.name }))]} /></label>}
    {gridded && pending && <p><small>Mirando: {pending.kind === "attack" ? pending.label : pending.kind === "usable" ? pending.name : `${pending.entryName} · ${pending.spellName}`} — clique no alvo e confirme Sim ou Não.</small> <button type="button" onClick={disarm}>Cancelar</button></p>}
    {!gridded && physical && <label>d20 físico <input type="number" min={1} max={20} value={die} onChange={e => setDie(e.target.value)} /></label>}
    {result && <small>Alvo resolvido: {result.target_name} · CA {result.target_ac}</small>}
    {(token.sheet?.attacks || []).map((attack, index) => <article key={index} onClick={activateCard}><div className="workspace-catalog-card-heading workspace-attack-card-heading"><strong>{attack.name}</strong></div><div className="workspace-catalog-card-summary"><small>{attack.damage || "Não configurado"}</small><b>{attack.bonus ?? "—"}</b></div>{actions?.attacks[index]?.execution_kind==='passive_grid'?<small>Passiva · 10 em voo no grid</small>:gridded
      ? <button data-card-command title={actions?.attacks[index]?.notes || actions?.attacks[index]?.reason} disabled={(done && !token.sheet?.statless) || busy || !attack.damage || actions?.attacks[index]?.status === "incomplete"} onClick={() => { const armId = arm(`token:${token.id}:attack:${index}`, `${token.name} · ${attack.name}`); setPending({ kind: "attack", index, label: attack.name, armId }); }}>Usar</button>
      : <button title={actions?.attacks[index]?.notes || actions?.attacks[index]?.reason} disabled={done || busy || !target || !attack.damage || actions?.attacks[index]?.status === "incomplete" || (result?.status === "pending")} onClick={() => void act(index)}>Atacar · rolar acerto e dano</button>}</article>)}
    {done && <p>Ação concluída. Use “Concluir e passar turno”.</p>}
    {!token.sheet?.attacks?.length && <p>Nenhum ataque configurado nesta criatura. Edite sua ficha.</p>}
    {result && <div role="status"><p>{result.attack_total} contra CA {result.target_ac} · {result.result === "hit" ? "Acertou" : "Errou"} · dano {result.damage_total}</p>{result.status === "pending" ? <button disabled={busy} onClick={() => void act()}>Confirmar resultado e aplicar dano</button> : <p>Resultado confirmado. Vida: {result.hp_before} → {result.hp_after}</p>}</div>}
    {!!actions && usableEntries.length > 0 && <>
      <header><span>USÁVEIS</span><small title="Habilidades e conjurações com JP e dano rolam e aplicam na hora.">JP + dano automáticos</small></header>
      {usableEntries.map((entry) => {
        const native=actions.native_breaths?.[entry.name];
        return <article key={entry.name} onClick={activateCard}><div className="workspace-catalog-card-heading workspace-attack-card-heading"><strong>{entry.name}</strong></div><div className="workspace-catalog-card-summary"><small>{native?.attacks_until_ready!=null ? (native.ready?'1/1':'0/1') : native ? (native.requires_eye_contact?'Contato visual':native.execution_status==='native'?'Área e JP automáticas':'Resolução assistida') : entry.frequency || 'ver ficha'}</small></div>{gridded
        ? <button data-card-command title={native?.attacks_until_ready ? `Faltam ${native.attacks_until_ready} ataques confirmados` : native?.gaps.join('; ')} disabled={done || busy || native?.ready===false || Boolean(native&&native.execution_status!=='native')} onClick={() => { const armId = arm(`token:${token.id}:ability:${entry.name}`, `${token.name} · ${entry.name}`); setPending({ kind: "usable", name: entry.name, armId }); }}>Usar</button>
        : <button disabled={done || busy || Boolean(native) || !target || (physical && !die)} onClick={() => void executeUsable(entry.name)}>{native?'Posicione no grid':'Executar · JP e dano na hora'}</button>}</article>;
      })}
    </>}
    {execResult && <div role="status">{execResult.outcome?<><p>{execResult.outcome.summary}</p><SheetDetail title={execResult.name} description={execResult.outcome.details} showIcon={false}>Ver resultado</SheetDetail></>:execResult.result.results.map((outcome, index) => <p key={index}>{execResult.name} → {spellTargetOutcome(outcome)}</p>)}{execResult.result.manual_note && <p>{execResult.result.manual_note}</p>}</div>}
    {!!actions && actions.spellcasting.length > 0 && <>
      <header><span>CONJURAÇÃO</span><small>grimório no turno · consome a ação</small></header>
      {actions.spellcasting.map((entry) => <article key={entry.name}>
        <div className="workspace-catalog-card-heading workspace-attack-card-heading"><strong>{entry.name}</strong></div>
        <div className="workspace-catalog-card-summary"><small>
          {entry.spellcasting?.caster_level != null ? `como ${entry.spellcasting.caster_class} de ${entry.spellcasting.caster_level}º (${entry.spellcasting.tradition})` : ""}
          {entry.frequency ? ` · ${entry.frequency}` : ""}
        </small></div>
        {(entry.spellcasting?.named_spells || []).map((spell) => <div key={spell.mentioned_as}><small>{spell.mentioned_as}: </small>{spell.links.map((link) => gridded
          ? <button key={link.id} type="button" disabled={done || busy || spellBlocked(link.id)} onClick={() => { const armId = arm(`spell:${link.id}`, `${token.name} · ${link.name}`); setPending({ kind: "spell", spellId: link.id, entryName: entry.name, spellName: link.name, armId }); }}>Mirar {link.name} ({link.circle}º){spellCounter(link.id)}</button>
          : <button key={link.id} type="button" disabled={done || busy || spellBlocked(link.id) || !target || (physical && !die)} onClick={() => void conjureNamed(entry.name, link.id, link.name)}>Conjurar {link.name} ({link.circle}º){spellCounter(link.id)}</button>)}</div>)}
        {entry.spellcasting?.caster_level != null && !token.sheet?.spell_repertoire && <ConjurePicker tradition={entry.spellcasting.tradition || ""} tokenId={token.id} target={target} die={die} physical={physical} disabled={done || busy} gridded={gridded} onArm={(spellId, spellName) => { const armId = arm(`spell:${spellId}`, `${token.name} · ${spellName}`); setPending({ kind: "spell", spellId, entryName: entry.name, spellName, armId }); }} onDone={async (name, result) => { setExecResult({ name: `${entry.name} · ${name}`, result }); await onChange(); }} />}
      </article>)}
    </>}
    </fieldset>
    <ParasiteControl state={combat} targetId={token.character_id || token.id} targetType={token.character_id?"character":"token"} onChange={onChange} />{error && <p role="alert">{error}</p>}
    {result?.status === "pending" && <button type="button" title="A rolagem permanece reservada no servidor. Retome a prévia ou passe o turno; não é possível rerrolar." disabled={busy} onClick={() => { setResult(null); retry.current = null; setError(""); window.dispatchEvent(new CustomEvent('omnisvera-attack-target', { detail: {} })); }}>Ocultar prévia · rolagem permanece</button>}
    {!!result?.breakdown?.manual_effects?.length && <p role="alert">Efeito adicional pendente: {result.breakdown.manual_effects.join(", ")}. O dano numérico foi calculado; resolva a proteção e as consequências descritas na ficha. Este efeito não foi aplicado automaticamente.</p>}
  </section>;
}
