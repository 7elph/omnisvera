import { useEffect, useState } from 'react';
import { getCharacterActionManifest, getPlayableCharacter, mediaUrlFromVaultPath } from '../api';
import type { NativeActionManifest, PlayableCharacter, PlayableCharacterSummary } from '../api';
import { characterActionReference, referenceWithManifest, searchText } from '../actionReference';
import SheetDetail from './SheetDetail';
import { iconPathForItem } from '../companionIconCatalog';

export default function CharacterActionReference({ characters, initialId }: { characters: PlayableCharacterSummary[]; initialId?: string }) {
  const [selected, setSelected] = useState(characters.some(item => item.id === initialId) ? initialId! : characters[0]?.id || '');
  const [sheet, setSheet] = useState<PlayableCharacter | null>(null);
  const [manifest, setManifest] = useState<NativeActionManifest | null>(null);
  const [manifestError, setManifestError] = useState('');
  const [query, setQuery] = useState(''), [category, setCategory] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let cancelled = false;
    setSheet(null); setManifest(null); setError(''); setManifestError('');
    setBusy(Boolean(selected));
    if (!selected) return;
    void Promise.allSettled([getPlayableCharacter(selected, true), getCharacterActionManifest(selected)]).then(([sheetResult, actionResult]) => {
      if (cancelled) return;
      if (sheetResult.status === 'fulfilled') setSheet(sheetResult.value);
      else setError(sheetResult.reason instanceof Error ? sheetResult.reason.message : 'Falha ao consultar ficha');
      if (actionResult.status === 'fulfilled' && actionResult.value.character_id === selected) setManifest(actionResult.value);
      else setManifestError('Não foi possível verificar a automação. As descrições continuam disponíveis.');
      setBusy(false);
    });
    return () => { cancelled = true; };
  }, [selected, revision]);
  const cards = sheet?.definition.id === selected ? referenceWithManifest(characterActionReference(sheet), manifest) : [];
  const visible = cards.filter(card => (!category || card.category === category) && searchText(`${card.name} ${card.description}`).includes(searchText(query.trim())));
  return <section className="workspace-action-reference" aria-label="Cola de ações" aria-busy={busy}>
    <p>Consulta somente-leitura. “Comando integrado” indica um executor nativo; a comprovação depende dos ensaios da ação.</p>
    <label>Personagem<select aria-label="Personagem da cola de ações" value={selected} onChange={event => { setSelected(event.target.value); setCategory(''); setQuery(''); }}>
      <option value="">Selecionar personagem</option>{characters.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
    </select></label>
    <label>Buscar<input type="search" aria-label="Buscar habilidade ou magia" placeholder="Nome ou trecho das regras" value={query} onChange={event => setQuery(event.target.value)} /></label>
    <label>Tipo<select aria-label="Tipo de ação na consulta" value={category} onChange={event => setCategory(event.target.value)}><option value="">Todos os tipos</option>{[...new Set(cards.map(card => card.category))].map(value => <option key={value}>{value}</option>)}</select></label>
    <button type="button" disabled={busy || !selected} onClick={() => setRevision(value => value + 1)}>Atualizar consulta</button>
    {error && <p role="alert">{error}</p>}
    {manifestError && <p role="status">{manifestError}</p>}
    {busy ? <p role="status">Carregando ações…</p> : <>
      <small>{visible.length}/{cards.length} opções · usos são uma fotografia da ficha; clique em Atualizar consulta para conferir alterações.</small>
      <div className="workspace-action-reference-list">{visible.map(card => <article key={card.id}>
        <SheetDetail key={`${selected}:${card.id}`} title={card.name} description={card.description} icon={mediaUrlFromVaultPath(card.image_path || iconPathForItem(card.name, card.category)) || undefined}>{card.name}</SheetDetail>
        <small>{card.category} · {card.status}</small>
      </article>)}</div>
      {selected && !visible.length && !error && <p>Nenhuma opção encontrada nesta consulta.</p>}
    </>}
  </section>;
}
