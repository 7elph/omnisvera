import { useState } from 'react';
import type { Cell, MapGrid } from '../spatialGrid';
import { configureMapGrid } from '../spatialCommands';
import './logicalGrid.css';

export function LogicalGrid({grid,destination}:{grid:MapGrid;destination:Cell|null}) {
  const dx=(100-grid.origin_x)/grid.cols,dy=(100-grid.origin_y)/grid.rows;
  return <svg className="logical-map-grid" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label={`Grid lógico ${grid.cols} por ${grid.rows}`}>
    {Array.from({length:grid.cols+1},(_,x)=><line key={`x${x}`} x1={grid.origin_x+x*dx} x2={grid.origin_x+x*dx} y1={grid.origin_y} y2={100}/>)}
    {Array.from({length:grid.rows+1},(_,y)=><line key={`y${y}`} y1={grid.origin_y+y*dy} y2={grid.origin_y+y*dy} x1={grid.origin_x} x2={100}/>)}
    {destination && <rect className="logical-grid-destination" x={grid.origin_x+destination[0]*dx} y={grid.origin_y+destination[1]*dy} width={dx} height={dy}/>}
  </svg>;
}

export function GridConfiguration({mapId,grid,disabled,onChange}:{mapId:string;grid?:MapGrid;disabled:boolean;onChange:()=>Promise<unknown>}) {
  const [error,setError]=useState(''); const [pending,setPending]=useState(false);
  return <details className="logical-grid-controls"><summary>{grid ? `Grid ${grid.cols}×${grid.rows} · ${grid.cell_size_m} m/célula` : 'Configurar grid lógico'}</summary>
    <p>Diagonal provisória, configurável; a imagem não define as regras. Origem em % da imagem. Calibre fora do combate.</p>
    <form key={`${mapId}:${grid?.version}`} onSubmit={async event=>{event.preventDefault();const data=new FormData(event.currentTarget);setPending(true);setError('');try {
      await configureMapGrid(mapId,{cols:Number(data.get('cols')),rows:Number(data.get('rows')),cell_size_m:Number(data.get('scale')),origin_x:Number(data.get('x')),origin_y:Number(data.get('y')),distance_rule:data.get('rule') as MapGrid['distance_rule']},grid?.version || 0);await onChange();
    } catch(reason){setError(reason instanceof Error?reason.message:'Não foi possível configurar');} finally{setPending(false);}}}>
      {[['cols','Colunas',grid?.cols || 32,1,200],['rows','Linhas',grid?.rows || 24,1,200],['scale','Metros/célula',grid?.cell_size_m || 1.5,.01,10000],['x','Origem X (%)',grid?.origin_x || 0,0,99],['y','Origem Y (%)',grid?.origin_y || 0,0,99]].map(([name,label,value,min,max])=><label key={name}>{label}<input name={String(name)} type="number" step={name==='cols'||name==='rows'?1:.01} defaultValue={value} min={min} max={max} required disabled={disabled||pending}/></label>)}
      <label>Distância (provisória)<select name="rule" defaultValue={grid?.distance_rule || 'chebyshev'} disabled={disabled||pending}><option value="chebyshev">Diagonal = 1 célula</option><option value="manhattan">Diagonal = 2 células</option></select></label>
      <button disabled={disabled||pending}>Salvar grid</button>
    </form>{error&&<p role="alert">{error}</p>}
  </details>;
}
