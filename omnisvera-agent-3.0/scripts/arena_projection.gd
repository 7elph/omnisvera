extends Node2D
var cols: int=12
var rows: int=8
var origin=Vector2.ZERO
var extent=Vector2(800,500)
func grid_to_world(cell: Vector2i) -> Vector2:
	return origin+Vector2((cell.x+.5)*extent.x/maxi(cols,1),(cell.y+.5)*extent.y/maxi(rows,1))
func world_to_grid(point: Vector2) -> Vector2i:
	return Vector2i(floori((point.x-origin.x)/maxf(extent.x,1)*cols),floori((point.y-origin.y)/maxf(extent.y,1)*rows))
