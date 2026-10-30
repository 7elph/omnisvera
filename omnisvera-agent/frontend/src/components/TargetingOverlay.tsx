import type { MapGrid } from "../spatialGrid";

export type TargetingRing = {
  origin: { cell_x: number; cell_y: number };
  rangeCells: number;
  path?: [number, number][];
  areaCells?: [number, number][];
};

export function cellCenterPct(grid: MapGrid, cell: [number, number]): { x: number; y: number } {
  const dx = (100 - grid.origin_x) / grid.cols, dy = (100 - grid.origin_y) / grid.rows;
  return { x: grid.origin_x + (cell[0] + 0.5) * dx, y: grid.origin_y + (cell[1] + 0.5) * dy };
}

export default function TargetingOverlay({ grid, ring }: { grid: MapGrid; ring: TargetingRing }) {
  const dx = (100 - grid.origin_x) / grid.cols, dy = (100 - grid.origin_y) / grid.rows;
  const center = cellCenterPct(grid, [ring.origin.cell_x, ring.origin.cell_y]);
  const points = (ring.path || []).map((cell) => {
    const point = cellCenterPct(grid, cell);
    return `${point.x},${point.y}`;
  }).join(" ");
  const rx=ring.rangeCells*dx, ry=ring.rangeCells*dy;
  return <svg className="targeting-overlay" width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="Alcance da ação">
    {grid.distance_rule==='manhattan'
      ? <polygon className="targeting-area" points={`${center.x},${center.y-ry} ${center.x+rx},${center.y} ${center.x},${center.y+ry} ${center.x-rx},${center.y}`} />
      : <rect className="targeting-area" x={center.x-rx-dx/2} y={center.y-ry-dy/2} width={2*rx+dx} height={2*ry+dy} />}
    <ellipse cx={center.x} cy={center.y} rx={ring.rangeCells * dx} ry={ring.rangeCells * dy} className="targeting-ring" />
    {(ring.areaCells || []).map(([x,y])=><rect key={`${x}:${y}`} className="targeting-cross-cell" x={grid.origin_x+x*dx} y={grid.origin_y+y*dy} width={dx} height={dy} />)}
    {points && <polyline points={points} className="targeting-path" />}
    {(ring.path || []).slice(1).map((cell, index) => {
      const point = cellCenterPct(grid, cell);
      return <circle key={index} cx={point.x} cy={point.y} r={0.6} className="targeting-step" />;
    })}
  </svg>;
}
