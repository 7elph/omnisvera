extends Control
## Bottom-center vitals bar: the life potion (its liquid level is the HP), the belt and the notes button.
## Values come from the authorized sheet read; the numbers only appear in the tooltip.
signal belt_pressed(item: Dictionary)
signal slot_pressed(entry: Dictionary)
signal portrait_pressed
signal notes_pressed
const Gothic = preload("res://scripts/gothic_theme.gd")
const Icons = preload("res://scripts/icon_catalog.gd")
var SLOTS: int = 6  # the battle bar raises it to fit every action
var slot_size: float = 44.0
var media: Node
var hp: float = 0
var hp_max: float = 0
var shown_hp: float = -1
var caption = Label.new()
var potion = TextureRect.new()
var potion_material = ShaderMaterial.new()
var notes_button = Button.new()
var belt = HBoxContainer.new()
var belt_signature: String = ""

const POTION_SHADER = """
shader_type canvas_item;
uniform float level : hint_range(0.0, 1.0) = 1.0;
uniform float top = 0.40;     // liquid surface when full (UV.y)
uniform float bottom = 0.97;  // bottom of the flask
void fragment() {
	vec4 c = texture(TEXTURE, UV);
	float red = c.r - max(c.g, c.b);
	float surface = mix(bottom, top, level);
	if (red > 0.12 && UV.y < surface) {
		float lum = dot(c.rgb, vec3(0.3, 0.45, 0.25));
		c.rgb = vec3(lum * 0.45) + vec3(0.03, 0.02, 0.02);
	} else if (red > 0.12 && UV.y < surface + 0.012) {
		c.rgb = mix(c.rgb, vec3(1.0, 0.55, 0.45), 0.6);
	}
	COLOR = c;
}
"""

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	Gothic.shadowed(caption)
	caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
	caption.add_theme_color_override("font_color", Gothic.GOLD)
	caption.add_theme_font_size_override("font_size", 13)
	add_child(caption)
	var shader = Shader.new()
	shader.code = POTION_SHADER
	potion_material.shader = shader
	potion.material = potion_material
	potion.texture = load("res://assets/ui/art/potion_hp.png")
	potion.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	potion.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	potion.mouse_filter = Control.MOUSE_FILTER_STOP
	potion.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	potion.gui_input.connect(func(event):
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT: portrait_pressed.emit())
	add_child(potion)
	notes_button.flat = true
	notes_button.icon = load("res://assets/ui/sessions.svg")
	notes_button.expand_icon = true
	notes_button.tooltip_text = "Anotações do personagem"
	notes_button.custom_minimum_size = Vector2(28, 28)
	notes_button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	notes_button.pressed.connect(func(): notes_pressed.emit())
	add_child(notes_button)
	belt.add_theme_constant_override("separation", 4)
	belt.alignment = BoxContainer.ALIGNMENT_CENTER
	add_child(belt)
	resized.connect(_arrange)

## Width the bar wants; main._layout centers it.
func preferred_width() -> float:
	return 64 + SLOTS * (slot_size + 4) + 24

static func slot_style() -> StyleBox:
	var frame = StyleBoxTexture.new()
	frame.texture = load("res://assets/ui/art/slot_frame.png")
	for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]:
		frame.set_texture_margin(side, 18)
		frame.set_content_margin(side, 5)
	return frame

func set_vitals(name: String, _art: Variant, current: Variant, maximum: Variant, _resource: Dictionary, items: Array) -> void:
	caption.text = name
	hp = float(current) if current != null else 0.0
	hp_max = float(maximum) if maximum != null else 0.0
	potion.tooltip_text = ("Vida %d / %d" % [int(hp), int(hp_max)]) if hp_max > 0 else "Vida —"
	if shown_hp < 0:
		shown_hp = hp / hp_max if hp_max > 0 else 0.0
		potion_material.set_shader_parameter("level", shown_hp)
	if not custom_slots: _fill(items, false)
	_arrange()

var custom_slots: bool = false

## Ordered bar entries: {"kind": "item"|"action", "name", "image_path"|"icon", ...}. Pressing emits slot_pressed.
func set_slots(entries: Array) -> void:
	custom_slots = true
	_fill(entries, true)
	_arrange()

func _fill(items: Array, generic: bool) -> void:
	var signature = JSON.stringify(items) + str(generic)
	if signature != belt_signature:
		belt_signature = signature
		for child in belt.get_children():
			belt.remove_child(child)
			child.queue_free()
		for index in range(SLOTS):
			var slot = Button.new()
			slot.custom_minimum_size = Vector2(slot_size, slot_size)
			slot.expand_icon = true
			slot.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
			slot.vertical_icon_alignment = VERTICAL_ALIGNMENT_CENTER
			for state in ["normal", "hover", "pressed", "disabled", "focus"]:
				slot.add_theme_stylebox_override(state, slot_style())
			if index < items.size():
				var item: Dictionary = items[index]
				var quantity = (" ×%d" % int(item.quantity)) if item.get("quantity") != null else ""
				slot.tooltip_text = str(item.get("item_title", item.get("name", "Item"))) + quantity
				slot.icon = load(str(item.get("icon", "res://assets/ui/items.svg")))
				var art = item.get("image_path") if generic else Icons.item_art(item)
				if media and art:
					media.bind(art, slot, "icon")
				if generic: slot.pressed.connect(func(): slot_pressed.emit(item))
				else: slot.pressed.connect(func(): belt_pressed.emit(item))
			else:
				slot.disabled = true
				slot.tooltip_text = "Vazio"
			belt.add_child(slot)

func _arrange() -> void:
	var potion_h = size.y - 4
	potion.size = Vector2(potion_h * 0.64, potion_h)
	potion.position = Vector2(6, size.y - potion_h)
	notes_button.position = Vector2(potion.position.x + potion.size.x - 6, size.y - 34)
	var belt_x = potion.position.x + potion.size.x + 22
	belt.position = Vector2(belt_x, size.y - slot_size - 8)
	belt.size = Vector2(size.x - belt_x - 10, slot_size)
	caption.position = Vector2(belt_x, size.y - slot_size - 30)
	caption.size = Vector2(size.x - belt_x - 10, 18)
	queue_redraw()

func _process(delta: float) -> void:
	var target = hp / hp_max if hp_max > 0 else 0.0
	if shown_hp >= 0 and not is_equal_approx(shown_hp, target):
		shown_hp = move_toward(shown_hp, target, delta * 0.8)
		potion_material.set_shader_parameter("level", clampf(shown_hp, 0, 1))

func _draw() -> void:
	# Dark stone tray behind the belt, tucked under the potion's shoulder.
	var tray = Rect2(potion.position.x + potion.size.x * 0.55, size.y - slot_size - 14, size.x - potion.size.x * 0.55 - 6, slot_size + 12)
	var style = StyleBoxFlat.new()
	style.bg_color = Color(Gothic.STONE, 0.92)
	style.border_color = Gothic.GOLD_DIM
	style.set_border_width_all(2)
	style.set_corner_radius_all(6)
	draw_style_box(style, tray)
