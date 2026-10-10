import { useEffect, useRef, useState } from 'react';
import { GameScene, getCombatEffects, getSessionWorkspace, listGameSessions, updateGameSessionStatus, newDiceRequestId, sendCombatEffectCommand } from '../api';

/** Native scene notes and native encounter command; never rendered in player mode. */
export default function Session7PreparationPanel({ scene }: { scene: GameScene }) {
  const [dorn, setDorn] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [sessionStatus, setSessionStatus] = useState('');
  const lock = useRef(false);
  const retry = useRef<{ key: string; id: string } | null>(null);
  const warehouse = scene.request_id === 'session7-scene-06';
  useEffect(() => {
    let cancelled = false;
    setSessionStatus('');
    void listGameSessions().then(sessions => {
      if (!cancelled) setSessionStatus(sessions.find(s => s.id === scene.session_id)?.status || '');
    }).catch(error => { if (!cancelled) setMessage(error instanceof Error ? error.message : 'Falha ao carregar sessão'); });
    return () => { cancelled = true; };
  }, [scene.session_id, scene.status]);
  async function changeSession(status: 'active' | 'completed') {
    if (lock.current || !scene.session_id) return;
    lock.current = true; setBusy(true); setMessage('');
    try {
      if ((await getCombatEffects()).encounter?.active) throw new Error('Encerre o combate salvo primeiro; ele não será alterado por este botão.');
      const session = await updateGameSessionStatus(scene.session_id, status);
      setSessionStatus(session.status);
      setMessage(status === 'active' ? 'Sessão 7 iniciada. Agora abra a cena preparada na Mesa.' : 'Sessão 7 encerrada; estado preservado.');
      window.dispatchEvent(new CustomEvent('omnisvera-open-scene', { detail: scene.id }));
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Falha ao atualizar sessão'); }
    finally { lock.current = false; setBusy(false); }
  }
  async function start() {
    if (lock.current || !scene.map_id || scene.status !== 'active') return;
    lock.current = true; setBusy(true); setMessage('');
    try {
      const [combat, workspace] = await Promise.all([getCombatEffects(), getSessionWorkspace(scene.map_id)]);
      if (combat.encounter?.active) throw new Error('Encerre o combate existente; ele não será substituído.');
      const roster = ['vezemir', 'morthak', 'raziel', ...(dorn ? ['dorn7'] : [])];
      const participants = roster.map((id, index) => ({ target_type: 'character', target_id: id, name: id === 'dorn7' ? 'Dorn' : id[0].toUpperCase() + id.slice(1), initiative: 20 - index }));
      participants.push(...workspace.tokens.filter(t => t.token_type === 'monster' && t.sheet?.marker === 'session7' && !t.name.includes('reserva')).map((t, index) => ({ target_type: 'token', target_id: t.id, name: t.name, initiative: 12 - index })));
      participants.push(...workspace.tokens.filter(t => t.sheet?.summon?.caster === 'morthak').map(t => ({ target_type: 'token', target_id: t.id, name: t.name, initiative: 19 })));
      const payload = { title: 'Âncora Partida · provas e captura', map_id: scene.map_id, participants, battle_mode: true };
      const key = JSON.stringify([payload, combat.version]);
      if (retry.current?.key !== key) retry.current = { key, id: newDiceRequestId('session7-encounter') };
      await sendCombatEffectCommand({ request_id: retry.current.id, expected_version: combat.version, action: 'start', payload });
      retry.current = null;
      setMessage('Encontro iniciado. A ordem inicial é uma proposta; ajuste pelo painel nativo de combate.');
      window.dispatchEvent(new CustomEvent('omnisvera-scene-updated'));
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Falha ao iniciar encontro'); }
    finally { lock.current = false; setBusy(false); }
  }
  return <section className="scene-section">
    <header><h3>Referência rápida do Mestre · S7</h3></header>
    <div className="scene-inline-form"><button disabled={busy || !sessionStatus || !['planned', 'paused'].includes(sessionStatus)} onClick={() => void changeSession('active')}>Iniciar Sessão 7</button><button disabled={busy || sessionStatus !== 'active'} onClick={() => void changeSession('completed')}>Encerrar Sessão 7</button></div>
    {scene.elements.filter(e => e.private_description).map(e => <details key={e.id}><summary>{e.title} · acesso e consequência</summary><p>{e.private_description}</p></details>)}
    {warehouse && <><label><input type="checkbox" checked={dorn} onChange={e => setDorn(e.target.checked)} /> Incluir Dorn como aliado</label>
      <button disabled={busy || scene.status !== 'active'} onClick={() => void start()}>Iniciar encontro preparado</button>
      <small>Somente se houver confronto. Abra esta cena na Mesa primeiro. Negociação e retirada continuam válidas.</small></>}
    {message && <p role="status">{message}</p>}
  </section>;
}
