import type {CombatEffect,WorkspaceToken,PlayableCharacterSummary} from '../api';
import {mediaUrlFromVaultPath} from '../api';
import type {MapGrid} from '../spatialGrid';
type Area={map_id:string;x_m:number;y_m:number;width_m:number;height_m:number};
/** Derived visuals only: images are not combatants and never gain turns/occupancy. */
export default function MapSpellEffects({effects,mapId,grid,tokens,characters}:{effects:CombatEffect[];mapId:string;grid?:MapGrid;tokens:WorkspaceToken[];characters:PlayableCharacterSummary[]}){
 if(!grid)return null;
 const dx=(100-grid.origin_x)/grid.cols,dy=(100-grid.origin_y)/grid.rows;
 return <svg className="workspace-map-spell-effects" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="Efeitos mágicos no mapa">
  {effects.map(effect=>{
   const area=(effect as CombatEffect&{web_area?:Area|null}).web_area;
   if(area?.map_id===mapId)return <rect key={effect.id} aria-label="Área de Teia" x={grid.origin_x+area.x_m/grid.cell_size_m*dx} y={grid.origin_y+area.y_m/grid.cell_size_m*dy} width={area.width_m/grid.cell_size_m*dx} height={area.height_m/grid.cell_size_m*dy} fill="rgba(255,255,255,.20)" stroke="rgba(255,255,255,.75)" strokeWidth=".15" strokeDasharray=".6 .3"/>;
   if(effect.spell!=='reflexos'||!effect.images_remaining)return null;
   const pin=tokens.find(t=>effect.target_type==='character'?t.character_id===effect.target_id:t.id===effect.target_id);
   if(!pin?.grid_position||pin.map_id!==mapId)return null;
   const count=effect.images_remaining;
   const image=mediaUrlFromVaultPath(pin.image_path||characters.find(c=>c.id===pin.character_id)?.portrait);
   return <g key={effect.id} aria-label={`${effect.images_remaining} reflexos de Dorn`} opacity=".6">
    {Array.from({length:count},(_,i)=>{
     const angle=(i/count)*Math.PI*2,x=grid.origin_x+(pin.grid_position!.cell_x+.5)*dx+Math.cos(angle)*dx*1.2,y=grid.origin_y+(pin.grid_position!.cell_y+.5)*dy+Math.sin(angle)*dy*1.2;
     return <g key={i}><rect x={x-dx/2} y={y-dy/2} width={dx} height={dy} fill="white" fillOpacity=".12" stroke="white" strokeWidth=".15"/>{image&&<image href={image} x={x-dx/2} y={y-dy/2} width={dx} height={dy} preserveAspectRatio="xMidYMid slice"/>}</g>;
    })}
   </g>;
  })}
 </svg>;
}
