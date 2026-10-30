import type {NpcRecord,PlayableCharacterSummary,WorkspaceToken} from './api';

/** Identity projection only: never merge/delete NPC records or combat instances. */
function identity(value:string){return value.split(/\s+[—–]\s+/)[0].replace(/^unidade\s+/i,'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');}
export function npcMatchesCharacter(npc:NpcRecord,character:PlayableCharacterSummary){
  const source=(npc.source_path||'').split('/').pop()?.replace(/\.md$/i,'')||'';
  return [npc.name,source].filter(Boolean).some(name=>identity(name)===identity(character.name));
}
export function npcPins(npc:NpcRecord,pins:WorkspaceToken[]){
  return pins.filter(pin=>!pin.sheet?.summon&&identity(pin.name)===identity(npc.name));
}
export function extraNpcPinGroups(npcs:NpcRecord[],characters:PlayableCharacterSummary[],pins:WorkspaceToken[]){
  const groups=new Map<string,WorkspaceToken[]>();
  for(const pin of new Map(pins.map(token=>[token.id,token])).values()){
    const matching=npcs.filter(npc=>npcPins(npc,[pin]).length);
    if(matching.length===1||characters.some(character=>identity(character.name)===identity(pin.name)))continue;
    const key=identity(pin.name)||pin.id;
    groups.set(key,[...(groups.get(key)||[]),pin]);
  }
  return [...groups.entries()].map(([key,tokens])=>({key,name:tokens[0].name,tokens}));
}
