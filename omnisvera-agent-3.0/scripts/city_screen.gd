extends Control
## Town screen with clickable points of interest. Art and hotspots come from a JSON
## config (swap sprites without code). Places link to real pins of the city map.
signal place_opened(spot: Dictionary, pin: Dictionary)
signal exit_requested
signal enter_requested
signal closed
signal variant_requested
const Gothic = preload("res://scripts/gothic_theme.gd")
var config: Dictionary = {}
var media: Node
var master: bool = false
var active_on_table: bool = false
var city: Dictionary = {}          # /workspace?map_id=<city> snapshot
var mode: String = "town"
var mask: Image
var spots: Array = []
var hovered: Dictionary = {}
var art = TextureRect.new()
var glow = TextureRect.new()
var city_map = TextureRect.new()
var pins = Control.new()
var tag = Label.new()
var title_label = Label.new()
var status = Label.new()
var toggle = Button.new()
var exit_button = Button.new()
var enter_button = Button.new()
var close_button = Button.new()
var art_button = Button.new()
var glows: Dictionary = {}
var outline = Control.new()          # polygon hotspots (art without a mask)
var art_size = Vector2(640, 480)

func _ready() -> void:
	z_index = 55
	mouse_filter = Control.MOUSE_FILTER_STOP
	var back = ColorRect.new()
	back.color = Color("#0b0806")
	back.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(back)
	for picture in [art, city_map]:
		picture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		picture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		picture.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(picture)
	glow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	glow.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	glow.stretch_mode = TextureRect.STRETCH_SCALE
	var add = CanvasItemMaterial.new()
	add.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	glow.material = add
	add_child(glow)
	outline.mouse_filter = Control.MOUSE_FILTER_IGNORE
	outline.draw.connect(_draw_outline)
	add_child(outline)
	pins.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(pins)
	var top = HBoxContainer.new()
	top.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	top.offset_left = 12
	top.offset_right = -12
	top.offset_top = 8
	top.add_theme_constant_override("separation", 8)
	add_child(top)
	Gothic.title(title_label, 22)
	title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(title_label)
	toggle.pressed.connect(func(): set_mode("map" if mode == "town" else "town"))
	enter_button.text = "Levar o grupo à cidade"
	enter_button.pressed.connect(func(): enter_requested.emit())
	exit_button.text = "Sair para os Arredores"
	exit_button.pressed.connect(func(): exit_requested.emit())
	close_button.text = "Fechar"
	close_button.pressed.connect(func():
		hide()
		closed.emit())
	art_button.tooltip_text = "Trocar o conjunto de arte da cidade"
	art_button.pressed.connect(func(): variant_requested.emit())
	for button in [art_button, toggle, enter_button, exit_button, close_button]:
		button.custom_minimum_size.y = 38
		top.add_child(button)
	Gothic.shadowed(tag)
	tag.add_theme_font_size_override("font_size", 18)
	tag.add_theme_color_override("font_color", Gothic.GOLD)
	tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tag.hide()
	add_child(tag)
	Gothic.shadowed(status)
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	status.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(status)
	resized.connect(_arrange)

func variant_label(name: String, switchable: bool) -> void:
	art_button.text = "Arte: " + {"original": "original", "rom2": "ROM2"}.get(name, name)
	art_button.visible = switchable

func configure(value: Dictionary) -> void:
	config = value
	art.texture = null
	hovered = {}
	spots = config.get("hotspots", [])
	title_label.text = str(config.get("title", "Cidade"))
	mask = null
	glows.clear()
	var background = str(config.get("background", ""))
	if background != "" and ResourceLoader.exists(background):
		art.texture = load(background)
	var mask_path = str(config.get("mask", ""))
	if mask_path != "" and ResourceLoader.exists(mask_path):
		mask = (load(mask_path) as Texture2D).get_image()
		if mask.is_compressed(): mask.decompress()
	if art.texture != null: art_size = art.texture.get_size()
	if art.texture == null: mode = "map"
	set_mode(mode)

func present(snapshot: Dictionary, is_master: bool, on_table: bool) -> void:
	city = snapshot
	master = is_master
	active_on_table = on_table
	var image_path = snapshot.get("map", {}).get("image_path")
	if media and image_path and city_map.get_meta("path", "") != image_path:
		city_map.set_meta("path", image_path)
		media.bind(image_path, city_map, "texture", 768)
	enter_button.visible = master and not on_table
	exit_button.visible = master and on_table
	close_button.visible = not on_table
	status.text = "" if on_table else "Visita: os estabelecimentos atendem quando o Mestre leva o grupo à cidade."
	show()
	_build_pins()
	_arrange()

func set_mode(value: String) -> void:
	mode = value if art.texture != null else "map"
	art.visible = mode == "town"
	city_map.visible = mode == "map"
	pins.visible = mode == "map"
	glow.hide()
	tag.hide()
	toggle.text = "Mapa da cidade" if mode == "town" else "Vista da cidade"
	toggle.visible = art.texture != null
	_arrange()

func pin(id: String) -> Dictionary:
	for token in city.get("tokens", []):
		if str(token.get("id")) == id: return token
	return {}

func _arrange() -> void:
	for picture in [art, city_map]:
		picture.position = Vector2(0, 54)
		picture.size = Vector2(size.x, maxf(100, size.y - 54 - 30))
	pins.position = city_map.position
	pins.size = city_map.size
	outline.position = Vector2.ZERO
	outline.size = size
	outline.queue_redraw()
	status.position = Vector2(20, size.y - 30)
	status.size = Vector2(size.x - 40, 24)
	_place_pins()
	if not hovered.is_empty(): _show_glow(hovered)

## Rect where the picture is actually drawn (keep-aspect, centered).
func _drawn(picture: TextureRect) -> Rect2:
	if picture.texture == null: return Rect2(picture.position, picture.size)
	var source = picture.texture.get_size()
	var factor = minf(picture.size.x / source.x, picture.size.y / source.y)
	var shown = source * factor
	return Rect2(picture.position + (picture.size - shown) / 2, shown)

func spot_at(point: Vector2) -> Dictionary:
	if mode != "town": return {}
	var rect = _drawn(art)
	if not rect.has_point(point): return {}
	var image_point = (point - rect.position) / rect.size * art_size
	for spot in spots:
		if spot.get("polygon") is Array and Geometry2D.is_point_in_polygon(image_point, _polygon(spot)):
			return spot
	if mask == null: return {}
	var local = (point - rect.position) / rect.size * Vector2(mask.get_width(), mask.get_height())
	var value = int(round(mask.get_pixel(clampi(int(local.x), 0, mask.get_width() - 1), clampi(int(local.y), 0, mask.get_height() - 1)).r * 255))
	if value <= 40: return {}
	var best: Dictionary = {}
	var gap = 999
	for spot in spots:
		var difference = absi(int(spot.get("mask", -1)) - value)
		if difference < gap and difference <= 10:
			gap = difference
			best = spot
	return best

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		var spot = spot_at(event.position)
		if spot != hovered:
			hovered = spot
			mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if not spot.is_empty() else Control.CURSOR_ARROW
			if spot.is_empty(): glow.hide(); tag.hide(); outline.queue_redraw()
			else: _show_glow(spot)
		if not spot.is_empty():
			tag.position = event.position + Vector2(16, -28)
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var spot = spot_at(event.position)
		if not spot.is_empty():
			hovered = spot
			_show_glow(spot)
			tag.position = event.position + Vector2(16, -28)
			activate(spot)
			accept_event()

func _polygon(spot: Dictionary) -> PackedVector2Array:
	var points = PackedVector2Array()
	for pair in spot.get("polygon", []):
		points.append(Vector2(float(pair[0]), float(pair[1])))
	return points

func _draw_outline() -> void:
	if hovered.is_empty() or not hovered.get("polygon") is Array or mode != "town": return
	var rect = _drawn(art)
	var scaled = PackedVector2Array()
	for point in _polygon(hovered):
		scaled.append(rect.position + point / art_size * rect.size)
	if scaled.size() < 3: return
	outline.draw_colored_polygon(scaled, Color(1.0, 0.82, 0.45, 0.16))
	var closed = scaled.duplicate()
	closed.append(scaled[0])
	outline.draw_polyline(closed, Color(1.0, 0.8, 0.4, 0.9), 2.5, true)

func _show_glow(spot: Dictionary) -> void:
	tag.text = str(spot.get("label", ""))
	tag.show()
	outline.queue_redraw()
	if spot.get("polygon") is Array:
		glow.hide()
		return
	var rect = _drawn(art)
	var source = art.texture.get_size() if art.texture else Vector2(640, 480)
	var factor = rect.size.x / source.x
	var light: Dictionary = spot.get("highlight", {}) if spot.get("highlight") is Dictionary else {}
	if light.get("texture") and ResourceLoader.exists(str(light.texture)):
		var texture: Texture2D = load(str(light.texture))
		glow.texture = texture
		glow.material.blend_mode = CanvasItemMaterial.BLEND_MODE_MIX
		glow.position = rect.position + Vector2(light.position[0], light.position[1]) * factor
		glow.size = texture.get_size() * factor
		glow.modulate = Color(1.15, 1.1, 1.0, 1.0)
	else:
		glow.texture = _region_glow(spot)
		glow.material.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		glow.position = rect.position
		glow.size = rect.size
		glow.modulate = Color(1, 1, 1, 1)
	glow.show()

## Generic hover light made from the mask itself: works with any swapped art.
func _region_glow(spot: Dictionary) -> Texture2D:
	var id = str(spot.get("id", ""))
	if glows.has(id) or mask == null: return glows.get(id)
	var target = int(spot.get("mask", -1))
	var light = Image.create(mask.get_width(), mask.get_height(), false, Image.FORMAT_RGBA8)
	for y in range(mask.get_height()):
		for x in range(mask.get_width()):
			var value = int(round(mask.get_pixel(x, y).r * 255))
			if value > 40 and absi(value - target) <= 10:
				light.set_pixel(x, y, Color(0.35, 0.27, 0.12, 1))
	glows[id] = ImageTexture.create_from_image(light)
	return glows[id]

func activate(spot: Dictionary) -> void:
	match str(spot.get("kind", "")):
		"city_map":
			set_mode("map")
		"exit":
			if master and active_on_table: exit_requested.emit()
			elif not active_on_table:
				hide()
				closed.emit()
			else:
				status.text = "O Mestre conduz a saída da cidade."
		_:
			place_opened.emit(spot, pin(str(spot.get("pin", ""))))

func _build_pins() -> void:
	for child in pins.get_children():
		pins.remove_child(child)
		child.queue_free()
	for token in city.get("tokens", []):
		if token.get("token_type") == "character": continue
		var button = Button.new()
		button.flat = true
		button.tooltip_text = str(token.get("name", ""))
		button.custom_minimum_size = Vector2(44, 44)
		button.expand_icon = true
		button.icon = load("res://assets/ui/maps.svg")
		button.set_meta("token", token)
		button.add_theme_constant_override("icon_max_width", 40)
		if media and token.get("image_path"):
			media.bind(token.image_path, button, "icon")
		var name = Label.new()
		name.text = str(token.get("name", ""))
		name.add_theme_font_size_override("font_size", 12)
		Gothic.shadowed(name)
		name.position = Vector2(-28, 42)
		name.size = Vector2(100, 16)
		name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		name.mouse_filter = Control.MOUSE_FILTER_IGNORE
		button.add_child(name)
		button.pressed.connect(func():
			var spot = {"id": "pin:" + str(token.id), "label": str(token.get("name", "")), "kind": "merchant" if token.get("token_type") == "monster" else "place", "pin": str(token.id)}
			for configured in spots:
				if str(configured.get("pin", "")) == str(token.id): spot = configured
			place_opened.emit(spot, token))
		pins.add_child(button)
	_place_pins()

func _place_pins() -> void:
	var rect = _drawn(city_map)
	for button in pins.get_children():
		var token: Dictionary = button.get_meta("token", {})
		var point = rect.position - pins.position + Vector2(float(token.get("longitude", 50)) / 100.0 * rect.size.x, float(token.get("latitude", 50)) / 100.0 * rect.size.y)
		button.position = point - Vector2(22, 22)
		button.size = Vector2(44, 44)
