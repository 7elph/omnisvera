import type {WorkspaceToken} from '../api';
import './mapLoot.css';

export function canCollectMapLoot(token:WorkspaceToken):boolean {
  return token.token_type==='monster' && token.current_hp!=null && token.current_hp<=0
    && !token.sheet?.loot_collected && !token.sheet?.summon && !token.sheet?.disintegrated
    && !token.sheet?.reanimated_by && /^[^(]*[A-Z]/i.test(token.sheet?.treasure||'');
}

export default function MapLootChest({token,left,top,disabled,onCollect}:{
  token:WorkspaceToken;left:number;top:number;disabled:boolean;onCollect:()=>void;
}) {
  if(!canCollectMapLoot(token))return null;
  return <button type="button" className="workspace-map-loot-chest" style={{left:`${left}%`,top:`${top}%`}}
    disabled={disabled} aria-label={`Saquear espólio de ${token.name}`} title={`Repartir espólio de ${token.name} entre o grupo`}
    onPointerDown={event=>event.stopPropagation()} onClick={event=>{event.stopPropagation();onCollect();}}>
    <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M3 11V8a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v3M3 11h18v9H3zM7 4v16M17 4v16"/>
      <path d="M10 10h4v5h-4z" fill="currentColor"/>
    </svg>
  </button>;
}
