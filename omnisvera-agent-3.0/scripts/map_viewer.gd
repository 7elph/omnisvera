extends Control
## Read-only view of the existing map and its authorized pins, including fog.
signal pin_selected(pin: Dictionary)
const Style = preload("res://scripts/ui_style.gd")
var media: Node
var caption = Label.new()
var loading = Label.new()
var heading = HBoxContainer.new()
var surface: Control
var record: Dictionary = {}
var people: Array = []
var master: bool = false

class MapSurface extends Control:
	var texture: Texture2D:
		set(value):
			texture = value
			queue_redraw()
	var fog: Dictionary = {}
	var master: bool = false
	var bounds = Rect2()
	var pins: Array = []
	var image_zoom: float = 1.0
	var image_offset = Vector2.ZERO
	var dragging: bool = false

	func update_geometry() -> void:
		if not texture:
			bounds = Rect2()
			return
		var dimensions = texture.get_size()
		var scale = minf(size.x / dimensions.x, size.y / dimensions.y) * image_zoom
		bounds = Rect2((size - dimensions * scale) / 2 + image_offset, dimensions * scale)

	func _has_point(point: Vector2) -> bool:
		return bounds.has_point(point) if texture else false

	func zoom_at(factor: float, point: Vector2) -> void:
		update_geometry()
		var next_zoom = clampf(image_zoom * factor, 0.6, 4.0)
		var actual_factor = next_zoom / image_zoom
		image_offset = point + (bounds.get_center() - point) * actual_factor - size / 2
		image_zoom = next_zoom
		queue_redraw()

	func _gui_input(event: InputEvent) -> void:
		if event is InputEventMouseButton:
			if event.button_index == MOUSE_BUTTON_LEFT or event.button_index == MOUSE_BUTTON_MIDDLE:
				dragging = event.pressed
			elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP:
				zoom_at(1.12, event.position)
			elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				zoom_at(1.0 / 1.12, event.position)
		elif event is InputEventMouseMotion and dragging:
			image_offset += event.relative
			queue_redraw()
		elif event is InputEventMagnifyGesture:
			zoom_at(event.factor, event.position)
		accept_event()

	func _draw() -> void:
		update_geometry()
		if not texture:
			return
		draw_texture_rect(texture, bounds, false)
		if not master:
			for layer in fog.values():
				if not layer.get("enabled", false):
					continue
				var cols = maxi(1, int(layer.get("columns", 32)))
				var rows = maxi(1, int(layer.get("rows", 24)))
				var revealed: Array = layer.get("revealed_cells", [])
				var density: Dictionary = layer.get("mist_density", {})
				for y in range(rows):
					for x in range(cols):
						var key = "%d:%d" % [x, y]
						var opacity = float(density.get(key, 0)) if not density.is_empty() else (1.0 if not revealed.is_empty() and not key in revealed else 0.0)
						if opacity > 0:
							draw_rect(Rect2(bounds.position + Vector2(x, y) * bounds.size / Vector2(cols, rows), bounds.size / Vector2(cols, rows) + Vector2.ONE), Color(0.025, 0.04, 0.04, clampf(opacity, 0, 1)))
		for button in pins:
			button.show()
			var pin: Dictionary = button.get_meta("pin")
			button.position = bounds.position + Vector2(float(pin.get("longitude", 50)), float(pin.get("latitude", 50))) / 100 * bounds.size - button.size / 2

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	surface = MapSurface.new()
	surface.clip_contents = true
	add_child(surface)
	surface.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	surface.resized.connect(surface.queue_redraw)
	add_child(heading)
	heading.mouse_filter = Control.MOUSE_FILTER_IGNORE
	caption.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	caption.clip_text = true
	caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
	caption.add_theme_constant_override("outline_size", 4)
	caption.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	heading.add_child(caption)
	var close = Button.new()
	Style.icon_button(close, load("res://assets/ui/close.svg"), "Fechar mapa", 24)
	close.pressed.connect(hide)
	heading.add_child(close)
	loading.text = "Carregando mapa…"
	loading.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	loading.mouse_filter = Control.MOUSE_FILTER_IGNORE
	loading.add_theme_constant_override("outline_size", 4)
	loading.add_theme_color_override("font_outline_color", Color.BLACK)
	add_child(loading)
	hide()

func present(snapshot: Dictionary, characters: Array, is_master: bool) -> void:
	record = snapshot
	people = characters
	master = is_master
	var map: Dictionary = snapshot.get("map") if snapshot.get("map") is Dictionary else {}
	caption.text = str(map.get("title", "Mapa indisponível"))
	loading.text = "Carregando mapa…"
	surface.texture = null
	surface.image_zoom = 1.0
	surface.image_offset = Vector2.ZERO
	surface.dragging = false
	surface.fog = snapshot.get("fog", {})
	surface.master = master
	for button in surface.pins:
		surface.remove_child(button)
		button.queue_free()
	surface.pins.clear()
	if map.get("image_path"):
		media.bind(map.image_path, surface, "texture", 768)
	for pin in snapshot.get("tokens", []):
		var button = Button.new()
		Style.icon_button(button, load("res://assets/ui/sheet.svg"), str(pin.get("name", "Pin")), 36)
		button.set_meta("pin", pin)
		button.hide()
		var portrait = pin.get("image_path")
		for character in characters:
			if character.get("id") == pin.get("character_id") and not portrait:
				portrait = character.get("portrait")
		if portrait:
			media.bind(portrait, button, "icon")
		button.pressed.connect(func(): pin_selected.emit(pin))
		surface.add_child(button)
		surface.pins.append(button)
	surface.queue_redraw()
	show()

func _process(_delta: float) -> void:
	if visible:
		loading.visible = surface.texture == null
		surface.update_geometry()
		var visible_image = surface.bounds.intersection(Rect2(Vector2.ZERO, size))
		if visible_image.size.x < 64 or visible_image.size.y < 48:
			visible_image = Rect2(Vector2.ZERO, size)
		heading.position = visible_image.position + Vector2(8, 0)
		heading.size = Vector2(maxf(48, visible_image.size.x - 16), 46)
		loading.size = Vector2(minf(400, size.x - 32), 60)
		loading.position = (size - loading.size) / 2

func media_failed(path: String) -> void:
	var map: Dictionary = record.get("map") if record.get("map") is Dictionary else {}
	if path == media.media_path(map.get("image_path"), 768):
		loading.text = "Não foi possível carregar a imagem. Reabra o mapa para tentar novamente."

func clear() -> void:
	hide()
	record.clear()
	surface.texture = null
	for button in surface.pins:
		button.queue_free()
	surface.pins.clear()
