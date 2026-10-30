type Pending = { current: { key: string; id: string } | null };
type Command = { request_id: string; map_id?: string; mode: 'reuse' | 'replace'; target_type?: 'token'; target_id?: string };
type Existing = { existing?: boolean; needs_replacement?: boolean; existing_token_id?: string;
  token?: { id: string; map_id?: string; visible_to_players?: boolean } };

/** One card action, two explicit native commands. Keep an uncertain replacement
 * ID until its receipt returns; inspection/cancellation never spends a use. */
export async function invokeSkeleton<T>({ actor, ability, mapId, pending, newId, invoke, confirmReplacement }: {
  actor: string; ability: string; mapId?: string; pending: Pending; newId: () => string;
  invoke: (command: Command) => Promise<T>; confirmReplacement: () => boolean;
}): Promise<T | null> {
  let previous: unknown;
  try { previous = JSON.parse(pending.current?.key || 'null'); } catch { previous = null; }
  const retry = Array.isArray(previous) && previous.length === 5 && previous[0] === 'skeleton'
    && previous[1] === actor && previous[2] === ability && previous[3] === 'replace' && typeof previous[4] === 'string' && previous[4];
  const send = async (mode: 'reuse' | 'replace', tokenId = '') => {
    const key = JSON.stringify(['skeleton', actor, ability, mode, tokenId]);
    if (pending.current?.key !== key) pending.current = { key, id: newId() };
    const receipt = pending.current;
    try {
      const result = await invoke({ request_id: receipt.id, map_id: mapId, mode,
        ...(mode === 'replace' ? { target_type: 'token' as const, target_id: tokenId } : {}) });
      if (pending.current === receipt) pending.current = null;
      return result;
    } catch (error) {
      const status = Number((error as { status?: number } | null)?.status);
      // A rejected command did not commit. Reinspect on the next click, rather
      // than stranding the card on an obsolete summon ID. Uncertain replies keep
      // the same ID so their successful receipt can be recovered safely.
      if (status >= 400 && status < 500 && status !== 408 && status !== 429 && pending.current === receipt) pending.current = null;
      throw error;
    }
  };
  if (retry && Array.isArray(previous)) return send('replace', String(previous[4]));
  const result = await send('reuse');
  const existing = result as Existing;
  if (existing.existing && (existing.needs_replacement || (existing.token && existing.token.map_id !== mapId))) {
    const tokenId = existing.existing_token_id || existing.token?.id;
    if (!tokenId) throw Error('Não foi possível identificar a invocação anterior. Atualize a ficha.');
    if (!confirmReplacement()) return null;
    return send('replace', tokenId);
  }
  return result;
}
