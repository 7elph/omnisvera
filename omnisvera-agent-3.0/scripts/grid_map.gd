extends Node2D
## Isometric projection of logical cells, without movement or RPG rules.
const HALF_TILE = Vector2(40, 20)
var terrain: Node2D
var cols: int = 18
var rows: int = 18
var selected = Vector2i(-1, -1)
var tokens: Array = []
var range_m: float = 0
var cell_size_m: float = 1
var range_origin = Vector2i.ZERO
var animated_profiles: Array = ["dorn7", "morthak"]
const Actor = preload("res://scripts/dorn.gd")
const CITY_ART = "res://assets/ui/art/city_marker.png"
var actors: Dictionary = {}        # token id -> sprite actor (heroes without a scene node, monsters)
var portraits: Dictionary = {}     # token id -> small picture for pins that have art but no sprite
var media: Node
var city_sprite: Sprite2D
var city_cell = Vector2i(-99, -99)
var city_token: Dictionary = {}
var city_near: bool = false
var _clock: float = 0
var geometry: Dictionary = {}
var blocked: Dictionary = {}   # cells taken by trees and the city (walk around them)
var blocked_props: Dictionary = {}

func _build_blocked() -> void:
	blocked_props.clear()
	if terrain and not terrain.model.is_empty():
		for placement in terrain.ordered:
			for cell in terrain.footprint(placement): blocked_props[cell] = true
	blocked = blocked_props.duplicate()
	if not city_token.is_empty():  # the city walls: you enter by clicking it, not by walking over it
		for dx in range(-2, 3):
			for dy in range(-2, 1):
				blocked[city_cell + Vector2i(dx, dy)] = true

## Cell of any token: its grid position, or (provisional grids send none) the cell under its map coordinates.
func token_cell(token: Dictionary) -> Vector2i:
	var cell: Dictionary = token.get("grid_position", {}) if token.get("grid_position") is Dictionary else {}
	if not cell.is_empty(): return Vector2i(int(cell.cell_x), int(cell.cell_y))
	return _cell_from_coords(token)

## Locations carry only map coordinates (0..100); place them on the cell under that point.
func _cell_from_coords(token: Dictionary) -> Vector2i:
	if token.get("latitude") == null or token.get("longitude") == null: return Vector2i(-99, -99)
	var origin = Vector2(float(geometry.get("origin_x", 0)), float(geometry.get("origin_y", 0)))
	return Vector2i(int((float(token.longitude) - origin.x) / ((100.0 - origin.x) / cols)), int((float(token.latitude) - origin.y) / ((100.0 - origin.y) / rows)))

## Sprite manifest for a pin, or "" to keep the drawn marker.
static func sprite_for(token: Dictionary) -> String:
	var hero = str(token.get("character_id", ""))
	if hero != "" and FileAccess.file_exists("res://assets/sprites/standee_%s.json" % hero):
		return "res://assets/sprites/standee_%s.json" % hero
	if "esqueleto" in str(token.get("name", "")).to_lower() and FileAccess.file_exists("res://assets/sprites/skeleton_morthak.json"):
		return "res://assets/sprites/skeleton_morthak.json"
	if "goblin" in str(token.get("name", "")).to_lower() and FileAccess.file_exists("res://assets/rom2_local/goblin.json"):
		return "res://assets/rom2_local/goblin.json"
	return ""

static func is_city(token: Dictionary) -> bool:
	return token.get("token_type") == "location" and token.get("sheet") is Dictionary and str(token.sheet.get("kind", "")) == "city"

func grid_to_world(cell: Vector2i) -> Vector2:
	if terrain: return terrain.cell_to_world(cell)
	return Vector2((cell.x - cell.y) * HALF_TILE.x, (cell.x + cell.y) * HALF_TILE.y)

func world_to_grid(point: Vector2) -> Vector2i:
	if terrain: return terrain.world_to_cell(point)
	return Vector2i(roundi((point.x / HALF_TILE.x + point.y / HALF_TILE.y) / 2.0),
		roundi((point.y / HALF_TILE.y - point.x / HALF_TILE.x) / 2.0))

func is_cell_valid(cell: Vector2i) -> bool:
	return cell.x >= 0 and cell.y >= 0 and cell.x < cols and cell.y < rows

func configure_grid(grid: Dictionary, visible_tokens: Array) -> void:
	cols = clampi(int(grid.get("cols", 18)), 1, 96)
	rows = clampi(int(grid.get("rows", 18)), 1, 96)
	cell_size_m = float(grid.get("cell_size_m", 1))
	tokens = visible_tokens
	geometry = grid
	_sync_actors()
	_build_blocked()
	queue_redraw()

func _sync_actors() -> void:
	var alive: Dictionary = {}
	city_token = {}
	for token in tokens:
		var at = token_cell(token)
		if is_city(token):
			city_token = token
			city_cell = at
			continue
		if at.x < -50: continue
		if token.get("character_id", "") in animated_profiles: continue
		var manifest = sprite_for(token)
		var id = str(token.get("id", ""))
		if manifest == "":
			if media and token.get("image_path"):
				alive[id] = true
				if not portraits.has(id):
					var picture = TextureRect.new()
					picture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
					picture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
					picture.mouse_filter = Control.MOUSE_FILTER_IGNORE
					picture.size = Vector2(18, 18)
					add_child(picture)
					media.bind(token.image_path, picture, "texture", 64)
					portraits[id] = picture
				portraits[id].position = grid_to_world(at) - Vector2(9, 9)
				portraits[id].z_index = int(grid_to_world(at).y) + 1
			continue
		alive[id] = true
		if not actors.has(id):
			var actor = Actor.new()
			actor.manifest_path = manifest
			actor.selected = false
			actor.projection = self
			add_child(actor)
			actor.snap_visual(grid_to_world(at))
			actors[id] = actor
		else:
			actors[id].move_visual(grid_to_world(at))
		actors[id].visible_name = str(token.get("name", ""))
	for id in actors.keys():
		if not alive.has(id):
			actors[id].queue_free()
			actors.erase(id)
	for id in portraits.keys():
		if not alive.has(id):
			portraits[id].queue_free()
			portraits.erase(id)
	if city_token.is_empty():
		if city_sprite: city_sprite.visible = false
	else:
		if not city_sprite:
			city_sprite = Sprite2D.new()
			city_sprite.texture = load(CITY_ART) if ResourceLoader.exists(CITY_ART) else null
			city_sprite.centered = true
			add_child(city_sprite)
		city_sprite.visible = true
		var art_width = city_sprite.texture.get_width() if city_sprite.texture else 256
		city_sprite.scale = Vector2.ONE * (HALF_TILE.x * 5.0 / art_width)
		city_sprite.position = grid_to_world(city_cell) - Vector2(0, city_sprite.texture.get_height() * city_sprite.scale.y * 0.35 if city_sprite.texture else 0)
		# Depth = bottom of the walls, so whoever stands in front of the city is drawn in front, and behind it, behind.
		city_sprite.z_index = int(city_sprite.position.y + (city_sprite.texture.get_height() * city_sprite.scale.y * 0.45 if city_sprite.texture else 0))
		city_sprite.modulate = Color(1, 1, 1, 1) if city_token.get("visible_to_players", true) else Color(1, 1, 1, 0.5)

## The city sprite lights up when a hero stands close enough to enter.
func set_city_near(near: bool) -> void:
	city_near = near
	if city_sprite: city_sprite.self_modulate = Color(1.25, 1.15, 0.9) if near else Color(0.85, 0.85, 0.85)

func city_hit(cell: Vector2i) -> bool:
	return not city_token.is_empty() and absi(cell.x - city_cell.x) <= 2 and cell.y - city_cell.y <= 0 and cell.y - city_cell.y >= -3

func _process(delta: float) -> void:
	_clock += delta
	for actor in actors.values():  # monsters and heroes breathe while standing still
		actor.sprite.position = Vector2(0, sin(_clock * 2.4 + actor.position.x * 0.05) * 1.4)

func _draw() -> void:
	for y in range(0 if terrain else rows):
		for x in range(cols):
			var point = grid_to_world(Vector2i(x, y))
			var polygon = PackedVector2Array([point + Vector2(-40, 0), point + Vector2(0, -20),
				point + Vector2(40, 0), point + Vector2(0, 20)])
			var color = Color("#34463e") if (x + y) % 2 == 0 else Color("#2c3d37")
			if x % 6 == 0 or y % 6 == 0:
				color = Color("#48514a")
			if Vector2i(x, y) == selected:
				color = Color("#476e77")
			draw_colored_polygon(polygon, color)
			if range_m > 0 and maxi(absi(x - range_origin.x), absi(y - range_origin.y)) * cell_size_m <= range_m:
				draw_colored_polygon(polygon, Color(1, 1, 1, 0.16))
			draw_polyline(PackedVector2Array([polygon[0], polygon[1], polygon[2], polygon[3], polygon[0]]),
				Color(0.53, 0.59, 0.48, 0.2), 1)
	if terrain and range_m > 0:
		for y in range(rows):
			for x in range(cols):
				if maxi(absi(x-range_origin.x),absi(y-range_origin.y))*cell_size_m > range_m: continue
				var points = PackedVector2Array()
				for corner in [Vector2(x,y),Vector2(x+1,y),Vector2(x+1,y+1),Vector2(x,y+1)]:
					points.append(Vector2(corner.x*32,corner.y*32-terrain.height_at(corner.x,corner.y)))
				draw_colored_polygon(points,Color(1,1,1,0.16))
	for token in tokens:
		if token.get("character_id", "") in animated_profiles or actors.has(str(token.get("id", ""))) or is_city(token):
			continue
		var at = token_cell(token)
		if at.x < -50 or token.get("token_type") == "location":
			continue
		var point = grid_to_world(at)
		# Person-sized marker in the token's colour, with the name always shown (heroes) so nobody gets lost on the map.
		var tint = Color(str(token.get("color", ""))) if Color.html_is_valid(str(token.get("color", ""))) else (Color("#d9b45a") if token.get("character_id") else Color("#b0523f"))
		draw_circle(point + Vector2(0, 2), 9, Color(0, 0, 0, 0.45))
		draw_circle(point, 8, tint)
		draw_arc(point, 9.5, 0, TAU, 24, Color(1, 1, 1, 0.9), 1.5)
		if token.get("character_id") or at == selected:
			var label = str(token.get("name", "")).get_slice(" ", 0)
			draw_string(ThemeDB.fallback_font, point + Vector2(-30, 22), label, HORIZONTAL_ALIGNMENT_CENTER, 60, 11, Color(0, 0, 0, 0.8))
			draw_string(ThemeDB.fallback_font, point + Vector2(-31, 21), label, HORIZONTAL_ALIGNMENT_CENTER, 60, 11, Color("#f3e6c4"))
