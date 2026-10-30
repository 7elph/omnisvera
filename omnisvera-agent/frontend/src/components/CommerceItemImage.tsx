import {useState} from 'react';
import {mediaUrlFromVaultPath} from '../api';
import {iconPathForItem} from '../companionIconCatalog';

/** Same image catalog and authenticated media route used by inventory cards. */
export default function CommerceItemImage({name,imagePath}:{name:string;imagePath?:string|null}){
  const [failed,setFailed]=useState<string[]>([]);
  const preferred=mediaUrlFromVaultPath(imagePath||iconPathForItem(name)||'zz_media/ui/icons/items/inventario.jpg');
  const fallback=mediaUrlFromVaultPath('zz_media/ui/icons/items/inventario.jpg');
  const source=failed.includes(preferred)?fallback:preferred;
  return failed.includes(source)?<svg className="commerce-item-image" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14v14H5ZM8 7V4h8v3M5 12h14" fill="none" stroke="currentColor" strokeWidth="2"/></svg>:
    <img className="commerce-item-image" src={source} alt={`Imagem de ${name}`} loading="lazy" onError={()=>setFailed([...failed,source])} />;
}
