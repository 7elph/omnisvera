extends Node
## Vitals bar (HP potion, notes, belt/action slots) for the character this client controls.
var host: Node
var view = preload("res://scripts/hud_orbs.gd").new()
var sheet: Dictionary = {}
var notes_dialog = AcceptDialog.new()
var notes_text = TextEdit.new()
var notes_version: int = 0
var notes_owner: String = ""
var kept_draft: String = ""

func setup(main: Node) -> void:
	host = main
	view.media = host.media
	host.screen.add_child(view)
	view.belt_pressed.connect(func(item): host._show_detail(item))
	view.portrait_pressed.connect(func():
		host.selected_id = controlled_id()
		host._open_panel("sheet"))
	view.notes_pressed.connect(open_notes)
	view.slot_pressed.connect(func(entry): host.powers.use_from_bar(entry) if host.powers.has_method("use_from_bar") else host._show_detail(entry))
	view.hide()
	notes_dialog.title = "Anotações"
	notes_dialog.ok_button_text = "Salvar"
	notes_dialog.add_cancel_button("Fechar")
	notes_text.custom_minimum_size = Vector2(360, 220)
	notes_text.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	notes_text.placeholder_text = "Escreva aqui o que seu personagem quer lembrar…"
	notes_dialog.add_child(notes_text)
	notes_dialog.confirmed.connect(save_notes)
	host.screen.add_child(notes_dialog)

func controlled_id() -> String:
	return host.my_profile if not host.master else host.selected_id

func handles(key: String) -> bool:
	return key in ["hud-sheet", "hud-notes", "hud-notes-save"]

func received(key: String, data: Variant) -> void:
	if key == "hud-notes":
		var payload: Dictionary = data if data is Dictionary else {}
		notes_version = int(payload.get("version", 0))
		notes_text.text = kept_draft if kept_draft != "" else str(payload.get("content", ""))
		kept_draft = ""
		notes_text.editable = true
		return
	if key == "hud-notes-save":
		var saved: Dictionary = data if data is Dictionary else {}
		notes_version = int(saved.get("version", notes_version + 1))
		host._notice("Anotações salvas.")
		return
	if data is Dictionary and str(data.get("definition", {}).get("id", "")) == controlled_id():
		sheet = data
		render()

func failed(key: String, message: String, code: int) -> bool:
	if key == "hud-notes-save":
		host._notice("Outra pessoa salvou antes; recarreguei as anotações. Seu texto continua na caixa." if code == 409 else message)
		if code == 409:
			kept_draft = notes_text.text
			host.api.request_json("hud-notes", "/characters/" + notes_owner.uri_encode() + "/notes")
			notes_dialog.popup_centered()
		return true
	return key in ["hud-sheet", "hud-notes"]

func open_notes() -> void:
	notes_owner = controlled_id()
	if notes_owner == "": return
	notes_text.text = "Carregando…"
	notes_text.editable = false
	notes_dialog.title = "Anotações · " + str(sheet.get("definition", {}).get("name", ""))
	host.api.request_json("hud-notes", "/characters/" + notes_owner.uri_encode() + "/notes")
	notes_dialog.popup_centered()

func save_notes() -> void:
	if notes_owner == "" or not notes_text.editable: return
	host.api.request_json("hud-notes-save", "/characters/" + notes_owner.uri_encode() + "/notes", HTTPClient.METHOD_PUT,
		{"content": notes_text.text.left(20000), "version": notes_version})

func load_sheet() -> void:
	var id = controlled_id()
	if host.authenticated and id != "":
		host.api.request_json("hud-sheet", "/characters/" + id.uri_encode() + "?read_only=true")

func state() -> Dictionary:
	return sheet.get("state") if sheet.get("state") is Dictionary else {}

func render() -> void:
	var definition: Dictionary = sheet.get("definition", {})
	var resources: Array = state().get("resources", [])
	var belt: Array = []
	var ability_art: Dictionary = {}
	for ability in definition.get("session_abilities", []):
		if ability is Dictionary and ability.get("image_path"): ability_art[str(ability.get("id", ""))] = ability.image_path
	for entry in sheet.get("inventory", []):
		var item: Dictionary = entry.duplicate()
		# Same as the 2.0 table: the repair kit shows the "Reparo" ability art.
		if str(item.get("item_title", "")) == "Kit de Reparo" and not item.get("image_path") and ability_art.has("dorn-reparo"):
			item.image_path = ability_art["dorn-reparo"]
		var name = str(item.get("item_title", item.get("name", ""))).to_lower()
		if ("poç" in name or "pocao" in name or "potion" in name or str(item.get("item_type", "")).to_lower() in ["consumivel", "consumível", "pocao", "poção"]) and belt.size() < 4:
			belt.append(item)
	view.set_vitals(str(definition.get("name", "")), definition.get("portrait"), state().get("current_hp"), state().get("maximum_hp"), resources[0] if not resources.is_empty() and resources[0] is Dictionary else {}, belt)
	if host.powers.has_method("bar_entries"):
		var entries: Array = host.powers.bar_entries(sheet, belt)
		if not entries.is_empty(): view.set_slots(entries)
	refresh_visibility()

func refresh_visibility() -> void:
	view.visible = host.authenticated and not sheet.is_empty() and not host.battle_overlay.visible and not host.town.screen_visible()
	host._layout()

func clear() -> void:
	sheet = {}
	view.hide()

static func purse_label(values: Dictionary) -> String:
	var copper = int(values.get("copper_coins", 0)) + int(values.get("silver_coins", 0)) * 10 + int(values.get("coins", 0)) * 100 + int(values.get("platinum_coins", 0)) * 10000
	return "Bolsa: " + preload("res://scripts/merchant_screen.gd").money(copper)
