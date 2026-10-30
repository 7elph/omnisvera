import {getAccessToken} from './api';
import {readJson} from './readJson';
import type {SpriteAsset,SpriteMetadata} from './spriteAnimation';
const base=import.meta.env.VITE_API_BASE_URL||'';
export const spriteImageUrl=(asset:SpriteAsset)=>`${base}/workspace/sprites/${encodeURIComponent(asset.id)}/${asset.image_hash}.png?token=${encodeURIComponent(getAccessToken())}`;
export async function spriteRequest<T>(path:string,body?:unknown):Promise<T>{
  if(body===undefined)return readJson<T>(`${base}${path}`,{'X-Omnisvera-Token':getAccessToken()},'Falha ao carregar sprites');
  const response=await fetch(`${base}${path}`,{method:'POST',headers:{'X-Omnisvera-Token':getAccessToken(),'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!response.ok)throw new Error((await response.json().catch(()=>null))?.detail||'Falha ao salvar sprite');
  return response.json();
}
export const listSprites=()=>spriteRequest<SpriteAsset[]>('/gm/sprites');
export const saveSprite=(payload:{request_id:string;asset_id?:string;expected_version:number;name:string;metadata:SpriteMetadata;png_base64?:string})=>spriteRequest<SpriteAsset>('/gm/sprites',payload);
export const bindSprite=(entity_type:'character'|'token',entity_id:string,asset_id:string|null,request_id:string)=>spriteRequest('/gm/sprites/binding',{entity_type,entity_id,asset_id,request_id});
export async function exportSprite(asset:SpriteAsset){
  const response=await fetch(`${base}/gm/sprites/${asset.id}/export`,{headers:{'X-Omnisvera-Token':getAccessToken()}});
  if(!response.ok)throw new Error('Falha ao exportar sprite');
  const url=URL.createObjectURL(await response.blob());const link=document.createElement('a');link.href=url;link.download=`sprite-${asset.id}.zip`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
