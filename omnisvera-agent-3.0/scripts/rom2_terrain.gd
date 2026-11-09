extends Node2D
var model: Dictionary = {}
var textures: Dictionary = {}
var atlas: Texture2D
var ordered: Array = []
## The ~7000 tiles and props are painted once into a texture (one draw per frame instead of thousands).
const MARGIN_TOP = 320
var baked = SubViewport.new()
var painter = Node2D.new()
var picture = Sprite2D.new()
var props = Node2D.new()   # trees, houses...: one sprite each, sorted by depth with the characters
var base_templates: Dictionary = {}  # prop name -> {name, atlas, rect, pivot}: what the editor can place
signal edited  # tiles, heights or props changed (the map rebuilds its blocked cells)
func _ready() -> void:
	var path = "res://assets/rom2_local/map.json"
	if not FileAccess.file_exists(path): return
	model = JSON.parse_string(FileAccess.get_file_as_string(path))
	atlas = texture(model.visuals.tiles_atlas)
	ordered = model.visuals.placements.duplicate(true)
	ordered.sort_custom(func(a,b): return float(a.y)<float(b.y))
	for placement in ordered: texture(placement.atlas)
	baked.transparent_bg = true
	baked.disable_3d = true
	baked.size = Vector2i(mini(int(model.width) * 32, 8192), mini(int(model.height) * 32 + MARGIN_TOP + 32, 8192))
	painter.position = Vector2(0, MARGIN_TOP)
	painter.draw.connect(func(): _paint(painter))
	baked.add_child(painter)
	add_child(baked)
	picture.centered = false
	picture.position = Vector2(0, -MARGIN_TOP)
	picture.texture = baked.get_texture()
	add_child(picture)
	add_child(props)
	for placement in ordered:
		if not base_templates.has(str(placement.get("name", ""))):
			base_templates[str(placement.get("name", ""))] = {"name": placement.get("name", ""), "atlas": placement.atlas, "rect": placement.rect, "pivot": placement.pivot}
	_rebuild_props()
	_rebake()

## One sprite per prop, depth-sorted with the characters.
func _rebuild_props() -> void:
	for child in props.get_children():
		child.queue_free()
	for placement in ordered:
		var sprite = Sprite2D.new()
		var region: Array = placement.rect
		var point = prop_point(placement)
		sprite.texture = textures[placement.atlas]
		sprite.region_enabled = true
		sprite.region_rect = Rect2(region[0], region[1], region[2], region[3])
		sprite.centered = false
		sprite.position = point - Vector2(placement.pivot[0], placement.pivot[1])
		sprite.z_as_relative = false
		sprite.z_index = clampi(prop_depth(placement), -4000, 4000)  # same rule as the characters (z = feet y)
		props.add_child(sprite)

func _rebake() -> void:
	baked.render_target_update_mode = SubViewport.UPDATE_ONCE
	painter.queue_redraw()
func cell_to_world(cell: Vector2i) -> Vector2:
	return Vector2((cell.x+.5)*32,(cell.y+.5)*32-height_at(cell.x+.5,cell.y+.5))
func world_to_cell(point: Vector2) -> Vector2i:
	var x = floori(point.x / 32)
	var fraction_x = point.x / 32
	# At a fixed X, the tile edges are linearly interpolated by the renderer.
	# Test those exact intervals instead of an iteration that oscillates on slopes.
	for y in range(int(model.height)-1,-1,-1):
		var top = y*32-height_at(fraction_x,y)
		var bottom = (y+1)*32-height_at(fraction_x,y+1)
		if point.y >= top and point.y < bottom:
			return Vector2i(x,y)
	return Vector2i(x,-1)
func texture(path: String) -> Texture2D:
	if not textures.has(path):
		textures[path] = load(path) as Texture2D
	return textures[path]

func height_at(x: float,y: float) -> float:
	var x0 = clampi(floori(x),0,int(model.width)-1)
	var y0 = clampi(floori(y),0,int(model.height)-1)
	var x1 = mini(x0+1,int(model.width)-1)
	var y1 = mini(y0+1,int(model.height)-1)
	var a = lerpf(float(model.heights[y0*int(model.width)+x0]),float(model.heights[y0*int(model.width)+x1]),x-floorf(x))
	var b = lerpf(float(model.heights[y1*int(model.width)+x0]),float(model.heights[y1*int(model.width)+x1]),x-floorf(x))
	return lerpf(a,b,y-floorf(y))

const BUILDINGS = ["Hut", "House", "Inn", "Shop", "Saving Place", "Ruins 1", "Well"]
const WALKABLE = ["Bridge", "Campfire"]
## Natural props the battle arena may use (no houses or bridges).
const NATURE = ["Bush", "Fur", "Iva", "Maple", "Oak", "Pine", "SmallStone", "Ruins 2", "Ruins 3", "TeeRose", "Tuya", "Vallenwood", "nuxTa", "Totem"]

static func kind_of(placement: Dictionary) -> String:
	var name = str(placement.get("name", ""))
	for word in WALKABLE:
		if word in name: return "walkable"
	for word in BUILDINGS:
		if word in name: return "building"
	return "nature"

## Bottom of the picture in world pixels (where a building's walls meet the ground).
func _bottom(placement: Dictionary) -> float:
	var region: Array = placement.rect
	return prop_point(placement).y - float(placement.pivot[1]) + float(region[3])

## Cells a prop takes: a tree/stone its trunk cell; a building its whole base (width x 2 rows); bridges none.
func footprint(placement: Dictionary) -> Array:
	match kind_of(placement):
		"walkable": return []
		"building":
			var region: Array = placement.rect
			var left = floori((prop_point(placement).x - float(placement.pivot[0]) + region[2] * 0.15) / 32.0)
			var right = floori((prop_point(placement).x - float(placement.pivot[0]) + region[2] * 0.85) / 32.0)
			var base_row = floori((_bottom(placement) - 8 + height_at(placement.x, placement.y)) / 32.0)
			var cells: Array = []
			for x in range(left, right + 1):
				for y in range(base_row - 1, base_row + 1):
					cells.append(Vector2i(x, y))
			return cells
	return [Vector2i(floori(float(placement.x)), floori(float(placement.y)))]

## Draw order: trees by their trunk, buildings by the bottom of their walls (so you pass behind them),
## bridges low (you walk over them).
func prop_depth(placement: Dictionary) -> int:
	match kind_of(placement):
		"walkable": return int(prop_point(placement).y - float(placement.pivot[1]))
		"building": return int(_bottom(placement) - 8)
	return int(prop_point(placement).y)

func prop_point(placement: Dictionary) -> Vector2:
	return Vector2(float(placement.x) * 32, float(placement.y) * 32 - height_at(placement.x, placement.y))

func _paint(canvas: CanvasItem) -> void:
	if model.is_empty() or atlas == null:return
	var width = int(model.width)
	var height = int(model.height)
	for y in range(height):
		for x in range(width):
			var tile = str(int(model.tiles[y*width+x]))
			var region: Array = model.visuals.tile_refs[tile].rect
			var points = PackedVector2Array([Vector2(x*32,y*32-height_at(x,y)), Vector2(x*32+32,y*32-height_at(x+1,y)),
				Vector2(x*32+32,y*32+32-height_at(x+1,y+1)),Vector2(x*32,y*32+32-height_at(x,y+1))])
			var uv = PackedVector2Array([Vector2(region[0],region[1]),Vector2(region[0]+32,region[1]),Vector2(region[0]+32,region[1]+32),Vector2(region[0],region[1]+32)])
			for i in range(4):uv[i] /= atlas.get_size()
			canvas.draw_polygon(points,PackedColorArray([Color.WHITE]),uv,atlas)
	pass  # props are separate sprites (see _ready) so characters can walk behind them


## ---------- Map editor (Master) ----------
const TERRAIN_NAME = "nimalis"
var server_version: int = 0
var dirty: bool = false
var history: Array = []   # snapshots [tiles, heights, props], one per stroke
var _rebake_queued: bool = false

func _queue_rebake() -> void:
	if _rebake_queued: return
	_rebake_queued = true
	call_deferred("_flush_rebake")

func _flush_rebake() -> void:
	_rebake_queued = false
	_rebake()

func begin_stroke() -> void:
	history.append([model.tiles.duplicate(), model.heights.duplicate(), ordered.duplicate(true)])
	if history.size() > 40: history.pop_front()
	dirty = true

## End of a mouse stroke: props follow the new relief and the map recomputes what blocks movement.
func finish_stroke() -> void:
	_rebuild_props()
	edited.emit()

func undo_edit() -> void:
	if history.is_empty(): return
	var previous: Array = history.pop_back()
	model.tiles = previous[0]
	model.heights = previous[1]
	ordered = previous[2]
	_rebuild_props()
	_rebake()
	edited.emit()

func inside(cell: Vector2i) -> bool:
	return cell.x >= 0 and cell.y >= 0 and cell.x < int(model.width) and cell.y < int(model.height)

func cells_in(center: Vector2i, radius: int) -> Array:
	var cells: Array = []
	for dy in range(-radius, radius + 1):
		for dx in range(-radius, radius + 1):
			var cell = center + Vector2i(dx, dy)
			if inside(cell) and Vector2(dx, dy).length() <= radius + 0.5: cells.append(cell)
	return cells

func tile_at(cell: Vector2i) -> int:
	return int(model.tiles[cell.y * int(model.width) + cell.x]) if inside(cell) else -1

func paint(cell: Vector2i, tile: int, radius: int = 0) -> void:
	if not model.visuals.tile_refs.has(str(tile)): return
	for target in cells_in(cell, radius):
		model.tiles[target.y * int(model.width) + target.x] = tile
	_queue_rebake()

## Bucket: every connected cell with the same terrain becomes the new one.
func fill(cell: Vector2i, tile: int) -> void:
	var old = tile_at(cell)
	if old < 0 or old == tile or not model.visuals.tile_refs.has(str(tile)): return
	var queue: Array = [cell]
	var seen = {cell: true}
	while not queue.is_empty():
		var current: Vector2i = queue.pop_back()
		model.tiles[current.y * int(model.width) + current.x] = tile
		for step in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var next = current + step
			if inside(next) and not seen.has(next) and tile_at(next) == old:
				seen[next] = true
				queue.append(next)
	_queue_rebake()

## Relief: raise, lower or flatten (to the height under the cursor) the corners around the cell.
func shape(cell: Vector2i, mode: String, radius: int = 1) -> void:
	var width = int(model.width)
	var target = float(model.heights[cell.y * width + cell.x]) if inside(cell) else 0.0
	for point in cells_in(cell, radius):
		var index = point.y * width + point.x
		var value = float(model.heights[index])
		match mode:
			"raise": value += 4.0
			"lower": value -= 4.0
			"flatten": value = lerpf(value, target, 0.5)
		model.heights[index] = clampf(value, -64.0, 256.0)
	_queue_rebake()

func add_prop(template: Dictionary, cell: Vector2i) -> void:
	if not inside(cell) or template.is_empty(): return
	var placement = template.duplicate(true)
	placement.x = cell.x + 0.5
	placement.y = cell.y + 0.5
	ordered.append(placement)
	ordered.sort_custom(func(a, b): return float(a.y) < float(b.y))
	_rebuild_props()
	edited.emit()

## Removes the prop standing on (or covering) the cell, nearest first. Returns true if something was removed.
func remove_prop_at(cell: Vector2i) -> bool:
	var best = -1
	var best_distance = 99.0
	for index in range(ordered.size()):
		var placement: Dictionary = ordered[index]
		var distance = Vector2(float(placement.x), float(placement.y)).distance_to(Vector2(cell) + Vector2(0.5, 0.5))
		if footprint(placement).has(cell): distance = minf(distance, 0.4)
		if distance < 1.2 and distance < best_distance:
			best = index
			best_distance = distance
	if best < 0: return false
	ordered.remove_at(best)
	_rebuild_props()
	edited.emit()
	return true

## Terrain families ("ambientes") by source image: grass, sand, snow, swamp... as the original game grouped them.
func families() -> Dictionary:
	var result: Dictionary = {}
	for id in model.visuals.tile_refs:
		var source = str(model.visuals.tile_refs[id].get("source", "outros")).get_file().get_basename()
		if not result.has(source): result[source] = []
		result[source].append(int(id))
	for key in result: result[key].sort()
	return result

func export_edit() -> Dictionary:
	var trimmed: Array = []
	for placement in ordered:
		trimmed.append({"name": placement.get("name", ""), "atlas": placement.atlas, "rect": placement.rect,
			"pivot": placement.pivot, "x": float(placement.x), "y": float(placement.y)})
	return {"tiles": model.tiles, "heights": model.heights, "props": trimmed}

## Server copy edited by the Master (same for every player). Invalid data is ignored.
func apply_edit(data: Dictionary) -> bool:
	var tiles = data.get("tiles")
	var heights = data.get("heights")
	var list = data.get("props")
	if not tiles is Array or not heights is Array or not list is Array: return false
	if tiles.size() != int(model.width) * int(model.height) or heights.size() != tiles.size(): return false
	for tile in tiles:
		if not model.visuals.tile_refs.has(str(int(tile))): return false
	for placement in list:
		if not placement is Dictionary or not str(placement.get("atlas", "")).begins_with("res://assets/rom2_local/"): return false
		texture(placement.atlas)
	model.tiles = tiles
	model.heights = heights
	ordered = list
	ordered.sort_custom(func(a, b): return float(a.y) < float(b.y))
	server_version = int(data.get("version", 0))
	history.clear()
	dirty = false
	_rebuild_props()
	_rebake()
	edited.emit()
	return true

## Back to the original map shipped with the game (after the Master resets the edit).
func reload_original() -> void:
	var path = "res://assets/rom2_local/map.json"
	var fresh = JSON.parse_string(FileAccess.get_file_as_string(path))
	model.tiles = fresh.tiles
	model.heights = fresh.heights
	ordered = fresh.visuals.placements.duplicate(true)
	ordered.sort_custom(func(a, b): return float(a.y) < float(b.y))
	server_version = 0
	history.clear()
	dirty = false
	_rebuild_props()
	_rebake()
	edited.emit()
