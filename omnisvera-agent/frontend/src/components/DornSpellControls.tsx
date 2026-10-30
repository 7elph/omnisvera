import { useRef, useState } from 'react';
import { CombatEffectsState, WorkspaceToken, newDiceRequestId, sendCombatEffectCommand } from '../api';
import { mediaUrlFromVaultPath } from '../api';
import ActionControlCard from './ActionControlCard';
import { nativeSpellRevision } from './nativeSpellRevision';
import type { NativeActionContract } from '../api';

export default function DornSpellControls({ spell, tokens, combat, onChange, onClose, ability }: {
  spell: string; tokens: WorkspaceToken[]; combat: CombatEffectsState; onChange: () => Promise<void>; onClose: () => void;
  ability?:{description?:string|null;image_path?:string|null;action_contract?:NativeActionContract};
}) {
  const [targets, setTargets] = useState<string[]>([]);
  const [distance, setDistance] = useState('0');
  const [weight, setWeight] = useState('');
  const [unwilling, setUnwilling] = useState(false);
  const [shape, setShape] = useState('line');
  const [contacts, setContacts] = useState<Record<string, number>>({});
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [outcome, setOutcome] = useState('');
  const lock = useRef(false);
  const retry = useRef<{ fingerprint: string; id: string } | null>(null);
  const automated=['reflexos','teia','forca-arcana','dissipar-magia'].includes(spell);
  const titles:Record<string,string>={'levitacao':'Levitação','escuridao':'Escuridão','relampago':'Relâmpago','reflexos':'Reflexos','teia':'Teia','forca-arcana':'Força Arcana','dissipar-magia':'Dissipar Magia'};
  const descriptions:Record<string,string>={'reflexos':'Em si mesmo: 1d4+1 imagens, 90% de interceptação (regra da campanha) por acerto. Dano de área não é interceptado. Duração em tempo ficcional.','teia':'Escolha um pin: sua célula será o canto inicial da área de chão 3×3 m, altura 6 m. Ocupantes, penalidades e movimento são calculados pelo grid.','forca-arcana':'Um receptor vivo adjacente (Dorn também é permitido). Bônus calculado pela FOR original, sem itens ou outras magias.','dissipar-magia':'Escolha magia arcana ativa com círculo e nível de origem cadastrados. Backend verifica alcance, rola e dissipa em caso de sucesso.'};
  async function cast() {
    if (lock.current) return;
    let revision;
    try { revision=nativeSpellRevision(spell, ability?.action_contract); }
    catch(reason) { setOutcome(reason instanceof Error?reason.message:'Contrato inválido'); return; }
    lock.current = true; setBusy(true); setOutcome('');
    const payload = automated ? {spell_id:spell,...(spell==='dissipar-magia'?{effect_id:targets[0]}:{targets:targets.map(id=>({type:'token',id}))})} : { spell_id: spell, targets: targets.map(id => ({type: 'token', id, contacts: contacts[id] || 1})), distance_meters: Number(distance), weight_kg: Number(weight), unwilling, shape, position_confirmed: confirmed };
    Object.assign(payload, revision);
    const fingerprint = JSON.stringify([payload, combat.version]);
    let applied = false;
    if (retry.current?.fingerprint !== fingerprint) retry.current = {fingerprint, id: newDiceRequestId('dorn-spell')};
    try {
      const state = await sendCombatEffectCommand({request_id: retry.current.id, expected_version: combat.version, action: 'dorn_spell_cast', payload});
      applied = true;
      retry.current = null;
      const result = state.protocol_result as unknown as {spell: string; results: Array<{target: string; damage?: number; hp_before?: number; hp_after?: number; success?:boolean;total?:number;difficulty?:number; saving_throw?: {success: boolean; total?: number}; contact_saves?: Array<{success: boolean; total?: number}>}>};
      if(spell==='dissipar-magia')setOutcome(`${result.spell}: ${result.results.map(r=>`${r.target} · ${r.total} contra ${r.difficulty}: ${r.success?'dissipada':'resistiu'}`).join('; ')}`);
      else
      setOutcome(`${result.spell}: ${result.results.map(r => `${r.target}${(r.contact_saves || (r.saving_throw ? [r.saving_throw] : [])).map(s => ` · JP ${s.total ?? '—'}: ${s.success ? 'resistiu' : 'falhou'}`).join('')}${r.damage !== undefined ? ` · dano ${r.damage} · PV ${r.hp_before}→${r.hp_after}` : r.saving_throw?.success ? '' : ' · efeito aplicado'}`).join('; ')}`);
      await onChange();
    } catch (error) { if (applied) setOutcome(current => `${current} · Conjuração aplicada; a tela não sincronizou. Não conjure novamente.`); else setOutcome(error instanceof Error ? error.message : 'Falha na conjuração'); }
    finally { lock.current = false; setBusy(false); }
  }
  return <ActionControlCard title={titles[spell]} label="Conjuração do Tomo Arcano" onClose={onClose}
    icon={ability?.image_path ? mediaUrlFromVaultPath(ability.image_path) || undefined : undefined}
    description={ability?.description || (automated?descriptions[spell]:spell === 'levitacao' ? 'Um receptor. Limite 50 kg/nível; alcance 20 m/nível. Vertical até 2 m por rodada.' : spell === 'escuridao' ? 'Imobilização por até 3 turnos do alvo: JP normal liberta; falha passa o turno. Raio 4,5 m, alcance 10 m/nível. Marque os ocupantes, inclusive aliados.' : 'Ponto inicial até 40 + 10 m/nível. Selecione todos atingidos, inclusive por reflexão. Dano máximo por criatura não se acumula.')}
    summary={<small>{automated?'Validação automática pelo backend':'Declaração de área e alcance'} · Tomo Arcano</small>}>
    {!automated && <label>Distância declarada (m)<input type="number" min="0" value={distance} onChange={e => setDistance(e.target.value)} /></label>}
    {spell === 'levitacao' && <><label>Peso do receptor (kg)<input type="number" min="1" value={weight} onChange={e => setWeight(e.target.value)} /></label><label><input type="checkbox" checked={unwilling} onChange={e => setUnwilling(e.target.checked)} />Receptor não aceita · JPC</label></>}
    {spell === 'relampago' && <label>Forma<select value={shape} onChange={e => setShape(e.target.value)}><option value="line">Raio 1,5 × 24 m</option><option value="forked">Bifurcado 3 × 12 m</option></select></label>}
    {spell==='dissipar-magia'?<label>Efeito arcano<select aria-label="Efeito a dissipar" value={targets[0] || ''} onChange={e=>setTargets(e.target.value?[e.target.value]:[])}><option value="">Selecione</option>{combat.effects.filter(e=>e.magic_type==='arcane' && e.spell_circle && e.caster_level && !e.environmental).map(e=><option key={e.id} value={e.id}>{e.label} · {e.target_id}</option>)}</select></label>:spell!=='reflexos' && <label>Receptores<select multiple aria-label="Alvos da magia" value={targets} onChange={e => setTargets(Array.from(e.target.selectedOptions, option => option.value))}>{tokens.filter(t => t.token_type !== 'location' && (t.current_hp || 0) > 0).map(t => <option key={t.id} value={t.id}>{t.name}</option>)}</select></label>}
    {spell === 'relampago' && targets.map(id => <label key={id}>Contatos do raio · {tokens.find(t => t.id === id)?.name}<input type="number" min="1" max="10" value={contacts[id] || 1} onChange={e => setContacts({...contacts, [id]: Number(e.target.value)})} /></label>)}
    {!automated && <label><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} />Confirmo alcance, área/posição e peso conforme o Tomo</label>}
    <button disabled={busy || (!automated && !confirmed) || (spell!=='reflexos' && !targets.length) || (automated && spell!=='reflexos' && targets.length!==1) || (spell === 'levitacao' && (!weight || targets.length !== 1))} onClick={() => void cast()}>Conjurar · resolver automaticamente</button>
    {outcome && <p role="status">{outcome}</p>}
  </ActionControlCard>;
}
