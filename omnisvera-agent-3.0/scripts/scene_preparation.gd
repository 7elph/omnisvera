extends RefCounted
signal changed
var scene: Dictionary = {}
var pins: Array = []
var element_ids: Array = []
var token_ids: Array = []
var include_map: bool = false
var library: Node = null   # LibraryController: places the prepared cast on the map

func select(record: Dictionary) -> void:
	scene = record.duplicate(true)
	pins.clear()
	element_ids.clear()
	token_ids.clear()
	include_map = false

func payload() -> Dictionary:
	return {"element_ids":element_ids.duplicate(),"token_ids":token_ids.duplicate(),"include_map":include_map}

func _toggle(list: Array, id: Variant, on: bool) -> void:
	if on and not id in list: list.append(id)
	elif not on: list.erase(id)
	changed.emit()

func render(body: Node, content: RefCounted, preview: Callable, send: Callable) -> void:
	var style = preload("res://scripts/ui_style.gd")
	style.label(body,str(scene.get("title","Cena")),21)
	if scene.get("public_description"): style.label(body,str(scene.public_description))
	if scene.get("private_notes"):
		style.label(body,"Notas do Mestre",17)
		style.label(body,str(scene.private_notes))
	if scene.get("map_id"):
		var row = HBoxContainer.new()
		body.add_child(row)
		var check = CheckBox.new()
		check.text = "Incluir mapa"
		check.button_pressed = include_map
		check.toggled.connect(func(on): include_map=on; changed.emit())
		row.add_child(check)
		var view = Button.new()
		view.text = "Ver mapa e pins"
		view.pressed.connect(func(): preview.call(str(scene.map_id)))
		row.add_child(view)
	for record in scene.get("elements",[]):
		var row = VBoxContainer.new()
		body.add_child(row)
		var check = CheckBox.new()
		check.text = str(record.get("title","Elemento"))
		check.button_pressed = int(record.id) in element_ids
		check.toggled.connect(func(on): _toggle(element_ids,int(record.id),on))
		row.add_child(check)
		if record.get("public_description"): style.label(row,str(record.public_description),14)
		if record.get("private_description") and not str(record.private_description).begins_with("item:"):
			style.label(row,"Mestre: "+str(record.private_description),13)
		if library and str(record.get("private_description","")).begins_with("item:"):
			var give = Button.new()
			give.text = "Entregar item"
			give.pressed.connect(func(): library.grant_scene_item(record))
			row.add_child(give)
	var cast: Array = scene.get("participants",[]).filter(func(p): return p is Dictionary and str(p.get("participant_type","")) in ["npc","creature"])
	if not cast.is_empty():
		style.label(body,"Elenco preparado",17)
	for participant in cast:
		var row = HBoxContainer.new()
		body.add_child(row)
		var name = Label.new()
		name.text = ("☺ " if participant.get("participant_type") == "npc" else "⚔ ") + str(participant.get("public_label",participant.get("npc_name","")))
		name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		name.clip_text = true
		row.add_child(name)
		if library:
			var put = Button.new()
			put.text = "No mapa"
			put.pressed.connect(func(): library.place_participant(participant))
			row.add_child(put)
	if library:
		var open = Button.new()
		open.text = "Biblioteca: monstros, NPCs, itens, magias, mapas"
		open.pressed.connect(func(): library.host._open_panel("library"))
		body.add_child(open)
	for pin in pins:
		var row = HBoxContainer.new()
		body.add_child(row)
		content.image(row,pin.get("image_path"),40)
		var check = CheckBox.new()
		check.text = str(pin.get("name","Pin"))
		check.button_pressed = str(pin.id) in token_ids
		check.toggled.connect(func(on): _toggle(token_ids,str(pin.id),on))
		row.add_child(check)
	var button = Button.new()
	button.text = "Enviar seleção à mesa"
	button.disabled = not include_map and element_ids.is_empty() and token_ids.is_empty()
	button.pressed.connect(send)
	body.add_child(button)
