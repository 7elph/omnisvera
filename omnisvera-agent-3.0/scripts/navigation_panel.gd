extends ScrollContainer
signal panel_requested(panel: String)
const Style = preload("res://scripts/ui_style.gd")
var buttons: Dictionary = {}
var column = GridContainer.new()

func _ready() -> void:
	horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	column.columns = 1
	column.add_theme_constant_override("h_separation", 6)
	column.add_theme_constant_override("v_separation", 4)
	add_child(column)
	for entry in [["sheet", "Ficha"], ["spells", "Poderes: ataques, magias e habilidades"],
		["items", "Inventário"], ["dice", "Dados e testes"], ["combat", "Combate"], ["city", "Cidade"], ["maps", "Mapas"],
		["editor", "Editor de mapas"], ["sessions", "Sessões"], ["gm", "Ferramentas do Mestre"]]:
		var button = TextureButton.new()
		button.custom_minimum_size = Vector2(56, 54)
		button.tooltip_text = entry[1]
		button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		var icon = TextureRect.new()
		icon.texture = load("res://assets/ui/" + entry[0] + (".svg" if entry[0] in ["editor", "city", "dice"] else ".png"))
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
		icon.position = Vector2(6, 5)
		icon.size = Vector2(44, 44)
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		button.add_child(icon)
		button.pressed.connect(func(): panel_requested.emit(entry[0]))
		column.add_child(button)
		buttons[entry[0]] = button
	buttons.gm.visible = false
	buttons.city.visible = false

func set_master(master: bool) -> void:
	buttons.gm.visible = master
	buttons.editor.visible = master
	buttons.city.visible = master  # players enter by walking up to the city on the map

func fit_height(height: float) -> void:
	column.columns = 2 if height < 500 else 1
	size = Vector2(118 if column.columns == 2 else 56, minf(column.get_combined_minimum_size().y, height - 64))
