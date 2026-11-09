extends Node
## Dados: rolagem livre, testes da ficha, pedidos do Mestre e histórico.
## Quem rola é o servidor; o cliente só pede e mostra o resultado.

const Style = preload("res://scripts/ui_style.gd")
const DICE = [4, 6, 8, 10, 12, 20, 100]
const ATTRIBUTES = [["strength", "Força"], ["dexterity", "Destreza"], ["constitution", "Constituição"],
	["intelligence", "Inteligência"], ["wisdom", "Sabedoria"], ["charisma", "Carisma"]]
const VISIBILITY = {"table": "Mesa", "private": "Privada", "owner": "Mestre e personagem", "gm": "Só o Mestre"}

var host: Node
var sides: int = 20
var count: int = 1
var modifier: int = 0
var roll_label: String = ""
var visibility: String = "table"
var character: String = ""         # character used for sheet tests
var history: Array = []
var requests: Array = []
var known_requests: Dictionary = {}
var last: Dictionary = {}
var sheets: Dictionary = {}        # character id -> definition
var busy: bool = false
# GM request form
var ask_character: String = ""
var ask_type: String = "attribute"
var ask_source: String = "dexterity"
var ask_formula: String = "1d20"
var ask_target: int = 0
var ask_hide: bool = false
var void_dialog = ConfirmationDialog.new()
var void_reason = LineEdit.new()
var void_id: int = -1

func setup(main: Node) -> void:
	host = main
	void_dialog.title = "Anular rolagem"
	void_dialog.ok_button_text = "Anular"
	void_dialog.cancel_button_text = "Cancelar"
	var box = VBoxContainer.new()
	Style.label(box, "Motivo (fica no registro):", 14)
	void_reason.placeholder_text = "Ex.: dado rolado por engano"
	box.add_child(void_reason)
	void_dialog.add_child(box)
	void_dialog.confirmed.connect(func():
		if void_id >= 0 and void_reason.text.strip_edges().length() >= 2:
			host.api.request_json("dice-void", "/gm/rolls/%d/void" % void_id, HTTPClient.METHOD_POST, {"reason": void_reason.text.strip_edges().left(500)})
		void_id = -1)
	host.screen.add_child(void_dialog)

func handles(key: String) -> bool:
	return key.begins_with("dice-")

func clear() -> void:
	history.clear()
	requests.clear()
	known_requests.clear()
	sheets.clear()
	last = {}
	busy = false
	character = ""

## Called on every table poll: pending requests are light and reach players quickly.
func poll() -> void:
	if not host.authenticated: return
	host.api.request_json("dice-requests", "/roll-requests")
	if _visible():
		host.api.request_json("dice-history", "/rolls?limit=20")

func open() -> void:
	if character == "": character = host.selected_id
	if character == "" and not host.characters.is_empty(): character = str(host.characters[0].get("id", ""))
	host.api.request_json("dice-history", "/rolls?limit=20")
	host.api.request_json("dice-requests", "/roll-requests")
	_load_sheet(character)

func _visible() -> bool:
	return host.panel.visible and host.active_panel == "dice"

func _load_sheet(id: String) -> void:
	if id == "" or sheets.has(id): return
	host.api.request_json("dice-sheet:" + id, "/characters/" + id.uri_encode() + "?read_only=true")

static func request_id(prefix: String) -> String:
	return prefix + "-" + Crypto.new().generate_random_bytes(10).hex_encode()

static func formula(n: int, faces: int, bonus: int) -> String:
	return "%dd%d%s" % [n, faces, ("" if bonus == 0 else ("%+d" % bonus))]

static func summary(roll: Dictionary) -> String:
	var text = "%s: %s = %d" % [str(roll.get("label", "Rolagem")), str(roll.get("formula", "")), int(roll.get("total", 0))]
	var dice: Array = roll.get("individual_results", []) if roll.get("individual_results") is Array else []
	if dice.size() > 1 or int(roll.get("modifier", 0)) != 0:
		text += "  [" + ", ".join(dice.map(func(d): return str(int(d)))) + "]"
	if roll.get("target_value") != null and not bool(roll.get("target_hidden", false)):
		text += ("  alvo ≤%d" if roll.get("target_comparison") == "at_most" else "  alvo %d") % int(roll.target_value)
	match str(roll.get("outcome", "")):
		"success": text += " · SUCESSO"
		"failure": text += " · FALHA"
	if bool(roll.get("voided", false)): text += " · ANULADA (" + str(roll.get("void_reason", "")) + ")"
	return text

func received(key: String, payload: Variant) -> void:
	if key.begins_with("dice-sheet:"):
		if payload is Dictionary: sheets[key.get_slice(":", 1)] = payload.get("definition", {})
		_refresh()
		return
	match key:
		"dice-history":
			history = payload if payload is Array else []
		"dice-requests":
			var list: Array = payload if payload is Array else []
			requests = list.filter(func(r): return str(r.get("status", "pending")) == "pending")
			for request in requests:
				var id = int(request.get("id", -1))
				if not known_requests.has(id):
					known_requests[id] = true
					if not host.master:
						host._notice("O Mestre pediu: " + str(request.get("label", "uma rolagem")) + " — abra Dados para rolar.")
			if not _visible(): return
		"dice-roll", "dice-check", "dice-complete":
			busy = false
			if payload is Dictionary:
				last = payload
				history.push_front(payload)
				host._notice(summary(payload))
			host.api.request_json("dice-requests", "/roll-requests")
		"dice-ask":
			busy = false
			host._notice("Pedido enviado ao jogador.")
			host.api.request_json("dice-requests", "/roll-requests")
		"dice-mode":
			if payload is Dictionary and payload.get("table_mode"): host.workspace.table_mode = payload.table_mode
			host._notice("Mesa em d20 físico." if physical() else "Mesa em dados digitais.")
			host._poll()
		"dice-void":
			host._notice("Rolagem anulada.")
			host.api.request_json("dice-history", "/rolls?limit=20")
	_refresh()

func failed(key: String, message: String, code: int) -> bool:
	if not handles(key): return false
	busy = false
	if key == "dice-requests" or key == "dice-history": return true  # quiet background reads
	if key.begins_with("dice-sheet:"):
		sheets[key.get_slice(":", 1)] = {}
	elif host.keeper.network_error(code) and key in ["dice-roll", "dice-check", "dice-complete"]:
		host._notice("Sem resposta do servidor. Veja o histórico antes de rolar de novo.")
	else:
		host._notice(message)
	_refresh()
	return true

func _refresh() -> void:
	if _visible(): host._render_panel()

# --- Comandos ------------------------------------------------------------------
func roll_free() -> void:
	if busy: return
	busy = true
	var body = {"request_id": request_id("free"), "formula": formula(count, sides, modifier),
		"label": roll_label.strip_edges().left(160) if roll_label.strip_edges() != "" else "Rolagem livre", "visibility": visibility}
	if character != "" and not host.master: body.character_id = character
	host.api.request_json("dice-roll", "/rolls", HTTPClient.METHOD_POST, body)

func roll_check(roll_type: String, source: String) -> void:
	if busy or character == "": return
	busy = true
	var body = {"request_id": request_id("check"), "roll_type": roll_type, "visibility": visibility}
	if source != "": body.source_id = source
	host.api.request_json("dice-check", "/characters/" + character.uri_encode() + "/rolls", HTTPClient.METHOD_POST, body)

func complete(request: Dictionary) -> void:
	if busy: return
	busy = true
	var id = int(request.id)
	host.api.request_json("dice-complete", "/roll-requests/%d/complete" % id, HTTPClient.METHOD_POST,
		{"request_id": ("request:%d:" % id) + str(request.get("request_id", "")).right(60)})

func ask() -> void:
	if busy or ask_character == "": return
	busy = true
	var body = {"request_id": request_id("ask"), "character_id": ask_character, "roll_type": ask_type, "visibility": "owner", "hide_target": ask_hide}
	if ask_type == "attribute": body.source_id = ask_source
	if ask_type == "free": body.formula = ask_formula.strip_edges().left(32)
	if ask_target > 0: body.target_value = ask_target
	host.api.request_json("dice-ask", "/gm/roll-requests", HTTPClient.METHOD_POST, body)

# --- Painel --------------------------------------------------------------------
## Table-wide roll mode, chosen by the GM (the server enforces it on every attack).
func physical() -> bool:
	return str(host.workspace.get("table_mode", "digital")) == "physical"

func set_physical(on: bool) -> void:
	if not host.master: return
	host.api.request_json("dice-mode", "/gm/workspace/table-mode", HTTPClient.METHOD_PATCH, {"table_mode": "physical" if on else "digital"})

func render(body: Node) -> void:
	if host.master:
		var toggle = CheckButton.new()
		toggle.text = "Mesa com d20 físico (jogadores digitam o dado nos ataques)"
		toggle.button_pressed = physical()
		toggle.toggled.connect(set_physical)
		body.add_child(toggle)
	elif physical():
		Style.label(body, "A mesa está em d20 físico: nos ataques, digite o valor que saiu no dado.", 14)
	if not last.is_empty():
		var result = Style.label(body, summary(last), 18)
		result.add_theme_color_override("font_color", Color("#e7c66b"))
	var mine: Array = requests if host.master else requests.filter(func(r): return str(r.get("character_id", "")) == host.my_profile or host.my_profile == "")
	if not mine.is_empty():
		Style.label(body, "Pedidos do Mestre" if not host.master else "Pedidos aguardando os jogadores", 16)
		for request in mine:
			var row = HBoxContainer.new()
			body.add_child(row)
			var text = Style.label(row, "%s · %s%s" % [_name(str(request.get("character_id", ""))), str(request.get("label", "")),
				("  (alvo %d)" % int(request.target_value)) if request.get("target_value") != null else ""], 14)
			text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			if not host.master or str(request.get("character_id", "")) == character:
				var go = Button.new()
				go.text = "Rolar"
				go.disabled = busy
				var captured: Dictionary = request
				go.pressed.connect(func(): complete(captured))
				row.add_child(go)
	_checks(body)
	_free(body)
	if host.master: _ask_form(body)
	_history(body)

func _name(id: String) -> String:
	for entry in host.characters:
		if str(entry.get("id", "")) == id: return str(entry.get("name", id))
	return id

func _checks(body: Node) -> void:
	Style.label(body, "Testes da ficha", 16)
	if not host.master and host.my_profile != "": character = host.my_profile
	if host.master:
		var who = OptionButton.new()
		for entry in host.characters:
			who.add_item(str(entry.get("name", "")))
			who.set_item_metadata(who.item_count - 1, str(entry.get("id", "")))
			if str(entry.get("id", "")) == character: who.select(who.item_count - 1)
		who.item_selected.connect(func(index): character = str(who.get_item_metadata(index)); _load_sheet(character); host._render_panel())
		body.add_child(who)
	if character == "":
		Style.label(body, "Nenhum personagem disponível.", 14)
		return
	var grid = GridContainer.new()
	grid.columns = 3
	body.add_child(grid)
	var definition: Dictionary = sheets.get(character, {})
	var mods: Dictionary = definition.get("attribute_modifiers", {}) if definition.get("attribute_modifiers") is Dictionary else {}
	for entry in ATTRIBUTES:
		var button = Button.new()
		var key: String = entry[0]
		button.text = entry[1] + ((" %+d" % int(mods[key])) if mods.get(key) != null else "")
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.disabled = busy
		button.pressed.connect(func(): roll_check("attribute", key))
		grid.add_child(button)
	var save = Button.new()
	var defenses: Dictionary = definition.get("defenses", {}) if definition.get("defenses") is Dictionary else {}
	save.text = "Jogada de Proteção" + ((" (%d)" % int(defenses.saving_throw)) if defenses.get("saving_throw") != null else "")
	save.disabled = busy
	save.pressed.connect(func(): roll_check("saving_throw", ""))
	body.add_child(save)
	var effects: Dictionary = definition.get("item_effects", {}) if definition.get("item_effects") is Dictionary else {}
	var skills: Dictionary = effects.get("skill_modifiers", {}) if effects.get("skill_modifiers") is Dictionary else {}
	var names: Array = skills.keys().filter(func(k): return str(k) != "all" and not str(k) in ATTRIBUTES.map(func(a): return a[0]))
	if not names.is_empty():
		var flow = HFlowContainer.new()
		body.add_child(flow)
		for skill in names:
			var button = Button.new()
			var skill_name := str(skill)
			button.text = "%s %+d" % [skill_name, int(skills[skill])]
			button.disabled = busy
			button.pressed.connect(func(): roll_check("skill", skill_name))
			flow.add_child(button)

func _free(body: Node) -> void:
	Style.label(body, "Rolagem livre", 16)
	var dice = HFlowContainer.new()
	body.add_child(dice)
	for faces in DICE:
		var button = Button.new()
		button.text = "d%d" % faces
		button.toggle_mode = true
		button.button_pressed = faces == sides
		button.custom_minimum_size = Vector2(52, 40)
		var f: int = faces
		button.pressed.connect(func(): sides = f; host._render_panel())
		dice.add_child(button)
	var row = HBoxContainer.new()
	body.add_child(row)
	_inline(row, "Quantidade")
	var amount = SpinBox.new()
	amount.custom_minimum_size = Vector2(96, 0)
	amount.min_value = 1
	amount.max_value = 20
	amount.value = count
	amount.value_changed.connect(func(v): count = int(v); roll_button_text())
	row.add_child(amount)
	_inline(row, "Modificador")
	var bonus = SpinBox.new()
	bonus.custom_minimum_size = Vector2(96, 0)
	bonus.min_value = -100
	bonus.max_value = 100
	bonus.value = modifier
	bonus.value_changed.connect(func(v): modifier = int(v); roll_button_text())
	row.add_child(bonus)
	var caption = LineEdit.new()
	caption.placeholder_text = "Rótulo (ex.: Percepção na passagem)"
	caption.max_length = 160
	caption.text = roll_label
	caption.text_changed.connect(func(t): roll_label = t)
	body.add_child(caption)
	var shown = OptionButton.new()
	for key in (["table", "private", "gm"] if host.master else ["table", "private"]):
		shown.add_item(VISIBILITY[key])
		shown.set_item_metadata(shown.item_count - 1, key)
		if key == visibility: shown.select(shown.item_count - 1)
	shown.item_selected.connect(func(index): visibility = str(shown.get_item_metadata(index)))
	body.add_child(shown)
	var go = Button.new()
	go.name = "RollButton"
	go.text = "Rolar " + formula(count, sides, modifier)
	go.disabled = busy
	go.custom_minimum_size = Vector2(0, 44)
	go.pressed.connect(roll_free)
	body.add_child(go)

func roll_button_text() -> void:
	var go = host.body.find_child("RollButton", true, false)
	if go: go.text = "Rolar " + formula(count, sides, modifier)

func _ask_form(body: Node) -> void:
	Style.label(body, "Pedir rolagem a um jogador", 16)
	var who = OptionButton.new()
	for entry in host.characters:
		who.add_item(str(entry.get("name", "")))
		who.set_item_metadata(who.item_count - 1, str(entry.get("id", "")))
		if ask_character == "": ask_character = str(entry.get("id", ""))
		if str(entry.get("id", "")) == ask_character: who.select(who.item_count - 1)
	who.item_selected.connect(func(index): ask_character = str(who.get_item_metadata(index)))
	body.add_child(who)
	var kind = OptionButton.new()
	for entry in [["attribute", "Teste de atributo"], ["saving_throw", "Jogada de Proteção"], ["free", "Fórmula livre"]]:
		kind.add_item(entry[1])
		kind.set_item_metadata(kind.item_count - 1, entry[0])
		if entry[0] == ask_type: kind.select(kind.item_count - 1)
	kind.item_selected.connect(func(index): ask_type = str(kind.get_item_metadata(index)); host._render_panel())
	body.add_child(kind)
	if ask_type == "attribute":
		var attribute = OptionButton.new()
		for entry in ATTRIBUTES:
			attribute.add_item(entry[1])
			attribute.set_item_metadata(attribute.item_count - 1, entry[0])
			if entry[0] == ask_source: attribute.select(attribute.item_count - 1)
		attribute.item_selected.connect(func(index): ask_source = str(attribute.get_item_metadata(index)))
		body.add_child(attribute)
	elif ask_type == "free":
		var text = LineEdit.new()
		text.text = ask_formula
		text.placeholder_text = "ex.: 1d6, 2d8+1"
		text.text_changed.connect(func(t): ask_formula = t)
		body.add_child(text)
	var row = HBoxContainer.new()
	body.add_child(row)
	_inline(row, "Dificuldade (0 = sem)")
	var target = SpinBox.new()
	target.custom_minimum_size = Vector2(96, 0)
	target.min_value = 0
	target.max_value = 100
	target.value = ask_target
	target.value_changed.connect(func(v): ask_target = int(v))
	row.add_child(target)
	var secret = CheckBox.new()
	secret.text = "Esconder"
	secret.button_pressed = ask_hide
	secret.toggled.connect(func(on): ask_hide = on)
	row.add_child(secret)
	var go = Button.new()
	go.text = "Pedir rolagem"
	go.disabled = busy
	go.pressed.connect(ask)
	body.add_child(go)

func _history(body: Node) -> void:
	Style.label(body, "Últimas rolagens", 16)
	if history.is_empty():
		Style.label(body, "Nenhuma rolagem ainda.", 14)
		return
	for roll in history.slice(0, 20):
		var row = HBoxContainer.new()
		body.add_child(row)
		var who = _name(str(roll.get("character_id", ""))) if roll.get("character_id") else ("Mestre" if str(roll.get("actor_role", "")) == "gm" else "")
		var text = Style.label(row, (who + " · " if who != "" else "") + summary(roll) + "  (" + VISIBILITY.get(str(roll.get("visibility", "")), "") + ")", 13)
		text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		if bool(roll.get("voided", false)): text.modulate = Color(1, 1, 1, 0.5)
		if host.master and not bool(roll.get("voided", false)) and roll.get("id") != null:
			var undo = Button.new()
			undo.text = "Anular"
			var id = int(roll.id)
			undo.pressed.connect(func(): void_id = id; void_reason.text = ""; void_dialog.popup_centered(Vector2i(380, 160)))
			row.add_child(undo)

static func _inline(row: Node, text: String) -> void:
	var label = Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 14)
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	row.add_child(label)
