export type Cell = [number, number];
export type MapGrid = { map_id: string; grid_type: 'square'; cols: number; rows: number; cell_size_m: number; origin_x: number; origin_y: number; distance_rule: 'chebyshev' | 'manhattan'; provisional: number; version: number };
export type GridPosition = { map_id: string; token_id: string; cell_x: number; cell_y: number; footprint_w: number; footprint_h: number; version: number };
export type SpatialCommand = { request_id: string; token_id: string; mode: 'GM_REPOSITION' | 'COMBAT_MOVE'; path: Cell[]; expected_position_version: number; expected_grid_version: number; expected_combat_version?: number };
export type SpatialResult = { position: GridPosition; longitude: number; latitude: number; combat_version: number; ledger_id: number; movement: { budget_m: number; spent_m: number; turn_key: unknown[] } | null };

export function cellAt(grid: MapGrid, longitude: number, latitude: number): Cell {
  return [Math.max(0,Math.min(grid.cols-1,Math.floor((longitude-grid.origin_x)/(100-grid.origin_x)*grid.cols))),
    Math.max(0,Math.min(grid.rows-1,Math.floor((latitude-grid.origin_y)/(100-grid.origin_y)*grid.rows)))];
}
export function cellCenter(grid: MapGrid, cell: Cell, width=1, height=1) {
  return {longitude:grid.origin_x+(cell[0]+width/2)*(100-grid.origin_x)/grid.cols,
    latitude:grid.origin_y+(cell[1]+height/2)*(100-grid.origin_y)/grid.rows};
}
export function simplePath(start: Cell, end: Cell, rule: MapGrid['distance_rule']): Cell[] {
  const path: Cell[] = [[...start]];
  let [x,y] = start;
  while(x!==end[0] || y!==end[1]) {
    if(rule==='chebyshev') { x+=Math.sign(end[0]-x); y+=Math.sign(end[1]-y); }
    else if(x!==end[0]) x+=Math.sign(end[0]-x); else y+=Math.sign(end[1]-y);
    path.push([x,y]);
  }
  return path;
}
export function tokenProjection(grid: MapGrid | undefined, position: GridPosition | undefined, fallback: {longitude:number;latitude:number}) {
  return grid && position?.map_id===grid.map_id ? cellCenter(grid,[position.cell_x,position.cell_y],position.footprint_w,position.footprint_h) : fallback;
}
