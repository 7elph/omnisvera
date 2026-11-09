extends Control
## Battle board built like the exploration map: the same terrain (heights, trees) around where the fight
## started, a 1 m grid, everyone's sprites at map scale, zoom and pan. Presentation and intent only:
## turns, reach, movement budget, dice and damage remain decisions of the server.
signal move_requested(token: Dictionary, cell: Vector2i)
signal attack_requested(actor: Dictionary, target: Dictionary)
signal next_requested
signal end_requested
signal ai_toggled(enabled: bool)
signal guard_requested
signal ability_requested(actor: Dictionary, entry: Dictionary)
signal ability_targets(entry: Dictionary, targets: Array)
const ABILITY_BINDINGS = ["character_technique", "vezemir_skill", "necromancer_spell", "hemomancy_attack", "hemomancy_shield", "dorn_protocol", "dorn_spell",
	"inventory_item", "character_state_action", "vine_bracelet"]  # potions and items, Forma da Noite, Pulseira de Vinhas
const Gothic = preload("res://scripts/gothic_theme.gd")
const Actor = preload("res://scripts/dorn.gd")
const Commands = preload("res://scripts/game_commands.gd")
const WorldGrid = preload("res://scripts/grid_map.gd")
const SPRITES = {"dorn7": "res://assets/sprites/dorn.json", "morthak": "res://assets/sprites/morthak.json"}
const TILE = 32.0               # one 1 m cell, same pixels as the exploration terrain
const STEP_SECONDS = 0.16        # visual walk per cell
const HudOrbs = preload("res://scripts/hud_orbs.gd")
const MOVES_FILE = "user://battle_moves.json"
const Icons = preload("res://scripts/icon_catalog.gd")
var state: Dictionary = {}
var snapshot: Dictionary = {}
var master: bool = false
var profile: String = ""
var actors: Dictionary = {}          # token id -> Fighter
var selected: Dictionary = {}        # token whose turn it is
var attacking: bool = false
var encounter_key: String = ""
var attack_id: String = "melee"
var attack_melee: bool = true
var definition: Dictionary = {}
var definitions: Dictionary = {}     # character id -> sheet definition
var states: Dictionary = {}          # character id -> authorized sheet state (PV)
var actions: Dictionary = {}         # character id -> native action manifest entries
var targeting_entry: Dictionary = {} # ability waiting for target(s)
var targeting_max: int = 1
var picked_targets: Array = []
var choose_ability = OptionButton.new()
var use_ability = Button.new()
var cast = Button.new()
var media: Node
var ai_enabled: bool = true
var log_lines: Array = []
var map_texture: Texture2D
var map_holder = TextureRect.new()  # receives the arena art from the media cache
var hover_cell = Vector2i(-99, -99)
var world_ref: Node2D               # the exploration grid (terrain + its cols/rows), set by main
var board = Node2D.new()            # zoomed/panned content of the board
var chunk_origin = Vector2i.ZERO    # terrain cell under arena cell (0, 0)
var chunk_props = Node2D.new()     # trees/rocks of the arena, depth-sorted with the fighters
var arena_tiles: Array = []         # ground tile id per cell (generated in the style of the world map)
var blocked: Dictionary = {}        # cells with a tree/rock: nobody stands there
var base_h: float = 0.0             # terrain height at the arena centre (keeps the board level in the frame)
var zoom: float = 0.0               # 0 = fit to the frame
var pan = Vector2.ZERO
var touches: Dictionary = {}
var action_bar = HudOrbs.new()
var counters = Label.new()
var turn_ref: String = ""           # turn whose movement is being counted
var moved_cells: int = 0
var last_cell = Vector2i(-99, -99)
# Widgets
var backdrop = TextureRect.new()
var shade = ColorRect.new()
var stage = Control.new()
var caption = Label.new()
var turn_label = Label.new()
var result = Label.new()
var bar = PanelContainer.new()
var choose_attack = OptionButton.new()
var attack = Button.new()
var advance = Button.new()
var retreat = Button.new()
var guard = Button.new()
var next = Button.new()
var finish = Button.new()
var ai_toggle = CheckButton.new()
var minimize = Button.new()
var intro = ColorRect.new()
var hint = Label.new()

class Fighter extends Control:
	var token: Dictionary = {}
	var side: String = "hero"
	var front: bool = true
	var active: bool = false
	var targetable: bool = false
	var hp: float = 0
	var hp_max: float = 0
	var shown: float = 1
	var body: Node2D
	var portrait: TextureRect
	var plate = Label.new()
	var flash: float = 0
	var cell = Vector2i(-99, -99)
	var walking: bool = false
	var breath: float = randf() * TAU
	var body_base = Vector2.ZERO
	signal picked(token: Dictionary)
	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		plate.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		plate.add_theme_font_size_override("font_size", 13)
		plate.add_theme_color_override("font_color", Color("#f1e3c0"))
		plate.add_theme_color_override("font_shadow_color", Color.BLACK)
		plate.add_theme_constant_override("shadow_outline_size", 4)
		plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
		plate.visible = false
		add_child(plate)
		mouse_entered.connect(func(): plate.visible = true)
		mouse_exited.connect(func(): plate.visible = active)
	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			picked.emit(token)
			accept_event()
	func _process(delta: float) -> void:
		if body:  # everyone breathes and shifts their weight while waiting
			breath += delta * (2.2 if side == "monster" else 1.6)
			body.position = body_base + Vector2(sin(breath * 0.5) * 1.2, sin(breath) * 1.6)
		var goal = hp / hp_max if hp_max > 0 else 1.0
		if not is_equal_approx(shown, goal) or flash > 0 or active or targetable:
			shown = move_toward(shown, goal, delta * 0.7)
			flash = maxf(0, flash - delta)
			queue_redraw()
	func layout(edge: float) -> void:
		size = Vector2(edge, edge * 1.25)
		plate.add_theme_font_size_override("font_size", 8)  # board is zoomed: small text stays readable
		plate.position = Vector2(-30, size.y - 2)
		plate.size = Vector2(size.x + 60, 12)
		if body:
			body_base = Vector2(size.x / 2, size.y * 0.86)
			body.position = body_base
			# Same proportions as on the map: the tallest (Dorn, 30) fills the cell box, goblins stay small.
			body.scale = Vector2.ONE * (edge * 1.05 / 30.0)
		if portrait:
			portrait.position = Vector2(size.x * 0.1, size.y * 0.12)
			portrait.size = Vector2(size.x * 0.8, size.x * 0.8)
	func _draw() -> void:
		var feet = Vector2(size.x / 2, size.y * 0.88)
		draw_set_transform(feet, 0, Vector2(1, 0.32))
		draw_circle(Vector2.ZERO, size.x * 0.42, Color(0, 0, 0, 0.55))
		if active:
			var pulse = 0.6 + 0.4 * sin(Time.get_ticks_msec() / 180.0)
			draw_arc(Vector2.ZERO, size.x * 0.46, 0, TAU, 48, Color(0.95, 0.78, 0.35, pulse), 4)
		if targetable:
			var pulse = 0.5 + 0.5 * sin(Time.get_ticks_msec() / 120.0)
			draw_arc(Vector2.ZERO, size.x * 0.5, 0, TAU, 48, Color(0.95, 0.2, 0.15, pulse), 4)
		draw_set_transform(Vector2.ZERO)
		if portrait:
			draw_rect(Rect2(portrait.position - Vector2(3, 3), portrait.size + Vector2(6, 6)), Color("#d4a85a") if active else Color("#7a5c2c"), false, 3)
		var bar = Rect2(size.x * 0.1, -10, size.x * 0.8, 7)
		draw_rect(bar.grow(1), Color(0, 0, 0, 0.85))
		var tone = Color("#c62a1e")  # life is always a red bar
		draw_rect(Rect2(bar.position, Vector2(bar.size.x * clampf(shown, 0, 1), bar.size.y)), tone)
		if flash > 0:
			draw_rect(Rect2(Vector2.ZERO, size), Color(1, 0.2, 0.1, flash * 0.5))

func _ready() -> void:
	z_index = 60
	mouse_filter = Control.MOUSE_FILTER_STOP
	backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	backdrop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	backdrop.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(backdrop)
	backdrop.visible = false  # the arena art is drawn on the board, not stretched over the screen
	map_holder.visible = false
	add_child(map_holder)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.color = Color(0.035, 0.028, 0.024, 0.94)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	stage.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	stage.mouse_filter = Control.MOUSE_FILTER_STOP
	stage.draw.connect(_draw_stage)
	stage.gui_input.connect(_board_input)
	stage.clip_contents = true
	add_child(stage)
	board.draw.connect(_draw_board)
	stage.add_child(board)
	board.add_child(chunk_props)
	var top = HBoxContainer.new()
	top.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	top.offset_left = 14
	top.offset_right = -14
	top.offset_top = 8
	top.add_theme_constant_override("separation", 10)
	add_child(top)
	Gothic.title(caption, 20)
	caption.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	caption.clip_text = true
	top.add_child(caption)
	ai_toggle.text = "IA dos monstros"
	ai_toggle.button_pressed = ai_enabled
	ai_toggle.tooltip_text = "Desligue para o Mestre assumir as criaturas"
	ai_toggle.toggled.connect(func(on: bool):
		ai_enabled = on
		ai_toggled.emit(on))
	top.add_child(ai_toggle)
	minimize.text = "Minimizar"
	minimize.pressed.connect(hide)
	top.add_child(minimize)
	Gothic.shadowed(turn_label)
	turn_label.add_theme_font_size_override("font_size", 17)
	turn_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	turn_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(turn_label)
	Gothic.shadowed(hint)
	hint.add_theme_color_override("font_color", Gothic.GOLD)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(hint)
	add_child(bar)
	var column = VBoxContainer.new()
	column.add_theme_constant_override("separation", 6)
	bar.add_child(column)
	result.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	result.add_theme_font_size_override("font_size", 13)
	result.max_lines_visible = 3
	column.add_child(result)
	var row = HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 6)
	row.add_theme_constant_override("v_separation", 6)
	column.add_child(row)
	choose_attack.item_selected.connect(_choose)
	choose_attack.custom_minimum_size = Vector2(150, 40)
	row.add_child(choose_attack)
	var shortcut = Shortcut.new(); var key = InputEventKey.new(); key.keycode = KEY_A; shortcut.events = [key]; attack.shortcut = shortcut
	var turn_shortcut = Shortcut.new(); var turn_key = InputEventKey.new(); turn_key.keycode = KEY_SPACE; turn_shortcut.events = [turn_key]; next.shortcut = turn_shortcut
	attack.text = "Atacar"
	attack.pressed.connect(func():
		if not targeting_entry.is_empty():
			cancel_targeting()
			return
		attacking = not attacking
		_refresh_targets())
	advance.text = "Avançar"
	advance.tooltip_text = "Ir para a linha de frente, junto ao inimigo mais próximo"
	advance.pressed.connect(func(): _step(true))
	retreat.text = "Recuar"
	retreat.tooltip_text = "Voltar para a retaguarda"
	retreat.pressed.connect(func(): _step(false))
	guard.text = "Guarda"
	guard.pressed.connect(func(): guard_requested.emit())
	next.text = "Passar turno"
	next.pressed.connect(func(): next_requested.emit())
	finish.text = "Encerrar"
	finish.pressed.connect(func(): end_requested.emit())
	choose_ability.custom_minimum_size = Vector2(150, 40)
	choose_ability.tooltip_text = "Magias e habilidades da ficha (validadas pelo servidor)"
	row.add_child(choose_ability)
	use_ability.text = "Usar"
	use_ability.pressed.connect(_use_ability)
	cast.text = "Lançar"
	cast.visible = false
	cast.pressed.connect(_finish_targets)
	for button in [use_ability, cast]:
		button.custom_minimum_size = Vector2(0, 40)
		row.add_child(button)
	for button in [attack, advance, retreat, guard, next, finish]:
		button.custom_minimum_size = Vector2(0, 40)
		row.add_child(button)
	# One bar like the map HUD: life potion + every attack and ability as a clickable icon.
	row.visible = false
	action_bar.slot_pressed.connect(_bar_pressed)
	add_child(action_bar)
	Gothic.shadowed(counters)
	counters.add_theme_color_override("font_color", Gothic.GOLD)
	counters.add_theme_font_size_override("font_size", 14)
	counters.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	counters.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(counters)
	next.reparent(self)
	finish.reparent(top)
	for ui in [top, turn_label, hint, bar, action_bar, counters, next]:
		ui.z_index = 1000  # always above the board's trees and fighters
	next.text = "Fim do turno"
	next.tooltip_text = "Passar a vez (Espaço)"
	intro.color = Color.WHITE
	intro.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	intro.mouse_filter = Control.MOUSE_FILTER_IGNORE
	intro.visible = false
	add_child(intro)
	resized.connect(_layout_arena)

func _layout_arena() -> void:
	var view = size
	turn_label.position = Vector2(0, 42)
	turn_label.size = Vector2(view.x, 24)
	hint.position = Vector2(0, 66)
	hint.size = Vector2(view.x, 22)
	bar.visible = result.text.strip_edges() != ""
	var bar_width = minf(action_bar.preferred_width(), view.x - 140)
	action_bar.size = Vector2(bar_width, 96)
	action_bar.position = Vector2((view.x - bar_width) / 2, view.y - 100)
	counters.position = Vector2(0, view.y - 126)
	counters.size = Vector2(view.x, 22)
	next.size = Vector2(120, 40)
	next.position = Vector2(minf(action_bar.position.x + bar_width + 10, view.x - 130), view.y - 52)
	bar.position = Vector2(10, view.y - 196)
	bar.size = Vector2(minf(420, view.x * 0.45), 64)
	_place_fighters()

func _ground_rect() -> Rect2:
	return Rect2(Vector2(10, 92), Vector2(size.x - 20, maxf(80, size.y - 92 - 132)))

func _grid_size() -> Vector2i:
	var grid: Dictionary = snapshot.get("map", {}).get("grid", {}) if snapshot.get("map", {}).get("grid") is Dictionary else {}
	return Vector2i(maxi(1, int(grid.get("cols", 12))), maxi(1, int(grid.get("rows", 8))))

func _terrain() -> Node2D:
	return world_ref.terrain if world_ref and world_ref.terrain and not world_ref.terrain.model.is_empty() else null

## A fresh arena in the same style as the world map: its ground tiles and its trees/rocks,
## laid out at random (same layout for everyone: seeded by the encounter).
func _pick_chunk() -> void:
	for old in chunk_props.get_children(): old.queue_free()
	arena_tiles.clear()
	blocked.clear()
	var t = _terrain()
	if not t: return
	var dims = _grid_size()
	var rng = RandomNumberGenerator.new()
	rng.seed = hash(encounter_key + str(dims))
	# Ground: the most common tiles of the world, weighted by how often they appear.
	var counts: Dictionary = {}
	for tile in t.model.tiles: counts[int(tile)] = counts.get(int(tile), 0) + 1
	var common = counts.keys()
	common.sort_custom(func(a, b): return counts[a] > counts[b])
	common = common.slice(0, 5)
	var weights = PackedFloat32Array(common.map(func(k): return float(counts[k])))
	for i in range(dims.x * dims.y):
		arena_tiles.append(common[rng.rand_weighted(weights)] if not common.is_empty() else 0)
	# Relief: borrow the slopes of a random patch of the world, so the arena has the same 3/4 depth as the map.
	chunk_origin = Vector2i(rng.randi_range(0, maxi(0, int(t.model.width) - dims.x - 1)), rng.randi_range(0, maxi(0, int(t.model.height) - dims.y - 1)))
	base_h = t.height_at(chunk_origin.x + dims.x / 2.0, chunk_origin.y + dims.y / 2.0)
	# Props: the world's own objects (pines, oaks, bushes, rocks), a few per arena.
	var kinds: Dictionary = {}
	for placement in t.ordered:
		var name = str(placement.get("name", ""))
		if t.NATURE.any(func(word): return word in name) and float(placement.rect[2]) <= 128:
			kinds[str(placement.atlas) + str(placement.rect)] = placement
	var palette = kinds.values()
	var taken: Dictionary = {}
	for token in _battle_tokens(): taken[cell_of(token)] = true
	var wanted = maxi(2, dims.x * dims.y / 14)
	var tries = 0
	while blocked.size() < wanted and tries < wanted * 20 and not palette.is_empty():
		tries += 1
		var cell = Vector2i(rng.randi_range(0, dims.x - 1), rng.randi_range(0, dims.y - 1))
		if taken.has(cell) or blocked.has(cell): continue
		var near_fighter = false
		for other in taken.keys():
			if maxi(absi(other.x - cell.x), absi(other.y - cell.y)) <= 1: near_fighter = true
		if near_fighter: continue
		var placement: Dictionary = palette[rng.randi_range(0, palette.size() - 1)]
		var region: Array = placement.rect
		var sprite = Sprite2D.new()
		sprite.texture = t.textures[placement.atlas]
		sprite.region_enabled = true
		sprite.region_rect = Rect2(region[0], region[1], region[2], region[3])
		sprite.centered = false
		var foot = corner(cell.x + 0.5, cell.y + 0.75)
		var pivot = Vector2(placement.pivot[0], placement.pivot[1])
		if pivot.y < float(region[3]) * 0.5: pivot = Vector2(region[2] / 2.0, region[3] - 4.0)  # stones: stand on their bottom
		sprite.position = foot - pivot
		sprite.z_index = int(foot.y)
		chunk_props.add_child(sprite)
		blocked[cell] = true

## Point of a grid corner in board coordinates (follows the terrain slopes).
func corner(gx: float, gy: float) -> Vector2:
	var t = _terrain()
	if t and not arena_tiles.is_empty():
		return Vector2(gx * TILE, gy * TILE - (t.height_at(chunk_origin.x + gx, chunk_origin.y + gy) - base_h))
	return Vector2(gx, gy) * TILE

func cell_center(cell: Vector2i) -> Vector2:
	return corner(cell.x + 0.5, cell.y + 0.5)

func _to_board(point: Vector2) -> Vector2:
	return (point - board.position) / board.scale.x

func cell_at(point: Vector2) -> Vector2i:
	var p = _to_board(point)
	var x = floori(p.x / TILE)
	var dims = _grid_size()
	for y in range(dims.y - 1, -1, -1):
		var fx = p.x / TILE
		if p.y >= corner(fx, y).y and p.y < corner(fx, y + 1).y: return Vector2i(x, y)
	return Vector2i(x, -1)

func _cell_shape(cell: Vector2i) -> PackedVector2Array:
	return PackedVector2Array([corner(cell.x, cell.y), corner(cell.x + 1, cell.y), corner(cell.x + 1, cell.y + 1), corner(cell.x, cell.y + 1)])

## Fit the arena in the frame (zoom 0) or keep the player's zoom/pan.
func _fit_board() -> void:
	var ground = _ground_rect()
	var dims = _grid_size()
	var content = Vector2(dims) * TILE
	var fit = clampf(minf(ground.size.x / content.x, ground.size.y / (content.y + 40)), 0.6, 4.0)
	var scale_now = zoom if zoom > 0 else fit
	board.scale = Vector2(scale_now, scale_now)
	board.position = (ground.get_center() - content * scale_now / 2.0 + pan).floor()

func _movement_cells(token: Dictionary) -> int:
	var source: Variant = definitions.get(str(token.get("character_id", "")), token.get("sheet", {}))
	var raw = str(source.get("movement", 9)) if source is Dictionary else "9"
	var digits = RegEx.new()
	digits.compile("[0-9]+([.,][0-9]+)?")
	var found = digits.search(raw)
	var meters = float(found.get_string().replace(",", ".")) if found else 9.0
	var cell_m = float(snapshot.get("map", {}).get("grid", {}).get("cell_size_m", 1)) if snapshot.get("map", {}).get("grid") is Dictionary else 1.0
	return maxi(1, int(floor(meters / maxf(cell_m, 0.1))))

func _moves_left(token: Dictionary) -> int:
	return maxi(0, _movement_cells(token) - (moved_cells if identity(token) == turn_ref.get_slice("|", 0) else 0))

func _can_act() -> bool:
	return not selected.is_empty() and (master or identity(selected) == profile) and not state.get("encounter", {}).get("action_committed", false) \
		and not (master and ai_enabled and not is_hero(selected))

func _draw_stage() -> void:
	_fit_board()
	stage.draw_rect(_ground_rect().grow(4), Color(0.05, 0.04, 0.03, 0.9))
	board.queue_redraw()

func _draw_board() -> void:
	var dims = _grid_size()
	var t = _terrain()
	if t and arena_tiles.size() == dims.x * dims.y:
		# Ground painted with the world's own tiles.
		for y in range(dims.y):
			for x in range(dims.x):
				var ref = t.model.visuals.tile_refs.get(str(arena_tiles[y * dims.x + x]), {})
				if ref.is_empty(): continue
				var rect: Array = ref.rect
				var atlas_size: Vector2 = t.atlas.get_size()
				var uv = PackedVector2Array([Vector2(rect[0], rect[1]) / atlas_size, Vector2(rect[0] + 32, rect[1]) / atlas_size,
					Vector2(rect[0] + 32, rect[1] + 32) / atlas_size, Vector2(rect[0], rect[1] + 32) / atlas_size])
				board.draw_polygon(_cell_shape(Vector2i(x, y)), PackedColorArray([Color.WHITE]), uv, t.atlas)
	elif map_holder.texture:
		board.draw_texture_rect(map_holder.texture, Rect2(Vector2.ZERO, Vector2(dims) * TILE), false)
	else:
		board.draw_rect(Rect2(Vector2.ZERO, Vector2(dims) * TILE), Color(0.2, 0.17, 0.12))
	var reach_cells: Dictionary = {}
	if _can_act() and attacking == false and targeting_entry.is_empty():
		var origin = cell_of(selected)
		var budget = _moves_left(selected)
		var used = _occupied()
		for x in range(maxi(0, origin.x - budget), mini(dims.x, origin.x + budget + 1)):
			for y in range(maxi(0, origin.y - budget), mini(dims.y, origin.y + budget + 1)):
				if not used.has(Vector2i(x, y)) and not blocked.has(Vector2i(x, y)): reach_cells[Vector2i(x, y)] = true
	for x in range(dims.x):
		for y in range(dims.y):
			var cell = Vector2i(x, y)
			var shape = _cell_shape(cell)
			if reach_cells.has(cell):
				board.draw_colored_polygon(shape, Color(0.45, 0.8, 1.0, 0.09))
			if cell == hover_cell and (reach_cells.has(cell) or attacking):
				board.draw_colored_polygon(shape, Color(0.95, 0.8, 0.4, 0.3))
			board.draw_polyline(shape + PackedVector2Array([shape[0]]), Color(0, 0, 0, 0.22), 1.0 / board.scale.x)
	if not selected.is_empty():
		var mine = _cell_shape(cell_of(selected))
		board.draw_polyline(mine + PackedVector2Array([mine[0]]), Color(0.95, 0.78, 0.35, 0.95), 2.0 / board.scale.x)
	var edge = PackedVector2Array([corner(0, 0), corner(dims.x, 0), corner(dims.x, dims.y), corner(0, dims.y), corner(0, 0)])
	board.draw_polyline(edge, Gothic.GOLD_DIM, 3.0 / board.scale.x)

func _zoom_at(point: Vector2, factor: float) -> void:
	var before = _to_board(point)
	zoom = clampf((zoom if zoom > 0 else board.scale.x) * factor, 0.6, 5.0)
	board.scale = Vector2(zoom, zoom)
	board.position = point - before * zoom
	var dims = _grid_size()
	pan = board.position - (_ground_rect().get_center() - Vector2(dims) * TILE * zoom / 2.0)
	stage.queue_redraw()

func _board_input(event: InputEvent) -> void:
	# Zoom: wheel or pinch. Pan: right/middle drag or two fingers. Left click/tap: act.
	if event is InputEventMouseButton and event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
		_zoom_at(event.position, 1.15 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 1 / 1.15)
		return
	if event is InputEventMagnifyGesture:
		_zoom_at(event.position, event.factor)
		return
	if event is InputEventPanGesture:
		pan -= event.delta * 8
		stage.queue_redraw()
		return
	if event is InputEventMouseMotion and event.button_mask & (MOUSE_BUTTON_MASK_RIGHT | MOUSE_BUTTON_MASK_MIDDLE):
		pan += event.relative
		stage.queue_redraw()
		return
	if event is InputEventScreenTouch:
		if event.pressed: touches[event.index] = event.position
		else: touches.erase(event.index)
		return
	if event is InputEventScreenDrag and touches.size() >= 2:
		var other = touches.keys().filter(func(k): return k != event.index)
		if other.is_empty(): return
		var anchor: Vector2 = touches[other[0]]
		var before = anchor.distance_to(touches[event.index])
		touches[event.index] = event.position
		var after = anchor.distance_to(event.position)
		if before > 8: _zoom_at((anchor + event.position) / 2.0, after / before)
		pan += event.relative / 2.0
		return
	if event is InputEventMouseMotion:
		var cell = cell_at(event.position)
		if cell != hover_cell:
			hover_cell = cell
			board.queue_redraw()
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var cell = cell_at(event.position)
		if not _inside(cell): return
		for token in _battle_tokens():  # a click on someone's cell picks them
			if cell_of(token) == cell:
				_picked(token)
				return
		if attacking or not targeting_entry.is_empty() or not _can_act(): return
		if blocked.has(cell):
			notice("Não dá para ficar aí: tem uma árvore ou pedra.")
			return
		var origin = cell_of(selected)
		if maxi(absi(cell.x - origin.x), absi(cell.y - origin.y)) > _moves_left(selected):
			notice("Longe demais: restam %d m de movimento." % _moves_left(selected))
			return
		move_requested.emit(selected, cell)

static func identity(token: Dictionary) -> String:
	return str(token.character_id if token.get("character_id") else token.get("id", ""))

static func is_hero(token: Dictionary) -> bool:
	if token.get("character_id"): return true
	var sheet: Variant = token.get("sheet", {})
	if not sheet is Dictionary: return false
	if str(sheet.get("disposition", "")) == "ally": return true
	var summon: Variant = sheet.get("summon", {})
	return summon is Dictionary and summon.get("caster") != null and str(summon.get("caster")) != ""

static func cell_of(token: Dictionary) -> Vector2i:
	var p: Dictionary = token.get("grid_position", {}) if token.get("grid_position") is Dictionary else {}
	return Vector2i(int(p.get("cell_x", -99)), int(p.get("cell_y", -99)))

static func reach(a: Dictionary, b: Dictionary) -> int:
	var d = cell_of(a) - cell_of(b)
	return maxi(absi(d.x), absi(d.y))

func _battle_tokens() -> Array:
	var ids = state.get("encounter", {}).get("participants", []).map(func(p): return str(p.get("token_id", p.get("target_id", ""))))
	var list: Array = []
	for token in snapshot.get("tokens", []):
		if str(token.get("id", "")) in ids and not token.get("sheet", {}).get("combat_retired", false):
			list.append(token)
	return list

func enemies_of(token: Dictionary) -> Array:
	return _battle_tokens().filter(func(other): return is_hero(other) != is_hero(token))

func nearest_enemy(token: Dictionary) -> Dictionary:
	var best: Dictionary = {}
	for other in enemies_of(token):
		if best.is_empty() or reach(token, other) < reach(token, best):
			best = other
	return best

func update_view(effects: Dictionary, workspace: Dictionary, is_master: bool, my_profile: String) -> void:
	state = effects; snapshot = workspace; master = is_master; profile = my_profile
	var enc: Dictionary = state.get("encounter", {})
	if not enc.get("active", false) or not enc.get("battle_mode", false):
		hide()
		return
	var key = str(enc.get("started_at", ""))
	if key != encounter_key:
		encounter_key = key
		for actor in actors.values(): actor.queue_free()
		actors.clear()
		log_lines.clear()
		result.text = ""
		zoom = 0.0
		pan = Vector2.ZERO
		_pick_chunk()
		show()
		play_intro()
	var participants: Array = enc.get("participants", [])
	var current: Dictionary = participants[int(enc.get("turn_index", 0)) % maxi(1, participants.size())] if not participants.is_empty() else {}
	var turn_identity = str(current.get("target_id", ""))
	caption.text = str(enc.get("title", "Batalha")) + " · Rodada " + str(int(state.get("round", 1)))
	selected = {}
	var alive: Dictionary = {}
	for token in _battle_tokens():
		var id = str(token.id)
		alive[id] = true
		if identity(token) == turn_identity: selected = token
		if not actors.has(id): _spawn(token)
		var fighter: Fighter = actors[id]
		fighter.token = token
		fighter.side = "hero" if is_hero(token) else "monster"
		var source: Dictionary = states.get(str(token.get("character_id", "")), token) if token.get("character_id") else token
		fighter.hp = float(source.get("current_hp") if source.get("current_hp") != null else 0)
		fighter.hp_max = float(source.get("maximum_hp") if source.get("maximum_hp") != null else maxf(fighter.hp, 1))
		fighter.plate.text = _short_name(token)
		fighter.tooltip_text = "%s · Vida %d / %d" % [_short_name(token), int(fighter.hp), int(fighter.hp_max)]
		fighter.active = identity(token) == turn_identity
		fighter.plate.visible = fighter.active
	for id in actors.keys():
		if not alive.has(id) and Time.get_ticks_msec() > int(actors[id].get_meta("dying_until", 0)):
			actors[id].queue_free()
			actors.erase(id)
	for token in _battle_tokens():
		var fighter: Fighter = actors[str(token.id)]
		var foe = nearest_enemy(token)
		fighter.front = not foe.is_empty() and reach(token, foe) <= 1
	turn_label.text = ("Turno de " + str(current.get("name", turn_identity))) if not current.is_empty() else ""
	var mine = master or turn_identity == profile
	var monster_turn = not selected.is_empty() and not is_hero(selected)
	var committed = enc.get("action_committed", false)
	attack.disabled = not mine or committed or selected.is_empty() or (monster_turn and ai_enabled and master)
	advance.disabled = attack.disabled or (not selected.is_empty() and actors.has(str(selected.id)) and actors[str(selected.id)].front)
	retreat.disabled = attack.disabled or (not selected.is_empty() and actors.has(str(selected.id)) and not actors[str(selected.id)].front)
	var manifest: Array = actions.get(str(selected.get("character_id", "")), [])
	guard.visible = selected.get("character_id") == "dorn7" and manifest.is_empty()
	guard.disabled = not mine
	_fill_abilities(manifest, mine and not committed)
	next.disabled = not mine or (monster_turn and ai_enabled and master)
	finish.visible = master
	ai_toggle.visible = master
	if not mine:
		hint.text = "Aguardando " + str(current.get("name", "o próximo combatente"))
	elif monster_turn and master and ai_enabled:
		hint.text = "A criatura age sozinha · desligue a IA para assumir"
	elif not targeting_entry.is_empty():
		hint.text = _targeting_hint()
	elif attacking:
		hint.text = "Escolha o alvo"
	else:
		hint.text = ""
	_fill_attacks()
	_track_movement(enc)
	_fill_bar(mine and not committed and not (monster_turn and ai_enabled and master))
	var image_path = workspace.get("map", {}).get("image_path")
	if media and image_path and map_holder.get_meta("path", "") != image_path:
		map_holder.texture = null
		map_holder.set_meta("path", image_path)
		media.bind(image_path, map_holder, "texture", 768)
	_place_fighters()
	_refresh_targets()

## Movement used this turn, counted from the cells the server confirmed.
func _track_movement(enc: Dictionary) -> void:
	var key = (identity(selected) if not selected.is_empty() else "") + "|" + str(enc.get("turn_sequence", "")) + "|" + str(state.get("round", ""))
	var now = cell_of(selected) if not selected.is_empty() else Vector2i(-99, -99)
	if key != turn_ref:
		turn_ref = key
		# A reload in the middle of a turn keeps what was already walked.
		var saved = JSON.parse_string(FileAccess.get_file_as_string(MOVES_FILE)) if FileAccess.file_exists(MOVES_FILE) else null
		moved_cells = int(saved.get("moved", 0)) if saved is Dictionary and saved.get("turn") == key else 0
	elif now != last_cell and last_cell.x > -50:
		moved_cells += maxi(absi(now.x - last_cell.x), absi(now.y - last_cell.y))
		var file = FileAccess.open(MOVES_FILE, FileAccess.WRITE)
		if file: file.store_string(JSON.stringify({"turn": turn_ref, "moved": moved_cells}))
	last_cell = now
	if selected.is_empty():
		counters.text = ""
		return
	var cell_m = float(snapshot.get("map", {}).get("grid", {}).get("cell_size_m", 1)) if snapshot.get("map", {}).get("grid") is Dictionary else 1.0
	var actions_left = 0 if enc.get("action_committed", false) else 1
	counters.text = "Ações: %d   ·   Movimento: %s m de %s m" % [actions_left, _m(_moves_left(selected) * cell_m), _m(_movement_cells(selected) * cell_m)]

static func _m(value: float) -> String:
	return str(int(value)) if is_equal_approx(value, roundf(value)) else "%.1f" % value

## The bar shows life and every attack and ability of whoever is acting; hover = what it does, click = use.
func _fill_bar(usable: bool) -> void:
	var entries: Array = []
	for index in range(choose_attack.item_count):
		var meta: Dictionary = choose_attack.get_item_metadata(index)
		var weapon_art = Icons.item_art({"name": str(meta.name), "item_type": "arma"})
		weapon_art.pop_back()  # no generic "inventory" picture: keep the sword icon when the weapon has no art
		entries.append({"key": "attack:" + str(meta.id), "kind": "attack", "index": index, "image_path": weapon_art if weapon_art.size() > 3 else null, "name": str(meta.name) + ("" if "corpo" in str(meta.name).to_lower() or "dist" in str(meta.name).to_lower() else (" · corpo a corpo" if meta.melee else " · à distância")),
			"icon": "res://assets/ui/attacks.svg" if ResourceLoader.exists("res://assets/ui/attacks.svg") else "res://assets/ui/items.svg"})
	for index in range(choose_ability.item_count):
		var entry: Dictionary = choose_ability.get_item_metadata(index)
		var reason = str(entry.get("availability", {}).get("reason", ""))
		entries.append({"key": "ability:" + str(entry.get("ref", index)), "kind": "ability", "index": index, "image_path": entry.get("image_path"),
			"name": str(entry.get("label", "Habilidade")) + ("\n" + reason if reason != "" else ""), "icon": "res://assets/ui/spells.svg",
			"disabled": choose_ability.is_item_disabled(index)})
	action_bar.SLOTS = clampi(entries.size(), 4, 12)
	action_bar.media = media
	action_bar.set_slots(entries)
	var slots = action_bar.belt.get_children()
	for index in range(mini(slots.size(), entries.size())):
		slots[index].disabled = not usable or entries[index].get("disabled", false)
	var who: Dictionary = selected
	var source: Dictionary = states.get(str(who.get("character_id", "")), who) if who.get("character_id") else who
	action_bar.set_vitals(_short_name(who) if not who.is_empty() else "", null, source.get("current_hp"), source.get("maximum_hp"), {}, [])
	_layout_arena()

func _bar_pressed(entry: Dictionary) -> void:
	if entry.get("kind") == "attack":
		cancel_targeting()
		choose_attack.select(int(entry.index))
		_choose(int(entry.index))
		attacking = true
		_refresh_targets()
		hint.text = "Escolha o alvo" + (" · corpo a corpo avança se preciso" if attack_melee else "")
	elif entry.get("kind") == "ability":
		choose_ability.select(int(entry.index))
		_use_ability()

func _short_name(token: Dictionary) -> String:
	var name = str(token.get("name", identity(token)))
	return "Dorn" if token.get("character_id") == "dorn7" else name.substr(0, 18)

func _spawn(token: Dictionary) -> void:
	var fighter = Fighter.new()
	fighter.token = token
	fighter.picked.connect(_picked)
	board.add_child(fighter)
	var manifest = ""
	if SPRITES.has(str(token.get("character_id", ""))):
		manifest = SPRITES[str(token.character_id)]
	else:
		manifest = WorldGrid.sprite_for(token)  # same sprite as on the map (goblins, Morthak's skeleton, standees)
	if manifest != "" and FileAccess.file_exists(manifest):
		var body = Actor.new()
		body.manifest_path = manifest
		body.selected = false
		fighter.add_child(body)
		body.set_process(false)
		fighter.body = body
	else:
		var picture = TextureRect.new()
		picture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		picture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		picture.mouse_filter = Control.MOUSE_FILTER_IGNORE
		picture.texture = load("res://assets/ui/sheet.svg")
		fighter.add_child(picture)
		fighter.portrait = picture
		if media and token.get("image_path"):
			media.bind(token.image_path, picture, "texture", 128)
	actors[str(token.id)] = fighter

func _place_fighters() -> void:
	_fit_board()
	var edge = 30.0 / 1.05  # body scale 1: the same size as on the exploration map
	for fighter in actors.values():
		if not is_instance_valid(fighter) or fighter.walking: continue
		fighter.layout(edge)
		var cell = cell_of(fighter.token)
		var goal = cell_center(cell) - Vector2(fighter.size.x / 2, fighter.size.y * 0.88)
		if fighter.has_meta("placed") and fighter.cell != cell and fighter.cell.x > -50:
			_walk(fighter, fighter.cell, cell)
		else:
			fighter.position = goal
			fighter.set_meta("placed", true)
		fighter.cell = cell
		fighter.z_index = int(cell_center(cell).y)
	board.queue_redraw()

## Step cell by cell with the walk animation facing the screen direction.
func _walk(fighter: Fighter, start: Vector2i, finish: Vector2i) -> void:
	fighter.walking = true
	var tween = fighter.create_tween()
	var dims = _grid_size()
	var path: Array = Commands.path_around(start, finish, blocked, dims.x, dims.y)
	if path.is_empty(): path = Commands.path_between(start, finish)
	for index in range(1, path.size()):
		var cell = Vector2i(int(path[index][0]), int(path[index][1]))
		var previous = Vector2i(int(path[index - 1][0]), int(path[index - 1][1]))
		var screen = cell_center(cell) - cell_center(previous)
		var facing = ("right" if screen.x > 0 else "left") if absf(screen.x) >= absf(screen.y) else ("down" if screen.y > 0 else "up")
		tween.tween_callback(func():
			if fighter.body and fighter.body.sprite.sprite_frames.has_animation("walk_" + facing):
				fighter.body.sprite.play("walk_" + facing))
		tween.tween_property(fighter, "position", cell_center(cell) - Vector2(fighter.size.x / 2, fighter.size.y * 0.88), STEP_SECONDS)
	tween.tween_callback(func():
		fighter.walking = false
		if fighter.body and not fighter.body.performing: fighter.body.sprite.play("idle")
		fighter.z_index = int(cell_center(finish).y))

func _fill_attacks() -> void:
	var chosen = attack_id
	choose_attack.clear()
	var list: Array = []
	if selected.get("character_id"):
		var sheet: Dictionary = definitions.get(str(selected.character_id), definition if str(definition.get("id", "")) == str(selected.character_id) else {})
		var by_id: Dictionary = {}
		for item in sheet.get("attacks", []):
			if item is Dictionary: by_id[str(item.get("id", ""))] = item
		var manifest: Array = actions.get(str(selected.character_id), [])
		for entry in manifest:
			if entry.get("binding") != "character_attack" or entry.get("availability", {}).get("state") in ["unavailable", "blocked"]: continue
			var attack_ref = str(entry.get("execution", {}).get("payload", {}).get("attack_id", ""))
			list.append({"id": attack_ref, "name": str(entry.get("label", "Ataque")), "melee": _is_melee(by_id[attack_ref]) if by_id.has(attack_ref) else false})
		if manifest.is_empty():
			for item in sheet.get("attacks", []):
				if item is Dictionary and not item.get("blocked", false):
					list.append({"id": str(item.get("id", "")), "name": str(item.get("name", "Ataque")), "melee": _is_melee(item)})
	else:
		var attacks: Array = selected.get("sheet", {}).get("attacks", [])
		for index in range(attacks.size()):
			list.append({"id": str(index), "name": str(attacks[index].get("name", "Ataque")), "melee": _is_melee(attacks[index])})
	for entry in list:
		choose_attack.add_item(entry.name)
		choose_attack.set_item_metadata(choose_attack.item_count - 1, entry)
	choose_attack.visible = choose_attack.item_count > 0
	for index in range(choose_attack.item_count):
		if choose_attack.get_item_metadata(index).id == chosen:
			choose_attack.select(index)
	if choose_attack.item_count:
		_choose(choose_attack.selected if choose_attack.selected >= 0 else 0)

func _choose(index: int) -> void:
	if index < 0 or index >= choose_attack.item_count: return
	var entry: Dictionary = choose_attack.get_item_metadata(index)
	attack_id = entry.id
	attack_melee = entry.melee

static func _is_melee(item: Dictionary) -> bool:
	var slot = str(item.get("slot", item.get("kind", item.get("type", "")))).to_lower()
	if "ranged" in slot or "distân" in slot or "dist" in slot or "throw" in slot: return false
	if item.get("range_m") != null and float(item.range_m) > 1.5: return false
	return true

func set_sheet(data: Dictionary) -> void:
	var definition_data: Dictionary = data.get("definition", {}) if data.get("definition") is Dictionary else {}
	if definition_data.get("id") and data.get("state") is Dictionary:
		states[str(definition_data.id)] = data.state
	set_attacks(definition_data)
	if visible and not snapshot.is_empty(): update_view(state, snapshot, master, profile)

func set_attacks(value: Dictionary) -> void:
	definition = value
	if value.get("id"):
		definitions[str(value.id)] = value
	if visible: _fill_attacks()

func _refresh_targets() -> void:
	for fighter in actors.values():
		if is_instance_valid(fighter):
			if not targeting_entry.is_empty():
				fighter.targetable = not str(fighter.token.id) in picked_targets.map(func(t): return str(t.id)) and fighter.token.get("id") != selected.get("id")
			else:
				fighter.targetable = attacking and not selected.is_empty() and fighter.side != ("hero" if is_hero(selected) else "monster")
	attack.text = "Cancelar" if attacking or not targeting_entry.is_empty() else "Atacar"
	if attacking:
		hint.text = "Escolha o alvo" + ("" if not attack_melee else " · corpo a corpo avança se preciso")

func _picked(token: Dictionary) -> void:
	if not targeting_entry.is_empty():
		_pick_ability_target(token)
		return
	if not attacking or selected.is_empty(): return
	if is_hero(token) == is_hero(selected): return
	attacking = false
	_refresh_targets()
	attack_requested.emit(selected, token)

func _step(forward: bool) -> void:
	if selected.is_empty(): return
	var cell = forward_cell(selected, nearest_enemy(selected)) if forward else retreat_cell(selected)
	if cell != cell_of(selected):
		move_requested.emit(selected, cell)

func _occupied() -> Dictionary:
	var used: Dictionary = {}
	for token in _battle_tokens(): used[cell_of(token)] = true
	return used

func _inside(cell: Vector2i) -> bool:
	var grid: Dictionary = snapshot.get("map", {}).get("grid", {})
	return cell.x >= 0 and cell.y >= 0 and cell.x < int(grid.get("cols", 12)) and cell.y < int(grid.get("rows", 8))

## Free cell adjacent to the target, closest to the mover. Server still validates budget.
func forward_cell(mover: Dictionary, target: Dictionary) -> Vector2i:
	var origin = cell_of(mover)
	if target.is_empty(): return origin
	var used = _occupied()
	var best = origin
	var best_cost = 9999
	var around = cell_of(target)
	for dx in [-1, 0, 1]:
		for dy in [-1, 0, 1]:
			var cell = around + Vector2i(dx, dy)
			if (dx == 0 and dy == 0) or not _inside(cell) or blocked.has(cell) or (used.has(cell) and cell != origin): continue
			var cost = maxi(absi(cell.x - origin.x), absi(cell.y - origin.y))
			if cost < best_cost: best_cost = cost; best = cell
	return best

func retreat_cell(mover: Dictionary) -> Vector2i:
	var origin = cell_of(mover)
	var foe = nearest_enemy(mover)
	if foe.is_empty(): return origin
	var away = Vector2i(signi(origin.x - cell_of(foe).x), 0)
	if away.x == 0: away.x = -1 if is_hero(mover) else 1
	var used = _occupied()
	for distance in [2, 1]:
		for dy in [0, -1, 1]:
			var cell = origin + away * distance + Vector2i(0, dy)
			if _inside(cell) and not used.has(cell): return cell
	return origin

func resolved(record: Dictionary) -> void:
	var labels = {"hit": "acertou", "miss": "errou", "critical": "crítico!", "critical_hit": "crítico!", "critical_failure": "falha crítica"}
	var line = "%s · d20 %d · %s · %d de dano" % [str(record.get("actor_name", "")), int(record.get("d20", 0)), labels.get(record.get("result", ""), str(record.get("result", ""))), int(record.get("damage_total", 0))]
	log_lines.append(line)
	log_lines = log_lines.slice(maxi(0, log_lines.size() - 3))
	result.text = "\n".join(log_lines)
	bar.visible = true
	var actor_id = str(record.get("actor_character_id", ""))
	var target_id = str(record.get("target_id", ""))
	for token in snapshot.get("tokens", []):
		if not actors.has(str(token.id)): continue
		var fighter: Fighter = actors[str(token.id)]
		if identity(token) == actor_id:
			_lunge(fighter)
		if identity(token) == target_id:
			var damage = int(record.get("damage_total", 0))
			_popup(fighter, ("-" + str(damage)) if damage > 0 else "Errou", Color("#ff5a3c") if damage > 0 else Color("#d8d8d8"))
			if damage > 0: fighter.flash = 0.6
			if int(record.get("hp_after", 1)) <= 0:
				fighter.set_meta("dying_until", Time.get_ticks_msec() + 1400)
				if fighter.body and fighter.body.sprite.sprite_frames.has_animation("death"):
					fighter.body.play_action("death")
				else:
					fighter.create_tween().tween_property(fighter, "modulate", Color(0.4, 0.4, 0.4, 0.0), 1.2)

func animate_defeat(record: Dictionary) -> void:
	resolved(record)

func _lunge(fighter: Fighter) -> void:
	if fighter.body and fighter.body.sprite.sprite_frames.has_animation("attack"):
		fighter.body.play_action("attack")
	var direction = 1.0 if fighter.side == "hero" else -1.0
	var start = fighter.position
	var tween = fighter.create_tween()
	tween.tween_property(fighter, "position", start + Vector2(8 * direction, -3), 0.12).set_trans(Tween.TRANS_QUAD)
	tween.tween_property(fighter, "position", start, 0.2)

func _popup(fighter: Fighter, text: String, color: Color) -> void:
	var label = Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 26)
	label.add_theme_color_override("font_color", color)
	Gothic.shadowed(label)
	label.position = fighter.position + Vector2(fighter.size.x / 2 - 10, -14)
	label.scale = Vector2(0.5, 0.5)
	label.z_index = 4000
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	board.add_child(label)
	var tween = label.create_tween()
	tween.tween_property(label, "position:y", label.position.y - 22, 0.9).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(label, "modulate:a", 0.0, 0.9).set_delay(0.3)
	tween.tween_callback(label.queue_free)

func play_intro() -> void:
	intro.visible = true
	intro.color = Color.WHITE
	intro.modulate.a = 0
	var tween = create_tween()
	for i in range(2):
		tween.tween_property(intro, "modulate:a", 0.9, 0.07)
		tween.tween_property(intro, "modulate:a", 0.0, 0.09)
	tween.tween_callback(func(): intro.color = Color.BLACK; intro.modulate.a = 1.0)
	tween.tween_property(intro, "modulate:a", 0.0, 0.45)
	tween.tween_callback(func(): intro.visible = false)

func notice(text: String) -> void:
	log_lines.append(text)
	log_lines = log_lines.slice(maxi(0, log_lines.size() - 3))
	result.text = "\n".join(log_lines)
	bar.visible = true

func _process(_delta: float) -> void:
	if visible and Engine.get_process_frames() % 10 == 0: board.queue_redraw()


# --- Magias e habilidades (manifesto nativo da ficha) ----------------------
func set_actions(character_id: String, entries: Array) -> void:
	actions[character_id] = entries
	if visible and not snapshot.is_empty(): update_view(state, snapshot, master, profile)

func _fill_abilities(manifest: Array, usable: bool) -> void:
	var chosen = choose_ability.get_item_metadata(choose_ability.selected).get("ref", "") if choose_ability.selected >= 0 and choose_ability.item_count else ""
	choose_ability.clear()
	for entry in manifest:
		if entry.get("automation_scope") != "native" or not str(entry.get("binding", "")) in ABILITY_BINDINGS: continue
		if str(entry.get("ref", "")).ends_with(":caixao"): continue  # full rest: not a battle action
		var availability: Dictionary = entry.get("availability", {})
		choose_ability.add_item(str(entry.get("label", "Habilidade")))
		var index = choose_ability.item_count - 1
		choose_ability.set_item_metadata(index, entry)
		choose_ability.set_item_tooltip(index, str(availability.get("reason", "")))
		if availability.get("state") in ["unavailable", "blocked"]:
			choose_ability.set_item_disabled(index, true)
		if str(entry.get("ref", "")) == chosen: choose_ability.select(index)
	var has_any = choose_ability.item_count > 0
	choose_ability.visible = has_any
	use_ability.visible = has_any
	use_ability.disabled = not usable or not has_any
	if has_any and (choose_ability.selected < 0 or choose_ability.is_item_disabled(choose_ability.selected)):
		for index in range(choose_ability.item_count):
			if not choose_ability.is_item_disabled(index):
				choose_ability.select(index)
				break

func _use_ability() -> void:
	if selected.is_empty() or choose_ability.selected < 0 or choose_ability.is_item_disabled(choose_ability.selected): return
	attacking = false
	ability_requested.emit(selected, choose_ability.get_item_metadata(choose_ability.selected))

## The controller asks for targets (count from the server contract when there is one).
func begin_targeting(entry: Dictionary, maximum: int = 1) -> void:
	targeting_entry = entry
	targeting_max = maxi(1, maximum)
	picked_targets.clear()
	cast.visible = targeting_max > 1
	cast.disabled = true
	attack.text = "Cancelar"
	hint.text = _targeting_hint()
	_refresh_targets()

func cancel_targeting() -> void:
	targeting_entry = {}
	picked_targets.clear()
	cast.visible = false
	attack.text = "Atacar"
	_refresh_targets()

func _targeting_hint() -> String:
	var label = str(targeting_entry.get("label", "Habilidade"))
	return label + (" · escolha o alvo" if targeting_max == 1 else " · alvos %d/%d · toque em Lançar" % [picked_targets.size(), targeting_max])

func _pick_ability_target(token: Dictionary) -> void:
	if str(token.get("id")) in picked_targets.map(func(t): return str(t.id)): return
	picked_targets.append(token)
	if targeting_max == 1 or picked_targets.size() >= targeting_max:
		_finish_targets()
		return
	cast.disabled = false
	hint.text = _targeting_hint()
	_refresh_targets()

func _finish_targets() -> void:
	if targeting_entry.is_empty() or picked_targets.is_empty(): return
	var entry = targeting_entry
	var chosen = picked_targets.duplicate()
	cancel_targeting()
	ability_targets.emit(entry, chosen)
