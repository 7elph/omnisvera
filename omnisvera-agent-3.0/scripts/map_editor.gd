extends Control
const Style = preload("res://scripts/ui_style.gd")
## Full-screen map editor for the Master: the whole terrain, every tool, terrain families ("ambientes").
## Edits are shared: "Salvar no mapa" stores them on the server and every player's map follows.
const TERRAIN_PATH = "/workspace/terrain/"
const SAVE_PATH = "/gm/workspace/terrain/"
const TOOLS = [
	["paint", "Pintar", "Pinta o terreno escolhido (arraste para pintar em sequência)"],
	["fill", "Balde", "Troca toda a área ligada do mesmo terreno"],
	["raise", "Elevar", "Sobe o relevo"],
	["lower", "Rebaixar", "Desce o relevo"],
	["flatten", "Aplainar", "Nivela o relevo com a altura do ponto clicado"],
	["prop", "Objeto", "Coloca árvore, pedra, casa... (escolha na lista)"],
	["erase", "Apagar objeto", "Remove o objeto da célula clicada"],
	["pick", "Conta-gotas", "Pega o terreno da célula clicada"],
]
var host: Node
var terrain: Node2D
var tool: String = "paint"
var tile: int = -1
var radius: int = 0
var template: Dictionary = {}
var family: String = ""
var stroke: bool = false
var last_cell = Vector2i(-999, -999)
var hover = Vector2i(-999, -999)
var panning: bool = false
var hidden_ui: Array = []
var poll_count: int = 0

var top = PanelContainer.new()
var toolbar = HFlowContainer.new()
var side = PanelContainer.new()
var families = OptionButton.new()
var palette = GridContainer.new()
var info = Label.new()
var canvas = Control.new()
var tool_buttons: Dictionary = {}
var save_button = Button.new()
var confirm_reset = ConfirmationDialog.new()

func setup(main: Node) -> void:
	host = main
	name = "MapEditor"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	hide()
	if get_parent(): get_parent().remove_child(self)
	host.screen.add_child(self)
	canvas.set_anchors_preset(Control.PRESET_FULL_RECT)
	canvas.mouse_filter = Control.MOUSE_FILTER_STOP
	canvas.gui_input.connect(_canvas_input)
	canvas.draw.connect(_draw_cursor)
	canvas.mouse_exited.connect(func():
		hover = Vector2i(-999, -999)
		canvas.queue_redraw())
	add_child(canvas)
	_build_top()
	_build_side()
	info.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	info.position = Vector2(-10, -30)
	info.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	info.add_theme_color_override("font_outline_color", Color.BLACK)
	info.add_theme_constant_override("outline_size", 6)
	add_child(info)
	confirm_reset.dialog_text = "Voltar o mapa ao original para todos? As edições salvas serão descartadas."
	confirm_reset.ok_button_text = "Restaurar original"
	confirm_reset.confirmed.connect(func(): host.api.request_json("terrain-reset", SAVE_PATH + _name(), HTTPClient.METHOD_DELETE))
	host.screen.add_child(confirm_reset)
	get_viewport().size_changed.connect(_layout)

func _name() -> String:
	return terrain.TERRAIN_NAME if terrain else "nimalis"

func _build_top() -> void:
	Style.rom_frame(top)
	Style.rom_frame(side)
	top.set_anchors_preset(Control.PRESET_TOP_WIDE)
	top.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(top)
	toolbar.add_theme_constant_override("h_separation", 6)
	toolbar.add_theme_constant_override("v_separation", 4)
	top.add_child(toolbar)
	var title = Label.new()
	title.text = "Editor de mapas"
	title.add_theme_font_size_override("font_size", 18)
	toolbar.add_child(title)
	var group = ButtonGroup.new()
	for entry in TOOLS:
		var button = Button.new()
		button.text = entry[1]
		button.tooltip_text = entry[2]
		button.toggle_mode = true
		button.button_group = group
		button.button_pressed = entry[0] == tool
		button.pressed.connect(func(): _set_tool(entry[0]))
		tool_buttons[entry[0]] = button
		toolbar.add_child(button)
	var sizes = OptionButton.new()
	for size in [1, 3, 5, 7, 9]:
		sizes.add_item("Pincel %d" % size)
	sizes.tooltip_text = "Tamanho do pincel (pintar e relevo)"
	sizes.item_selected.connect(func(i): radius = i)
	toolbar.add_child(sizes)
	for entry in [["Desfazer", "Desfaz o último traço (Ctrl+Z)", _undo], ["Salvar no mapa", "Grava para todos os jogadores", _save],
			["Restaurar original", "Volta ao mapa original", func(): confirm_reset.popup_centered()], ["Fechar", "Sai do editor (Esc)", close]]:
		var button = save_button if entry[0] == "Salvar no mapa" else Button.new()
		button.text = entry[0]
		button.tooltip_text = entry[1]
		button.pressed.connect(entry[2])
		toolbar.add_child(button)

func _build_side() -> void:
	side.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(side)
	var column = VBoxContainer.new()
	side.add_child(column)
	var label = Label.new()
	label.text = "Ambiente"
	column.add_child(label)
	families.item_selected.connect(func(i):
		family = str(families.get_item_metadata(i))
		_fill_palette())
	column.add_child(families)
	var scroll = ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(scroll)
	palette.columns = 4
	palette.add_theme_constant_override("h_separation", 4)
	palette.add_theme_constant_override("v_separation", 4)
	scroll.add_child(palette)

func _layout() -> void:
	if not visible: return
	var view = get_viewport_rect().size
	var narrow = view.x < 760
	top.position = Vector2.ZERO
	top.size = Vector2(view.x, 0)
	top.reset_size()
	top.size.x = view.x
	var below = top.get_combined_minimum_size().y
	var width = 150.0 if narrow else 230.0
	palette.columns = 3 if narrow else 4
	side.position = Vector2(0, below)
	side.size = Vector2(width, view.y - below)

func open() -> void:
	terrain = host.grid.terrain
	if terrain == null or terrain.model.is_empty():
		host._notice("Este mapa não tem terreno editável.")
		return
	hidden_ui.clear()
	for child in host.screen.get_children():
		if child != self and child is Control and child.visible:
			hidden_ui.append(child)
			child.hide()
	show()
	families.clear()
	families.add_item("Todos os terrenos")
	families.set_item_metadata(0, "")
	var groups: Dictionary = terrain.families()
	var keys = groups.keys()
	keys.sort()
	for key in keys:
		families.add_item(_family_label(key, groups[key].size()))
		families.set_item_metadata(families.item_count - 1, key)
	family = ""
	if tile < 0: tile = int(terrain.model.tiles[0])
	_fill_palette()
	_layout()
	call_deferred("_layout")
	_refresh_info()
	host.api.request_json("terrain", TERRAIN_PATH + _name())  # latest saved copy before editing

func _family_label(key: String, count: int) -> String:
	return "Ambiente " + key.replace("tile", "").replace("-", " ").strip_edges() + " (%d)" % count

func close() -> void:
	if not visible: return
	hide()
	for child in hidden_ui:
		if is_instance_valid(child): child.show()
	hidden_ui.clear()
	if terrain and terrain.dirty:
		host._notice("Edição do mapa não salva: abra o editor e use \"Salvar no mapa\" para os jogadores verem.")

func _set_tool(name: String) -> void:
	var was_prop = tool == "prop"
	tool = name
	if (tool == "prop") != was_prop: _fill_palette()
	_refresh_info()

func _fill_palette() -> void:
	for child in palette.get_children(): child.queue_free()
	if terrain == null: return
	families.disabled = tool == "prop"
	if tool == "prop":
		var names = terrain.base_templates.keys()
		names.sort()
		for key in names:
			var entry: Dictionary = terrain.base_templates[key]
			var region: Array = entry.rect
			_palette_button(_atlas(terrain.texture(entry.atlas), Rect2(region[0], region[1], region[2], region[3])), key,
				template.get("name", "") == key, _choose_template.bind(entry))
		if template.is_empty() and not names.is_empty(): template = terrain.base_templates[names[0]]
		return
	var ids: Array = []
	if family == "":
		for id in terrain.model.visuals.tile_refs: ids.append(int(id))
		ids.sort()
	else:
		ids = terrain.families().get(family, [])
	for id in ids:
		var region: Array = terrain.model.visuals.tile_refs[str(id)].rect
		_palette_button(_atlas(terrain.atlas, Rect2(region[0], region[1], 32, 32)), "Terreno %d" % id, id == tile,
			_choose_tile.bind(id))

func _choose_template(entry: Dictionary) -> void:
	template = entry
	_fill_palette()
	_refresh_info()

func _choose_tile(id: int) -> void:
	tile = id
	if tool in ["pick", "erase", "prop"]:
		tool_buttons["paint"].button_pressed = true
		_set_tool("paint")
	_fill_palette()
	_refresh_info()

func _atlas(texture: Texture2D, region: Rect2) -> AtlasTexture:
	var picture = AtlasTexture.new()
	picture.atlas = texture
	picture.region = region
	return picture

func _palette_button(icon: Texture2D, hint: String, selected: bool, action: Callable) -> void:
	var button = TextureButton.new()
	button.texture_normal = icon
	button.ignore_texture_size = true
	button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	button.custom_minimum_size = Vector2(44, 44)
	button.tooltip_text = hint
	button.pressed.connect(action)
	if selected:
		button.modulate = Color(1.25, 1.15, 0.7)
		var frame = ReferenceRect.new()
		frame.border_color = Color(1, 0.85, 0.3)
		frame.border_width = 2
		frame.editor_only = false
		frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
		frame.set_anchors_preset(Control.PRESET_FULL_RECT)
		button.add_child(frame)
	palette.add_child(button)

func _refresh_info() -> void:
	if terrain == null: return
	var what = "terreno %d" % tile
	if tool == "prop": what = str(template.get("name", "nenhum objeto"))
	var where = "" if hover.x < -100 else " · célula %d,%d" % [hover.x, hover.y]
	var state = " · NÃO SALVO" if terrain.dirty else " · salvo"
	info.text = tool_buttons[tool].text + ": " + what + where + state + "   (roda: zoom · botão direito: mover)"
	save_button.disabled = not terrain.dirty

func _cell() -> Vector2i:
	return host.grid.world_to_grid(host.get_global_mouse_position())

func _canvas_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			host._zoom(1.12)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			host._zoom(0.89)
		elif event.button_index in [MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE]:
			panning = event.pressed
		elif event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				_press(_cell())
			elif stroke:
				stroke = false
				terrain.finish_stroke()
				_refresh_info()
		canvas.queue_redraw()
	elif event is InputEventMouseMotion:
		if panning:
			host.camera.position -= event.relative / host.camera.zoom
		var cell = _cell()
		if cell != hover:
			hover = cell
			if stroke and tool in ["paint", "raise", "lower", "flatten"] and cell != last_cell:
				_apply(cell)
			_refresh_info()
			canvas.queue_redraw()
	elif event is InputEventMagnifyGesture:
		host._zoom(event.factor)
	elif event is InputEventPanGesture:
		host.camera.position += event.delta * 8 / host.camera.zoom

func _press(cell: Vector2i) -> void:
	if not terrain.inside(cell): return
	if tool == "pick":
		tile = terrain.tile_at(cell)
		_set_tool("paint")
		tool_buttons["paint"].button_pressed = true
		_fill_palette()
		return
	terrain.begin_stroke()
	match tool:
		"fill":
			terrain.fill(cell, tile)
			terrain.finish_stroke()
		"prop":
			terrain.add_prop(template, cell)
		"erase":
			if not terrain.remove_prop_at(cell):
				terrain.history.pop_back()
				host._notice("Nenhum objeto nessa célula.")
		_:
			stroke = true
			_apply(cell)
	_refresh_info()

func _apply(cell: Vector2i) -> void:
	last_cell = cell
	if tool == "paint":
		terrain.paint(cell, tile, radius)
	else:
		terrain.shape(cell, tool, maxi(radius, 1))

func _draw_cursor() -> void:
	if terrain == null or not terrain.inside(hover): return
	var view: Transform2D = host.get_canvas_transform()
	var cells: Array = [hover] if tool in ["fill", "prop", "erase", "pick"] else terrain.cells_in(hover, radius if tool == "paint" else maxi(radius, 1))
	var color = Color(1, 0.85, 0.3, 0.9) if tool != "erase" else Color(1, 0.3, 0.25, 0.9)
	for cell in cells:
		var points = PackedVector2Array()
		for corner in [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1), Vector2(0, 0)]:
			var gx = cell.x + corner.x
			var gy = cell.y + corner.y
			points.append(view * Vector2(gx * 32, gy * 32 - terrain.height_at(gx, gy)) - canvas.global_position)
		canvas.draw_polyline(points, color, 1.5)

func _undo() -> void:
	if terrain:
		terrain.undo_edit()
		_refresh_info()

func _save() -> void:
	if terrain == null or not terrain.dirty: return
	var data: Dictionary = terrain.export_edit()
	var heights: Array = []
	for value in data.heights: heights.append(snappedf(float(value), 0.01))
	data.heights = heights
	data["expected_version"] = terrain.server_version
	save_button.disabled = true
	host.api.request_json("terrain-save", SAVE_PATH + _name(), HTTPClient.METHOD_PUT, data)

func _unhandled_key_input(event: InputEvent) -> void:
	if not visible or not event.pressed: return
	if event.keycode == KEY_ESCAPE:
		close()
		get_viewport().set_input_as_handled()
	elif event.keycode == KEY_Z and event.ctrl_pressed:
		_undo()
		get_viewport().set_input_as_handled()

## Everyone keeps the map in sync with the Master's saved edit (cheap: the server answers "unchanged").
func poll() -> void:
	if terrain == null:
		terrain = host.grid.terrain
		if terrain == null or terrain.model.is_empty(): return
	poll_count += 1
	if poll_count % 2 == 1 and not visible:
		host.api.request_json("terrain", TERRAIN_PATH + _name() + "?since=" + str(terrain.server_version))

# ---- controller protocol (main.gd dispatches API answers) ----
## Access lost: close the editor (unsaved strokes stay in memory until the page reloads).
func clear() -> void:
	close()
	poll_count = 0

func handles(key: String) -> bool:
	return key in ["terrain", "terrain-save", "terrain-reset"]

func received(key: String, data: Variant) -> void:
	if terrain == null or not data is Dictionary: return
	match key:
		"terrain":
			if data.get("unchanged", false): return
			if data.get("edited", false):
				if int(data.get("version", 0)) != terrain.server_version and not terrain.dirty:
					terrain.apply_edit(data)
			elif terrain.server_version > 0 and not terrain.dirty:
				terrain.reload_original()
		"terrain-save":
			terrain.server_version = int(data.get("version", terrain.server_version))
			terrain.dirty = false
			host._notice("Mapa salvo: todos os jogadores já veem a nova versão.")
		"terrain-reset":
			terrain.reload_original()
			host._notice("Mapa restaurado ao original.")
	_refresh_info()

func failed(key: String, message: String, code: int) -> bool:
	if not handles(key): return false
	if key == "terrain": return true  # older server/proxy: the map simply stays as shipped
	save_button.disabled = false
	host._notice(("Outra janela salvou o mapa antes. " if code == 409 else "") + message)
	return true
