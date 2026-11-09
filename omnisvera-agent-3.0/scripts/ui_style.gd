extends RefCounted
static func icon_button(button: Button, texture: Texture2D, label: String, edge: int = 32) -> void:
	button.text = ""
	button.icon = texture
	button.tooltip_text = label
	button.expand_icon = true
	button.flat = true
	button.add_theme_constant_override("icon_max_width", edge)
	button.add_theme_stylebox_override("normal", StyleBoxEmpty.new())
	button.add_theme_stylebox_override("disabled", StyleBoxEmpty.new())
	for state in ["hover", "pressed", "hover_pressed", "focus"]:
		button.add_theme_stylebox_override(state, StyleBoxEmpty.new())
	button.add_theme_color_override("icon_normal_color", Color.WHITE)
	button.add_theme_color_override("icon_hover_color", Color.WHITE)
	button.add_theme_color_override("icon_pressed_color", Color("#8fd8b4"))
	button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	button.custom_minimum_size = Vector2(48, 46)

static func label(parent: Node, text: String, font_size: int = 15) -> Label:
	var item = Label.new()
	item.text = text
	item.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	item.add_theme_font_size_override("font_size", font_size)
	parent.add_child(item)
	return item

static func rom_frame(panel: PanelContainer) -> void:
	var path = "res://assets/rom2_local/ui/t_border-0.png"
	if not ResourceLoader.exists(path): return
	var border = NinePatchRect.new()
	border.name = "ROM2Border"
	border.texture = load(path)
	border.draw_center = false
	border.patch_margin_left = 12
	border.patch_margin_top = 14
	border.patch_margin_right = 12
	border.patch_margin_bottom = 14
	border.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(border)
	border.set_as_top_level(true)
	border.z_index = panel.z_index+1
