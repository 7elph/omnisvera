extends RefCounted
## UI projection only. Mechanics, permissions and narrative come from the server.
const Style = preload("res://scripts/ui_style.gd")
const Icons = preload("res://scripts/icon_catalog.gd")
var media: Node
var details: Callable
var open_map: Callable
var open_session: Callable
var activate: Callable

static func number(value: Variant) -> String:
	return str(int(value)) if value is float and is_equal_approx(value, roundf(value)) else str(value)

func image(parent: Node, path: Variant, edge: int = 56, fallback: String = "sheet") -> TextureRect:
	var icon = TextureRect.new()
	icon.custom_minimum_size = Vector2(edge, edge)
	icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	icon.texture = load("res://assets/ui/" + fallback + ".svg")
	parent.add_child(icon)
	media.bind(path, icon)
	return icon

func card(parent: Node, name: String, art: Variant, subtitle: String, action: Callable, fallback: String = "sheet") -> Button:
	var button = Button.new()
	button.custom_minimum_size = Vector2(0, 68)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.tooltip_text = name
	button.pressed.connect(action)
	parent.add_child(button)
	var row = HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	row.offset_left = 8
	row.offset_right = -8
	row.offset_top = 6
	row.offset_bottom = -6
	row.add_theme_constant_override("separation", 12)
	button.add_child(row)
	image(row, art, 48, fallback)
	var text = VBoxContainer.new()
	text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(text)
	for pair in [[name, 17], [subtitle, 13]]:
		var label = Style.label(text, pair[0], pair[1])
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		label.max_lines_visible = 2
	return button

func show_detail(record: Dictionary) -> void:
	details.call(record)

func ficha(body: Node, definition: Dictionary, state: Dictionary, items: Array = [], sprite_preview: Control = null) -> void:
	var heading = HBoxContainer.new()
	body.add_child(heading)
	if sprite_preview:
		heading.add_child(sprite_preview)
	else:
		image(heading, definition.get("portrait"), 56)
	var copy = VBoxContainer.new()
	copy.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	heading.add_child(copy)
	Style.label(copy, str(definition.get("name", "")), 23)
	if definition.get("epithet"):
		Style.label(copy, str(definition.epithet), 14)
	Style.label(copy, "%s · Nível %s" % [definition.get("class_name", ""), number(definition.get("level", "—"))])
	var tags = HFlowContainer.new()
	body.add_child(tags)
	for identity in definition.get("identity_cards", {}).values():
		var chip = Button.new()
		chip.text = str(identity.get("name", ""))
		chip.custom_minimum_size.y = 40
		chip.expand_icon = true
		chip.add_theme_constant_override("icon_max_width", 28)
		media.bind(identity.get("image_path"), chip, "icon")
		chip.pressed.connect(func(): show_detail(identity))
		tags.add_child(chip)
	if not state.is_empty():
		hp_bar(body, state.get("current_hp"), state.get("maximum_hp"))
		for condition in state.get("conditions", []):
			Style.label(body, str(condition), 14)
	var defense: Dictionary = definition.get("defenses", {})
	Style.label(body, "CA %s  ·  JP %s  ·  %s" % [number(defense.get("armor_class", "—")), number(defense.get("saving_throw", "—")), definition.get("movement", "")])
	var attributes = GridContainer.new()
	attributes.columns = 2
	attributes.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	attributes.add_theme_constant_override("h_separation", 24)
	body.add_child(attributes)
	var labels = {"strength": "FOR", "dexterity": "DES", "constitution": "CON", "intelligence": "INT", "wisdom": "SAB", "charisma": "CAR"}
	for attribute in definition.get("attributes", {}):
		var field = Style.label(attributes, "%s  %s" % [labels.get(attribute, attribute), number(definition.attributes[attribute])], 17)
		field.custom_minimum_size.x = 150
		field.autowrap_mode = TextServer.AUTOWRAP_OFF
	var equipped: Array = []
	for item in items:
		if item.get("equipped", false):
			equipped.append(item)
	if not equipped.is_empty():
		Style.label(body, "Equipamentos", 18)
		inventory(body, equipped)
	if not state.get("resources", []).is_empty():
		Style.label(body, "Recursos", 18)
		var resources = HFlowContainer.new()
		body.add_child(resources)
		for resource in state.resources:
			var art: Variant = null
			for ability in definition.get("session_abilities", []):
				if ability.get("uses") is Dictionary and ability.uses.get("resource_key") == resource.get("key"):
					art = ability.get("image_path")
					break
			var entry = VBoxContainer.new()
			entry.custom_minimum_size.x = 84
			resources.add_child(entry)
			var icon = image(entry, art, 40, "spells")
			icon.tooltip_text = str(resource.get("label", resource.get("name", resource.get("key", ""))))
			Style.label(entry, "%s/%s" % [number(resource.get("current", 0)), number(resource.get("maximum", 0))], 14)
	# Lore in one place: hover shows the short description, click opens everything.
	var sections: Array = []
	for pair in [["public_description", "Descrição"], ["history", "História"], ["physical_description", "Aparência"], ["personality", "Personalidade"], ["relationships", "Relações"], ["goals", "Objetivos"], ["location", "Localização"]]:
		if definition.get(pair[0]):
			sections.append("%s\n%s" % [pair[1].to_upper(), str(definition[pair[0]])])
	if not sections.is_empty():
		var about = Button.new()
		about.icon = load("res://assets/ui/sessions.svg")
		about.text = "Sobre o personagem"
		about.expand_icon = true
		about.add_theme_constant_override("icon_max_width", 22)
		about.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		about.tooltip_text = str(definition.get("public_description", sections[0])).left(220)
		var info = {"name": str(definition.get("name", "")), "description": "\n\n".join(sections), "image_path": definition.get("portrait")}
		about.pressed.connect(func(): show_detail(info))
		body.add_child(about)

## Red life bar; the numbers are in the tooltip.
static func hp_bar(parent: Node, current: Variant, maximum: Variant, height: float = 14) -> ProgressBar:
	var bar = ProgressBar.new()
	bar.show_percentage = false
	bar.max_value = maxf(1, float(maximum) if maximum != null else 1.0)
	bar.value = clampf(float(current) if current != null else 0.0, 0, bar.max_value)
	bar.custom_minimum_size = Vector2(120, height)
	bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bar.tooltip_text = "Vida %s / %s" % [number(current if current != null else "—"), number(maximum if maximum != null else "—")]
	var back = StyleBoxFlat.new()
	back.bg_color = Color(0.08, 0.03, 0.03)
	back.border_color = Color(0.48, 0.36, 0.17)
	back.set_border_width_all(1)
	back.set_corner_radius_all(3)
	var fill = StyleBoxFlat.new()
	fill.bg_color = Color(0.62, 0.07, 0.06)
	fill.set_corner_radius_all(3)
	bar.add_theme_stylebox_override("background", back)
	bar.add_theme_stylebox_override("fill", fill)
	parent.add_child(bar)
	return bar

func attacks(body: Node, definition: Dictionary) -> void:
	for attack in definition.get("attacks", []):
		var art: Variant = null
		var equipment: Array = attack.get("equipment", [])
		if not equipment.is_empty():
			art = Icons.item_art(equipment[0])
		var info = attack.duplicate(true)
		info.image_path = art
		info.description = "Ataque %+d · Dano %s\nAlcance: %s\n%s" % [int(attack.get("attack_bonus", 0)), attack.get("damage", "—"), attack.get("range") if attack.get("range") else "Corpo a corpo", attack.get("notes") if attack.get("notes") else ""]
		card(body, str(attack.get("name", "Ataque")), art, "%+d · %s" % [int(attack.get("attack_bonus", 0)), attack.get("damage", "—")], func(): show_detail(info))

func spells(body: Node, definition: Dictionary, state: Dictionary) -> void:
	for ability in definition.get("session_abilities", []):
		var uses = "Passiva" if not ability.get("active", false) else ""
		var usage: Dictionary = ability.get("uses", {}) if ability.get("uses") is Dictionary else {}
		for resource in state.get("resources", []):
			if usage.get("resource_key") and resource.get("key") == usage.get("resource_key"):
				uses = "%s/%s" % [resource.get("current", 0), resource.get("maximum", 0)]
		card(body, str(ability.get("name", "Habilidade")), ability.get("image_path"), ("Usar · " if ability.get("active", false) else "") + uses,
			func(): activate.call(ability) if ability.get("active", false) and activate.is_valid() else show_detail(ability))

func inventory(body: Node, items: Array) -> void:
	var icons = GridContainer.new()
	icons.columns = 6
	icons.add_theme_constant_override("h_separation", 10)
	icons.add_theme_constant_override("v_separation", 10)
	body.add_child(icons)
	for item in items:
		if int(item.get("quantity", 0)) <= 0:
			continue
		var button = Button.new()
		Style.icon_button(button, load("res://assets/ui/items.svg"), str(item.get("item_title", "Item")), 46)
		button.custom_minimum_size = Vector2(56, 62)
		var art = Icons.item_art(item)
		media.bind(art, button, "icon")
		var count = Label.new()
		count.text = number(item.get("quantity", 0))
		count.position = Vector2(40, 42)
		count.mouse_filter = Control.MOUSE_FILTER_IGNORE
		button.add_child(count)
		if item.get("equipped", false):
			var equipped = StyleBoxFlat.new()
			equipped.bg_color = Color(0, 0, 0, 0)
			equipped.border_color = Color("#8dbfa8")
			equipped.set_border_width_all(1)
			equipped.set_corner_radius_all(5)
			button.add_theme_stylebox_override("normal", equipped)
		var info = item.duplicate(true)
		info.name = item.get("item_title", "Item")
		info.image_path = art
		info.description = str(item.get("description", "")) + "\n" + "\n".join(item.get("effects", []))
		button.pressed.connect(func(): show_detail(info))
		icons.add_child(button)

func maps(body: Node, entries: Array, master: bool) -> void:
	for map in entries:
		card(body, str(map.get("title", "Mapa")), map.get("image_path") if master else null, "Abrir mapa e pins", func(): open_map.call(str(map.id)), "maps")

func sessions(body: Node, entries: Array) -> void:
	for session in entries:
		var states = {"active": "Em andamento", "completed": "Concluída", "planned": "Planejada", "paused": "Pausada"}
		card(body, str(session.get("title", "Sessão")), session.get("image_path"), str(states.get(session.get("status"), "")), func(): open_session.call(int(session.id)), "sessions")

func session_detail(body: Node, session: Dictionary, master: bool) -> void:
	if session.get("image_path"):
		var cover = image(body, session.image_path, 180)
		media.bind(session.image_path, cover, "texture", 768)
	Style.label(body, str(session.get("title", "Sessão")), 22)
	for key in ["public_summary", "public_chronicle"]:
		if session.get(key):
			Style.label(body, str(session[key]))
	var narrative: Dictionary = session.get("narrative", {})
	for pair in [["participants", "Participantes"], ["locations", "Locais"], ["missions", "Missões"], ["discoveries", "Descobertas"], ["items_acquired", "Itens"], ["world_events", "Acontecimentos"], ["open_threads", "Pendências narrativas"]]:
		if not narrative.get(pair[0], []).is_empty():
			Style.label(body, pair[1], 18)
			for entry in narrative[pair[0]]:
				Style.label(body, str(entry.get("name", entry.get("title", ""))) + "\n" + str(entry.get("description", "")))
	if master:
		for pair in [["gm_summary", "Resumo do Mestre"], ["private_notes", "Notas privadas"]]:
			if session.get(pair[0]):
				Style.label(body, pair[1], 18)
				Style.label(body, str(session[pair[0]]))
