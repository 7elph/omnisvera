extends RefCounted
## Dark "Diablo-like" visual language. Presentation only.
const INK := Color("#e9d9b4")
const GOLD := Color("#d4a85a")
const GOLD_DIM := Color("#7a5c2c")
const BLOOD := Color("#a3261f")
const MANA := Color("#2f5fb8")
const STONE := Color("#15100c")
const STONE_HI := Color("#2a1f16")
const GOOD := Color("#7fc77d")

static func panel_box(alpha: float = 0.95, radius: int = 4) -> StyleBoxFlat:
	var style = StyleBoxFlat.new()
	style.bg_color = Color(STONE, alpha)
	style.border_color = GOLD_DIM
	style.set_border_width_all(2)
	style.set_corner_radius_all(radius)
	style.shadow_color = Color(0, 0, 0, 0.55)
	style.shadow_size = 8
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 12
	style.content_margin_bottom = 12
	return style

static func button_box(state: String) -> StyleBoxFlat:
	var style = StyleBoxFlat.new()
	style.bg_color = {"normal": Color("#1d1510"), "hover": Color("#33251a"), "pressed": Color("#4a3320"), "focus": Color("#1d1510"), "disabled": Color("#120d0a")}.get(state, Color("#1d1510"))
	style.border_color = GOLD if state in ["hover", "pressed"] else (Color("#3a2c1c") if state == "disabled" else GOLD_DIM)
	style.set_border_width_all(1)
	style.border_width_bottom = 2
	style.set_corner_radius_all(3)
	style.content_margin_left = 10
	style.content_margin_right = 10
	style.content_margin_top = 7
	style.content_margin_bottom = 7
	return style

static func build() -> Theme:
	var theme = Theme.new()
	theme.default_font_size = 15
	theme.set_stylebox("panel", "PanelContainer", panel_box())
	theme.set_stylebox("panel", "Panel", panel_box())
	for state in ["normal", "hover", "pressed", "focus", "disabled"]:
		theme.set_stylebox(state, "Button", button_box(state))
		theme.set_stylebox(state, "OptionButton", button_box(state))
	theme.set_color("font_color", "Button", INK)
	theme.set_color("font_hover_color", "Button", Color("#fff1cf"))
	theme.set_color("font_pressed_color", "Button", GOLD)
	theme.set_color("font_disabled_color", "Button", Color("#6d5f4a"))
	theme.set_color("font_color", "Label", INK)
	theme.set_color("font_color", "CheckBox", INK)
	theme.set_color("font_color", "LineEdit", INK)
	var field = StyleBoxFlat.new()
	field.bg_color = Color("#0d0907")
	field.border_color = GOLD_DIM
	field.set_border_width_all(1)
	field.set_corner_radius_all(3)
	field.content_margin_left = 8
	field.content_margin_right = 8
	field.content_margin_top = 6
	field.content_margin_bottom = 6
	theme.set_stylebox("normal", "LineEdit", field)
	theme.set_stylebox("focus", "LineEdit", field)
	var popup = panel_box(0.98)
	theme.set_stylebox("panel", "PopupPanel", popup)
	theme.set_stylebox("panel", "AcceptDialog", popup)
	theme.set_stylebox("embedded_border", "Window", popup)
	theme.set_color("title_color", "Window", GOLD)
	return theme

static func title(label: Label, size: int = 20) -> Label:
	label.add_theme_color_override("font_color", GOLD)
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
	label.add_theme_constant_override("shadow_offset_x", 1)
	label.add_theme_constant_override("shadow_offset_y", 2)
	return label

static func shadowed(label: Label) -> Label:
	label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.95))
	label.add_theme_constant_override("shadow_offset_x", 1)
	label.add_theme_constant_override("shadow_offset_y", 1)
	label.add_theme_constant_override("shadow_outline_size", 4)
	return label
