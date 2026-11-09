extends Node
## Ficha: nível (leitura) e PV de nível pendentes (quem controla rola); nível/XP editáveis nas ferramentas do Mestre;
## anotações numa janela aberta pelo ícone ao lado da poção de vida.
## O servidor recalcula a progressão aprovada; PV que dependem de dado ficam pendentes, sem cura automática.

const Style = preload("res://scripts/ui_style.gd")

var host: Node
var notes: Dictionary = {}         # character id -> {"content", "version"}
var drafts: Dictionary = {}        # character id -> unsaved text
var draft_level: int = 0
var draft_xp: int = 0
var busy: bool = false
var confirm_level = ConfirmationDialog.new()
var level_target: String = ""
var confirm_rest = ConfirmationDialog.new()
var resting: Dictionary = {}       # character id -> "pending" | "ok" | error text
var rest_id: String = ""

func setup(main: Node) -> void:
	host = main
	confirm_level.title = "Nível e experiência"
	confirm_level.ok_button_text = "Salvar"
	confirm_level.cancel_button_text = "Cancelar"
	confirm_level.confirmed.connect(func():
		if level_target == "" or busy: return
		busy = true
		host.api.request_json("prog-level", "/gm/characters/" + level_target.uri_encode() + "/definition", HTTPClient.METHOD_PATCH,
			{"fields": {"level": draft_level, "experience": draft_xp}, "reason": "Edição de nível e XP"}))
	host.screen.add_child(confirm_level)
	confirm_rest.title = "Descanso geral"
	confirm_rest.ok_button_text = "Conceder descanso"
	confirm_rest.cancel_button_text = "Cancelar"
	confirm_rest.dialog_text = "Conceder descanso geral a todo o grupo?\nRecarrega usos diários, Reserva de Sangue, Caixão e demais recursos de descanso, e restaura os monstros conforme a regra da 2.0."
	confirm_rest.confirmed.connect(rest_all)
	host.screen.add_child(confirm_rest)

func handles(key: String) -> bool:
	return key.begins_with("prog-")

func clear() -> void:
	notes.clear()
	drafts.clear()
	busy = false

## GM panel: same command the 2.0 table sends (rest_at_inn per character; the first one resets monsters).
func render_gm(body: Node) -> void:
	var rest = Button.new()
	rest.text = "Descanso geral (recarrega o grupo)"
	rest.disabled = resting.values().has("pending")
	rest.custom_minimum_size.y = 44
	rest.pressed.connect(func(): confirm_rest.popup_centered(Vector2i(440, 180)))
	body.add_child(rest)
	if not resting.is_empty():
		var lines: Array = []
		for id in resting:
			var value = str(resting[id])
			lines.append("%s: %s" % [_name(id), "descansando…" if value == "pending" else ("ok" if value == "ok" else value)])
		Style.label(body, "\n".join(lines), 13)

func _name(id: String) -> String:
	for entry in host.characters:
		if str(entry.get("id", "")) == id: return str(entry.get("name", id))
	return id

func rest_all() -> void:
	if not host.master or resting.values().has("pending") or host.characters.is_empty(): return
	# A retry after a failure reuses the same ids (the server applies each rest once);
	# characters that already rested are skipped.
	var retry = rest_id != "" and resting.values().any(func(v): return v != "ok")
	if not retry:
		rest_id = "rest-all-" + Crypto.new().generate_random_bytes(8).hex_encode()
		resting.clear()
	for index in range(host.characters.size()):
		var id = str(host.characters[index].get("id", ""))
		if id == "" or resting.get(id) == "ok": continue
		resting[id] = "pending"
		host.api.request_json("prog-rest:" + id, "/characters/" + id.uri_encode() + "/actions", HTTPClient.METHOD_POST,
			{"action": "rest_at_inn", "payload": {"reset_monsters": true} if index == 0 else {},
			"reason": "Descanso geral concedido pelo Mestre", "request_id": rest_id + ":" + id})
	_refresh_gm()

func _refresh_gm() -> void:
	if host.panel.visible and host.active_panel == "gm": host._render_panel()

func load_notes(id: String) -> void:
	if id == "" or notes.has(id): return
	host.api.request_json("prog-notes:" + id, "/characters/" + id.uri_encode() + "/notes")

func render(body: Node, id: String, definition: Dictionary) -> void:
	# Player sheet: only the level line and pending level-up rolls. Editing level/XP lives in the GM tools;
	# notes open from the icon next to the life potion.
	if id == "" or definition.is_empty(): return
	var progression: Dictionary = definition.get("progression", {}) if definition.get("progression") is Dictionary else {}
	Style.label(body, "Nível %s · XP %d" % [str(int(definition.level)) if definition.get("level") != null else "—", int(progression.get("experience", 0) if progression.get("experience") != null else 0)], 14)
	var pending: Array = progression.get("pending_rolls", []) if progression.get("pending_rolls") is Array else []
	for entry in pending:
		var row = HBoxContainer.new()
		body.add_child(row)
		var text = Style.label(row, "PV do nível %s: 1d%s (sem cura automática)" % [str(entry.get("level", "")), str(entry.get("die", ""))], 14)
		text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var go = Button.new()
		go.text = "Rolar PV"
		go.disabled = busy
		var request = int(entry.get("request_id", -1))
		go.pressed.connect(func():
			if busy or request < 0: return
			busy = true
			host.api.request_json("prog-hp", "/roll-requests/%d/complete" % request, HTTPClient.METHOD_POST, {"request_id": "level-hp-completion:%d" % request}))
		row.add_child(go)

## GM tools: level and XP of the character picked in the selector above the panel.
func render_gm_progress(body: Node) -> void:
	var id = host.selected_id
	var definition: Dictionary = host.sheet.get("definition", {}) if host.sheet.get("definition") is Dictionary else {}
	Style.label(body, "Progressão", 16)
	if id == "" or definition.is_empty() or str(definition.get("id", "")) != id:
		Style.label(body, "Escolha um personagem no seletor acima.", 13)
		return
	var progression: Dictionary = definition.get("progression", {}) if definition.get("progression") is Dictionary else {}
	Style.label(body, "%s · nível %s · XP %d" % [str(definition.get("name", id)), str(int(definition.level)) if definition.get("level") != null else "—", int(progression.get("experience", 0) if progression.get("experience") != null else 0)], 14)
	_level_form(body, id, definition, progression)

func _level_form(body: Node, id: String, definition: Dictionary, progression: Dictionary) -> void:
	var row = HBoxContainer.new()
	body.add_child(row)
	var level = SpinBox.new()
	level.min_value = 1
	level.max_value = 20
	level.value = int(definition.get("level", 1)) if definition.get("level") != null else 1
	level.prefix = "Nível"
	level.custom_minimum_size = Vector2(120, 0)
	row.add_child(level)
	var xp = SpinBox.new()
	xp.min_value = 0
	xp.max_value = 10000000
	xp.value = int(progression.get("experience", 0))
	xp.prefix = "XP"
	xp.custom_minimum_size = Vector2(140, 0)
	row.add_child(xp)
	var save = Button.new()
	save.text = "Salvar"
	save.disabled = busy
	save.pressed.connect(func():
		draft_level = int(level.value)
		draft_xp = int(xp.value)
		level_target = id
		var up = draft_level > int(definition.get("level", 1) if definition.get("level") != null else 1)
		confirm_level.dialog_text = "%s: nível %d, XP %d?%s" % [str(definition.get("name", id)), draft_level, draft_xp,
			"\nA progressão aprovada é recalculada; PV que dependem de dado ficam pendentes para o jogador rolar." if up else ""]
		confirm_level.popup_centered(Vector2i(420, 170)))
	row.add_child(save)

func _notes(body: Node, id: String) -> void:
	if not notes.has(id):
		Style.label(body, "Carregando anotações…", 14)
		load_notes(id)
		return
	var editor = TextEdit.new()
	editor.custom_minimum_size = Vector2(0, 190)
	editor.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	editor.text = str(drafts.get(id, notes[id].get("content", "")))
	editor.placeholder_text = "Pistas, nomes, dívidas, planos…"
	body.add_child(editor)
	var save = Button.new()
	save.text = "Salvar anotações"
	save.disabled = busy
	editor.text_changed.connect(func(): drafts[id] = editor.text.left(12000))
	save.pressed.connect(func():
		if busy: return
		busy = true
		host.api.request_json("prog-save:" + id, "/characters/" + id.uri_encode() + "/notes", HTTPClient.METHOD_PUT,
			{"content": editor.text.left(12000), "version": int(notes[id].get("version", 0))}))
	body.add_child(save)

func received(key: String, payload: Variant) -> void:
	if key.begins_with("prog-notes:") or key.begins_with("prog-save:"):
		var id = key.get_slice(":", 1)
		if payload is Dictionary: notes[id] = payload
		if key.begins_with("prog-save:"):
			busy = false
			drafts.erase(id)
			host._notice("Anotações salvas.")
	elif key.begins_with("prog-rest:"):
		resting[key.get_slice(":", 1)] = "ok"
		if not resting.values().has("pending") and not resting.values().any(func(v): return v != "ok"):
			host._notice("Descanso geral concedido.")
			rest_id = ""
			host._load_sheet()
			host.hud.load_sheet()
			host.powers.manifests.clear()
			host._poll()
		_refresh_gm()
		return
	elif key == "prog-level":
		busy = false
		host._notice("Nível e XP salvos.")
		host._load_sheet()
	elif key == "prog-hp":
		busy = false
		if payload is Dictionary: host._notice("PV do nível: " + str(payload.get("formula", "")) + " = " + str(int(payload.get("total", 0))))
		host._load_sheet()
	_refresh()

func failed(key: String, message: String, code: int) -> bool:
	if not handles(key): return false
	busy = false
	if key.begins_with("prog-rest:"):
		resting[key.get_slice(":", 1)] = message.left(80)
		host._notice("Descanso: " + message)
		_refresh_gm()
		return true
	if key.begins_with("prog-notes:"):
		notes[key.get_slice(":", 1)] = {"content": "", "version": 0, "unavailable": true}
		host._notice("Anotações: " + message)
	elif key.begins_with("prog-save:") and code == 409:
		notes.erase(key.get_slice(":", 1))  # someone else saved: reload, the draft stays
		host._notice("As anotações mudaram em outro lugar. Seu rascunho foi mantido; confira e salve de novo.")
	else:
		host._notice(message)
	_refresh()
	return true

func _refresh() -> void:
	if host.panel.visible and host.active_panel == "sheet": host._render_panel()
