import { useEffect, useState } from "react";
import { createWorkspaceToken, getCompanionRoster, listMasterNpcTokens, mediaUrlFromVaultPath, NpcRecord, PlayableCharacterSummary, WorkspaceToken } from "../api";
import NpcDirectory from "../pages/NpcDirectory";
import {extraNpcPinGroups,npcMatchesCharacter,npcPins} from '../npcLibrary';

// Presentation over the existing character, NPC and map-pin stores; no copies.
export default function MasterNpcLibrary({ characters: allCharacters, reservedIds, allies, mapId, onOpenCharacter, onOpenToken, onBack }: {
  characters: PlayableCharacterSummary[]; allies: WorkspaceToken[];
  reservedIds: string[]; mapId: string;
  onOpenCharacter: (id: string) => void; onOpenToken: (token: WorkspaceToken) => void; onBack: () => void;
}) {
  const [tokens, setTokens] = useState<WorkspaceToken[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [placing, setPlacing] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  const [gmIds, setGmIds] = useState<string[]>([]);
  const characters = allCharacters.filter(item => reservedIds.includes(item.id) || gmIds.includes(item.id));
  useEffect(() => {
    let active = true;
    setLoading(true); setError("");
    listMasterNpcTokens().then(rows => { if (active) setTokens(rows); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : "Falha ao carregar NPCs"); })
      .finally(() => { if (active) setLoading(false); });
    getCompanionRoster().then(roster => { if (active) setGmIds(roster.gm_character_ids || []); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : "Falha ao carregar fichas reservadas"); });
    return () => { active = false; };
  }, [revision]);
  const matches = (name: string) => name.toLocaleLowerCase('pt-BR').includes(query.toLocaleLowerCase('pt-BR').trim());
  const pins = [...new Map([...allies, ...tokens].map(token => [token.id, token])).values()];
  const currentMap = mapId || 'default';
  async function placeOnMap(npc: NpcRecord) {
    if (placing !== null) return;
    setPlacing(npc.id); setError(""); setNotice("");
    try {
      const slot = pins.filter(pin => (pin.map_id || 'default') === currentMap).length % 9;
      const token = await createWorkspaceToken({
        token_type: "monster", name: npc.name, map_id: currentMap,
        image_path: npc.portrait_path || undefined, color: "#4f8c9d", visible_to_players: false,
        latitude: 44 + Math.floor(slot / 3) * 4, longitude: 50 + (slot % 3) * 4,
        current_hp: 10, maximum_hp: 10,
        sheet: {
          marker: "\u25CF", role: npc.class_or_role || "NPC", level: 1, armor_class: 10, initiative: 0,
          description: npc.public_description || "", attacks: [], abilities: [], notes: "",
        },
      });
      setTokens(current => [...current, token]);
      setNotice(`${npc.name} colocado no mapa (oculto até você revelar).`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível colocar o NPC no mapa.");
    } finally { setPlacing(null); }
  }
  return <section className="workspace-npc-reference" aria-label="NPCs do Mestre">
    <header className="workspace-reference-actions"><h2>NPCs do Mestre</h2>
      <button type="button" onClick={onBack}>Voltar para a mesa</button>
      <button type="button" onClick={() => window.dispatchEvent(new CustomEvent('omnisvera-open-workspace', { detail: 'maps' }))}>Mapas</button>
    </header>
    <p>Consulta do Mestre. Abrir uma ficha não revela o NPC nem muda sua posição.</p>
    <NpcDirectory mode="gm" embedded isListed={npc=>!characters.some(character=>npcMatchesCharacter(npc,character))} renderActions={npc=>{
      const npcPinList=npcPins(npc,pins);
      const onCurrentMap=npcPinList.filter(pin=>(pin.map_id||'default')===currentMap);
      return <div className="workspace-reference-actions">
        {onCurrentMap.map(pin=><button type="button" key={pin.id} onClick={()=>onOpenToken(pin)}>Abrir ficha no mapa{npcPinList.length>1?` · ${pin.map_id}`:''}</button>)}
        {!onCurrentMap.length && <button type="button" disabled={placing!==null} onClick={()=>void placeOnMap(npc)}>{placing===npc.id?'Colocando…':'Colocar no mapa'}</button>}
        {npcPinList.length>onCurrentMap.length && <small>{npcPinList.length-onCurrentMap.length} pin(s) em outro(s) mapa(s)</small>}
      </div>;
    }}>
      {npcs=>{
      const groups=extraNpcPinGroups(npcs,characters,pins);
      const pinButton=(token:WorkspaceToken,instance=false)=><button type="button" key={token.id} onClick={()=>onOpenToken(token)}>
        {token.image_path&&<img src={mediaUrlFromVaultPath(token.image_path)} alt="" loading="lazy"/>}
        <span><strong>{token.name}</strong><small>{token.sheet?.role||'NPC / criatura'} · {token.map_id||'default'} · {token.visible_to_players?'revelado':'oculto'}{instance?` · ${token.current_hp??'—'}/${token.maximum_hp??'—'} PV`:''}</small></span>
      </button>;
      return <>
      <section className="workspace-npc-roster" aria-label="Fichas reservadas e pins de NPCs">
        <h3>Fichas reservadas e criaturas criadas</h3>
        <input type="search" aria-label="Buscar fichas e pins" placeholder="Buscar fichas e pins" value={query} onChange={event => setQuery(event.target.value)} />
        <button type="button" disabled={loading} onClick={() => setRevision(value => value + 1)}>{loading ? 'Carregando pins…' : 'Atualizar pins'}</button>
        {error && <p role="alert">{error}</p>}
        {notice && <p role="status">{notice}</p>}
        <div className="workspace-npc-reference-list">
          {characters.filter(item => matches(item.name)).map(item => <div className="npc-reserved-entry" key={`character:${item.id}`}><button type="button" onClick={() => onOpenCharacter(item.id)}>
            <strong>{item.name}</strong><small>Ficha reservada · abrir ficha</small>
          </button>{npcs.filter(npc=>npcMatchesCharacter(npc,item)).map(npc=><button type="button" key={npc.id} onClick={()=>window.dispatchEvent(new CustomEvent('omnisvera-open-npc-directory',{detail:npc.id}))}>Histórico</button>)}</div>)}
          {groups.filter(group=>matches(group.name)).map(group=>group.tokens.length===1?pinButton(group.tokens[0]):<details key={group.key} className="npc-pin-group"><summary><strong>{group.name}</strong><small>{group.tokens.length} instâncias</small></summary>{group.tokens.map(token=>pinButton(token,true))}</details>)}
        </div>
        {!loading && !characters.some(item => matches(item.name)) && !groups.some(group=>matches(group.name)) && <p>Nenhuma ficha ou pin encontrado.</p>}
      </section>
      </>;
      }}
    </NpcDirectory>
  </section>;
}
