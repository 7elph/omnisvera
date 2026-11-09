extends HBoxContainer
signal character_selected(id: String)
const Style = preload("res://scripts/ui_style.gd")
var media: Node
var signature: String = ""
var controlled_id: String = ""

static func online_characters(characters: Array, presence: Array) -> Array:
	var online: Dictionary = {}
	for user in presence:
		if user.get("online", false):
			online[str(user.get("character_id", ""))] = true
	return characters.filter(func(character: Dictionary): return online.has(str(character.get("id", ""))))

func update_roster(characters: Array, presence: Array) -> void:
	var people = online_characters(characters, presence).duplicate(true)
	var next_signature = JSON.stringify(people)
	if signature == next_signature:
		return
	signature = next_signature
	for child in get_children():
		remove_child(child)
		child.queue_free()
	for person in people:
		var button = Button.new()
		Style.icon_button(button, load("res://assets/ui/sheet.svg") if person.id == "master" else null, str(person.name) + (" · sob seu controle" if person.get("controlled", false) else ""), 40)
		button.set_meta("identity", str(person.id))
		if person.id != "master":
			button.text = str(person.name).substr(0, 1)
			if media and person.get("portrait"):
				button.text = ""
				button.icon = load("res://assets/ui/sheet.svg")
				media.bind(person.portrait, button, "icon")
			button.pressed.connect(func(): character_selected.emit(str(person.id)))
		var dot = Panel.new()
		var circle = StyleBoxFlat.new()
		circle.bg_color = Color("#8bc5f0") if person.get("controlled", false) else Color("#7ccb85")
		circle.set_corner_radius_all(5)
		dot.add_theme_stylebox_override("panel", circle)
		dot.position = Vector2(37, 37)
		dot.size = Vector2(8, 8)
		dot.mouse_filter = Control.MOUSE_FILTER_IGNORE
		button.add_child(dot)
		add_child(button)
