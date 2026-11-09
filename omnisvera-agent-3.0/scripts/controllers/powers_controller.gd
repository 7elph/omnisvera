extends Node
## Poderes fora da arena: lista o que o manifesto de ações marca como executável
## (técnicas, Forma da Noite, Caixão, itens mágicos, Pulseira de Vinhas, invocações)
## e envia o comando ao mesmo endpoint da 2.0. Ataques ficam na tela de batalha.

const Style = preload("res://scripts/ui_style.gd")
const RUN = ["character_technique", "vezemir_skill", "necromancer_spell", "hemomancy_shield",
	"character_state_action", "vine_bracelet", "inventory_item"]
const ANIMALS = [["corvo", "Corvo"], ["coruja", "Coruja"], ["morcego", "Morcego"]]
const NEEDS_TARGET = ["marca-rubra", "forca-arcana", "pulseira-de-vinhas"]
## Dorn's Arcane Tome spells (GM-controlled). "Automated" ones are validated whole by the server;
## the others carry the GM's declaration of range/area, exactly like the 2.0 table.
const DORN_AUTOMATED = ["reflexos", "teia", "forca-arcana", "dissipar-magia"]
const DORN_BINDINGS = {"reflexos": "dorn_reflexos", "teia": "dorn_teia", "forca-arcana": "dorn_forca_arcana", "dissipar-magia": "dorn_dissipar_magia"}

var host: Node
var bar_order: Dictionary = {}  # character id -> Array of keys, persisted in user://bar_order.json
var manifests: Dictionary = {}     # character id -> Array of actions
var loading: Dictionary = {}
var animal: String = "corvo"
var target_id: String = ""
var busy: bool = false
var pending: Dictionary = {}       # {"key": String, "id": String} keeps the request id across retries
var dorn: Dictionary = {}          # open spell form: entry, targets, distance, weight, unwilling, shape, contacts, confirmed, effect
var diagnose_subject: String = ""
var diagnose_difficulty: int = 14

func setup(main: Node) -> void:
	host = main

func handles(key: String) -> bool:
	return key.begins_with("pow-")

func clear() -> void:
	manifests.clear()
	loading.clear()
	busy = false
	pending = {}

func _load(id: String) -> void:
	if id == "" or loading.get(id, false): return
	loading[id] = true
	host.api.request_json("pow-manifest:" + id, "/characters/" + id.uri_encode() + "/action-manifest")

static func _id(entry: Dictionary) -> String:
	var ref = str(entry.get("ref", ""))
	return ref.get_slice(":", 2) if ref.count(":") >= 2 else ref

func _usable(entry: Dictionary) -> bool:
	var execution: Dictionary = entry.get("execution", {}) if entry.get("execution") is Dictionary else {}
	var binding = str(entry.get("binding", ""))
	if entry.get("automation_scope") != "native" or execution.get("confirmation_endpoint"): return false
	return binding in RUN or (host.master and binding in ["dorn_spell", "dorn_protocol"])

const BAR_FILE = "user://bar_order.json"
const BAR_SLOTS = 6
var _bar_loaded: bool = false

func _load_bar_order() -> void:
	if _bar_loaded: return
	_bar_loaded = true
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(BAR_FILE)) if FileAccess.file_exists(BAR_FILE) else null
	if parsed is Dictionary: bar_order = parsed

func _save_bar_order() -> void:
	var file = FileAccess.open(BAR_FILE, FileAccess.WRITE)
	if file: file.store_string(JSON.stringify(bar_order))

## Everything that may go in the bar: usable actions first, then the belt items.
func bar_candidates(character: String, _sheet: Dictionary, belt: Array) -> Array:
	var candidates: Array = []
	for action in (manifests.get(character, []) as Array).filter(_usable):
		candidates.append({"key": "action:" + _id(action), "kind": "action", "name": str(action.get("label", "Poder")),
			"image_path": action.get("image_path"), "icon": "res://assets/ui/spells.svg", "record": action, "character": character})
	for item in belt:
		var id_part = str(item.get("id", item.get("item_title", "")))
		candidates.append({"key": "item:" + id_part, "kind": "item", "name": str(item.get("item_title", item.get("name", "Item"))),
			"image_path": item.get("image_path"), "icon": "res://assets/ui/items.svg", "quantity": int(item.get("quantity")) if item.get("quantity") != null else 1,
			"record": item, "character": character})
	return candidates

## Keys shown in the bar, in order: the saved choice, or the first six candidates.
func _bar_keys(character: String, candidates: Array) -> Array:
	_load_bar_order()
	var present = candidates.map(func(c): return c.key)
	if bar_order.get(character) is Array:
		return (bar_order[character] as Array).filter(func(k): return k in present).slice(0, BAR_SLOTS)
	return present.slice(0, BAR_SLOTS)

func bar_entries(sheet: Dictionary, belt: Array) -> Array:
	var definition: Dictionary = sheet.get("definition", {}) if sheet.get("definition") is Dictionary else {}
	var character = str(definition.get("id", ""))
	if character == "": return []
	if not manifests.has(character):
		_load(character)
		return []
	var candidates = bar_candidates(character, sheet, belt)
	var by_key = {}
	for c in candidates: by_key[c.key] = c
	return _bar_keys(character, candidates).map(func(k): return by_key[k])

## A bar slot: items show their card; actions without a choice to make run at once, the rest open the panel.
func use_from_bar(entry: Dictionary) -> void:
	if entry.get("kind") == "item":
		host._show_detail(entry.record)
		return
	var character = str(entry.get("character", ""))
	if character == "": return
	var record: Dictionary = entry.record
	var id = _id(record)
	var binding = str(record.get("binding", ""))
	var needs_choice = id in NEEDS_TARGET or id == "forma-da-noite" or binding in ["vine_bracelet", "dorn_spell", "dorn_protocol"]
	if needs_choice or busy:
		host.selected_id = character
		host._open_panel("spells")
		return
	use_entry(character, record, host.sheet.get("definition", {}) if host.sheet is Dictionary else {})

func _set_bar(character: String, keys: Array) -> void:
	bar_order[character] = keys.slice(0, BAR_SLOTS)
	_save_bar_order()
	host.hud.render()
	_refresh()

func _bar_editor(body: Node, character: String) -> void:
	var belt: Array = []
	if host.sheet is Dictionary:
		for item in host.sheet.get("inventory", []):
			if not item is Dictionary: continue
			var name = str(item.get("item_title", item.get("name", ""))).to_lower()
			if "poç" in name or "pocao" in name or "potion" in name or str(item.get("item_type", "")).to_lower() in ["consumivel", "consumível", "pocao", "poção"]:
				belt.append(item)
	var candidates = bar_candidates(character, host.sheet if host.sheet is Dictionary else {}, belt)
	if candidates.is_empty(): return
	Style.label(body, "Barra de ações (até %d, na ordem abaixo)" % BAR_SLOTS, 14)
	var keys: Array = _bar_keys(character, candidates)
	var ordered = candidates.duplicate()
	ordered.sort_custom(func(a, b):
		var ia = keys.find(a.key)
		var ib = keys.find(b.key)
		return (ia if ia >= 0 else 99) < (ib if ib >= 0 else 99))
	for cand in ordered:
		var key: String = cand.key
		var index = keys.find(key)
		var row = HBoxContainer.new()
		body.add_child(row)
		var check = CheckBox.new()
		check.text = str(cand.name)
		check.button_pressed = index >= 0
		check.disabled = index < 0 and keys.size() >= BAR_SLOTS
		check.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		check.toggled.connect(func(on):
			var next = keys.duplicate()
			if on and not key in next: next.append(key)
			if not on: next.erase(key)
			_set_bar(character, next))
		row.add_child(check)
		for step in [-1, 1]:
			var move = Button.new()
			move.text = "▲" if step < 0 else "▼"
			move.disabled = index < 0 or index + step < 0 or index + step >= keys.size()
			move.pressed.connect(func():
				var next = keys.duplicate()
				next.remove_at(index)
				next.insert(index + step, key)
				_set_bar(character, next))
			row.add_child(move)

# --- Painel --------------------------------------------------------------------
func render(body: Node, character: String, definition: Dictionary, state: Dictionary) -> void:
	if character == "": return
	_bar_editor(body, character)
	Style.label(body, "Usar agora (fora da batalha)", 16)
	if not manifests.has(character):
		Style.label(body, "Carregando poderes…", 14)
		_load(character)
		return
	var entries: Array = (manifests[character] as Array).filter(_usable)
	if entries.is_empty():
		Style.label(body, "Nenhum poder ou item utilizável fora da batalha nesta ficha.", 14)
		return
	if entries.any(func(e): return (_id(e) in NEEDS_TARGET and str(e.get("binding", "")) != "dorn_spell") or str(e.get("binding", "")) == "vine_bracelet"):
		_target_picker(body, character)
	var form = str(state.get("animal_form", "")) if state.get("animal_form") else ""
	for entry in entries:
		var row = HBoxContainer.new()
		body.add_child(row)
		var availability: Dictionary = entry.get("availability", {}) if entry.get("availability") is Dictionary else {}
		var title = str(entry.get("label", "Poder"))
		var cost: Dictionary = entry.get("cost", {}) if entry.get("cost") is Dictionary else {}
		if cost.get("current_estimate") != null: title += " · custo %d" % int(cost.current_estimate)
		var text = Style.label(row, title, 14)
		text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		text.tooltip_text = str(entry.get("description", "")).left(400)
		text.mouse_filter = Control.MOUSE_FILTER_PASS
		var id = _id(entry)
		if str(entry.get("binding", "")) == "dorn_spell":
			var open = not dorn.is_empty() and dorn.entry.get("ref") == entry.get("ref")
			var prepare = Button.new()
			prepare.text = "Fechar" if open else "Preparar"
			var spell_entry: Dictionary = entry
			prepare.pressed.connect(func():
				dorn = {} if open else {"entry": spell_entry, "targets": [], "distance": 0, "weight": 0, "unwilling": false, "shape": "line", "contacts": {}, "confirmed": false, "effect": ""}
				_refresh())
			row.add_child(prepare)
			if open: _dorn_form(body)
			continue
		if str(entry.get("binding", "")) == "dorn_protocol":
			var activate = Button.new()
			activate.text = "Ativar"
			activate.disabled = busy
			var protocol = str((entry.get("execution", {}) as Dictionary).get("action", "dorn_guard"))
			activate.pressed.connect(func(): host._send_effect(protocol, {}))
			row.add_child(activate)
			continue
		if id == "forma-da-noite" and form != "":
			var off = Button.new()
			off.text = "Desativar (" + form.capitalize() + ")"
			off.disabled = busy
			off.pressed.connect(func(): _state_action(character, "end_night_form", {}, "Desativar Forma da Noite"))
			row.add_child(off)
			continue
		if id == "forma-da-noite":
			var pick = OptionButton.new()
			for a in ANIMALS:
				pick.add_item(a[1])
				pick.set_item_metadata(pick.item_count - 1, a[0])
				if a[0] == animal: pick.select(pick.item_count - 1)
			pick.item_selected.connect(func(i): animal = str(pick.get_item_metadata(i)))
			row.add_child(pick)
		var use = Button.new()
		use.text = "Usar"
		var blocked = str(availability.get("state", "")) in ["unavailable", "blocked"]
		use.disabled = busy or blocked or (form != "" and id != "forma-da-noite")
		use.tooltip_text = str(availability.get("reason", "")) if blocked else ("Desative a forma animal primeiro." if form != "" and id != "forma-da-noite" else "")
		var captured: Dictionary = entry
		use.pressed.connect(func(): use_entry(character, captured, definition))
		row.add_child(use)
		if blocked:
			var why = Style.label(body, "   " + str(availability.get("reason", "Indisponível")), 12)
			why.modulate = Color(1, 1, 1, 0.6)
	if character == "dorn7" and host.master:
		_diagnostic(body)

# --- Dorn: Tomo Arcano e Diagnóstico --------------------------------------------
func _dorn_form(body: Node) -> void:
	var spell = _id(dorn.entry)
	var automated = spell in DORN_AUTOMATED
	var box = VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	body.add_child(box)
	var help = {"levitacao": "Um receptor. Limite 50 kg/nível; alcance 20 m/nível.", "escuridao": "Raio 4,5 m; marque todos os ocupantes, inclusive aliados.",
		"relampago": "Marque cada alvo atingido e quantos contatos do raio ele recebe.", "reflexos": "Em si mesmo; sem alvo.",
		"teia": "Escolha um pin: a célula dele é o canto da área 3×3 m.", "forca-arcana": "Um receptor vivo.", "dissipar-magia": "Escolha o efeito arcano a dissipar."}
	Style.label(box, help.get(spell, str(dorn.entry.get("description", "")).left(200)), 13)
	if spell == "dissipar-magia":
		var pick = OptionButton.new()
		pick.add_item("Selecione o efeito")
		pick.set_item_metadata(0, "")
		for effect in host.combat_state.get("effects", []):
			if effect is Dictionary and effect.get("magic_type") == "arcane" and effect.get("spell_circle") and effect.get("caster_level") and not effect.get("environmental"):
				pick.add_item(str(effect.get("label", "Efeito")) + " · " + str(effect.get("target_id", "")))
				pick.set_item_metadata(pick.item_count - 1, str(effect.get("id", "")))
				if str(effect.get("id", "")) == dorn.effect: pick.select(pick.item_count - 1)
		pick.item_selected.connect(func(i): dorn.effect = str(pick.get_item_metadata(i)))
		box.add_child(pick)
	elif spell != "reflexos":
		for token in host.workspace.get("tokens", []):
			if str(token.get("character_id", "")) == "dorn7": continue
			if not str(token.get("token_type", "")) in ["monster", "character"]: continue
			var id = str(token.get("id", ""))
			var line = HBoxContainer.new()
			box.add_child(line)
			var check = CheckBox.new()
			check.text = str(token.get("name", ""))
			check.button_pressed = id in dorn.targets
			check.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			check.toggled.connect(func(on):
				if on and not id in dorn.targets: dorn.targets.append(id)
				if not on: dorn.targets.erase(id)
				if spell == "relampago": _refresh())
			line.add_child(check)
			if spell == "relampago" and id in dorn.targets:
				var contacts = SpinBox.new()
				contacts.min_value = 1
				contacts.max_value = 10
				contacts.prefix = "contatos"
				contacts.value = int(dorn.contacts.get(id, 1))
				contacts.value_changed.connect(func(v): dorn.contacts[id] = int(v))
				line.add_child(contacts)
	if not automated:
		var distance = SpinBox.new()
		distance.min_value = 0
		distance.max_value = 2000
		distance.prefix = "Distância (m)"
		distance.value = float(dorn.distance)
		distance.value_changed.connect(func(v): dorn.distance = v)
		box.add_child(distance)
	if spell == "levitacao":
		var weight = SpinBox.new()
		weight.min_value = 0
		weight.max_value = 5000
		weight.prefix = "Peso do receptor (kg)"
		weight.value = float(dorn.weight)
		weight.value_changed.connect(func(v): dorn.weight = v)
		box.add_child(weight)
		var unwilling = CheckBox.new()
		unwilling.text = "Receptor não aceita (JP)"
		unwilling.button_pressed = dorn.unwilling
		unwilling.toggled.connect(func(on): dorn.unwilling = on)
		box.add_child(unwilling)
	if spell == "relampago":
		var shape = OptionButton.new()
		shape.add_item("Raio 1,5 × 24 m")
		shape.set_item_metadata(0, "line")
		shape.add_item("Bifurcado 3 × 12 m")
		shape.set_item_metadata(1, "forked")
		shape.select(1 if dorn.shape == "forked" else 0)
		shape.item_selected.connect(func(i): dorn.shape = str(shape.get_item_metadata(i)))
		box.add_child(shape)
	if not automated:
		var confirm = CheckBox.new()
		confirm.text = "Confirmo alcance, área/posição e peso conforme o Tomo"
		confirm.button_pressed = dorn.confirmed
		confirm.toggled.connect(func(on): dorn.confirmed = on)
		box.add_child(confirm)
	var cast = Button.new()
	cast.text = "Conjurar · resolver automaticamente"
	cast.disabled = busy
	cast.pressed.connect(cast_dorn)
	box.add_child(cast)

func cast_dorn() -> void:
	if dorn.is_empty() or busy: return
	var spell = _id(dorn.entry)
	var automated = spell in DORN_AUTOMATED
	var problem = ""
	if spell == "dissipar-magia" and dorn.effect == "": problem = "escolha o efeito a dissipar"
	elif spell not in ["reflexos", "dissipar-magia"] and dorn.targets.is_empty(): problem = "marque pelo menos um alvo"
	elif automated and spell not in ["reflexos", "dissipar-magia"] and dorn.targets.size() != 1: problem = "marque um único alvo"
	elif spell == "levitacao" and (dorn.targets.size() != 1 or float(dorn.weight) <= 0): problem = "um receptor e o peso dele"
	elif not automated and not dorn.confirmed: problem = "confirme alcance e área"
	if problem != "":
		host._notice(str(dorn.entry.get("label", "Magia")) + ": " + problem + ".")
		return
	if automated:
		busy = true
		host.api.request_json("pow-contract", "/gm/actions/describe?ref=" + str(dorn.entry.get("ref", "")).uri_encode())
		_refresh()
	else:
		_send_dorn({})

func _send_dorn(revision: Dictionary) -> void:
	var spell = _id(dorn.entry)
	var payload: Dictionary = {"spell_id": spell}
	if spell in DORN_AUTOMATED:
		if spell == "dissipar-magia": payload.effect_id = dorn.effect
		else: payload.targets = (dorn.targets as Array).map(func(id): return {"type": "token", "id": id})
	else:
		payload.targets = (dorn.targets as Array).map(func(id): return {"type": "token", "id": id, "contacts": int(dorn.contacts.get(id, 1))})
		payload.distance_meters = float(dorn.distance)
		payload.weight_kg = float(dorn.weight)
		payload.unwilling = bool(dorn.unwilling)
		payload.shape = str(dorn.shape)
		payload.position_confirmed = bool(dorn.confirmed)
	payload.merge(revision)
	busy = false
	host._send_effect("dorn_spell_cast", payload)
	dorn = {}
	_refresh()

func _diagnostic(body: Node) -> void:
	Style.label(body, "Diagnóstico da Unidade", 15)
	var row = HBoxContainer.new()
	body.add_child(row)
	var subject = LineEdit.new()
	subject.placeholder_text = "Componente analisado"
	subject.max_length = 160
	subject.text = diagnose_subject
	subject.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	subject.text_changed.connect(func(t): diagnose_subject = t)
	row.add_child(subject)
	var difficulty = SpinBox.new()
	difficulty.min_value = 1
	difficulty.max_value = 99
	difficulty.value = diagnose_difficulty
	difficulty.prefix = "Dif."
	difficulty.value_changed.connect(func(v): diagnose_difficulty = int(v))
	row.add_child(difficulty)
	var go = Button.new()
	go.text = "Diagnosticar"
	go.pressed.connect(func():
		if diagnose_subject.strip_edges() == "":
			host._notice("Diagnóstico: descreva o componente.")
		else:
			host._send_effect("dorn_diagnose", {"subject": diagnose_subject.strip_edges(), "difficulty": diagnose_difficulty}))
	row.add_child(go)

static func _n(value: Variant) -> String:
	return "—" if value == null else str(int(value)) if value is float or value is int else str(value)

## Outcome line for the table status after a Dorn effect (same wording as the 2.0 card).
static func dorn_outcome(result: Dictionary) -> String:
	if result.has("outcome") and not result.has("results"):
		return "Diagnóstico: INT %s · %s" % [_n(result.get("total")), "sucesso; o Mestre define a informação" if result.get("outcome") == "success" else "inconclusivo"]
	var parts: Array = []
	for r in result.get("results", []):
		var text = str(r.get("target", ""))
		var saves: Array = r.get("contact_saves", []) if r.get("contact_saves") is Array else ([r.saving_throw] if r.get("saving_throw") is Dictionary else [])
		for save in saves:
			text += " · JP %s: %s" % [_n(save.get("total")), "resistiu" if save.get("success") else "falhou"]
		if r.get("damage") != null:
			text += " · dano %d · PV %d→%d" % [int(r.damage), int(r.get("hp_before", 0)), int(r.get("hp_after", 0))]
		elif r.get("total") != null and r.get("difficulty") != null:
			text += " · %d contra %d: %s" % [int(r.total), int(r.difficulty), "dissipada" if r.get("success") else "resistiu"]
		parts.append(text)
	return str(result.get("spell", "Magia")) + ": " + "; ".join(parts)

func _target_picker(body: Node, character: String) -> void:
	var row = HBoxContainer.new()
	body.add_child(row)
	var caption = Label.new()
	caption.text = "Alvo:"
	row.add_child(caption)
	var pick = OptionButton.new()
	pick.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pick.add_item("Sem alvo")
	pick.set_item_metadata(0, "")
	for token in host.workspace.get("tokens", []):
		if str(token.get("character_id", "")) == character: continue
		if token.get("current_hp") != null and int(token.current_hp) <= 0: continue
		if not str(token.get("token_type", "")) in ["monster", "character"]: continue
		pick.add_item(str(token.get("name", "")))
		pick.set_item_metadata(pick.item_count - 1, str(token.get("id", "")))
		if str(token.get("id", "")) == target_id: pick.select(pick.item_count - 1)
	pick.item_selected.connect(func(i): target_id = str(pick.get_item_metadata(i)); pending = {})
	row.add_child(pick)

# --- Comandos ------------------------------------------------------------------
func _request_id(key: String) -> String:
	if pending.get("key") != key:
		pending = {"key": key, "id": "power-" + Crypto.new().generate_random_bytes(10).hex_encode()}
	return str(pending.id)

func _resource_key(definition: Dictionary, id: String, fallback: String) -> String:
	for ability in definition.get("session_abilities", []):
		if ability is Dictionary and str(ability.get("id", "")) == id and ability.get("uses") is Dictionary:
			return str(ability.uses.get("resource_key", fallback))
	return fallback

func _state_action(character: String, action: String, payload: Dictionary, reason: String) -> void:
	if busy: return
	busy = true
	var key = JSON.stringify([character, action, payload])
	host.api.request_json("pow-use", "/characters/" + character.uri_encode() + "/actions", HTTPClient.METHOD_POST,
		{"action": action, "payload": payload, "reason": reason.left(400), "request_id": _request_id(key)})
	_refresh()

func use_entry(character: String, entry: Dictionary, definition: Dictionary) -> void:
	if busy: return
	var execution: Dictionary = entry.get("execution", {}) if entry.get("execution") is Dictionary else {}
	var binding = str(entry.get("binding", ""))
	var id = _id(entry)
	var label = str(entry.get("label", "Poder"))
	if (id in NEEDS_TARGET or binding == "vine_bracelet") and target_id == "":
		host._notice(label + ": escolha um alvo acima.")
		return
	match binding:
		"character_state_action":
			if id == "forma-da-noite":
				_state_action(character, "consume_resource", {"resource_key": _resource_key(definition, id, "forma_da_noite"), "amount": 1, "animal": animal}, "Forma da Noite: " + animal)
			elif id == "caixao":
				_state_action(character, "rest_in_coffin", {}, str(definition.get("name", "Personagem")) + " descansou no Caixão")
			else:
				_state_action(character, str(execution.get("action", "consume_resource")), {}, label)
			return
		"inventory_item":
			_state_action(character, "use_item", (execution.get("payload", {}) as Dictionary).duplicate() if execution.get("payload") is Dictionary else {}, "Usou " + label)
			return
		"vine_bracelet":
			busy = true
			host.api.request_json("pow-use", str(execution.endpoint), HTTPClient.METHOD_POST,
				{"target_type": "token", "target_id": target_id, "request_id": _request_id("vines:" + target_id)})
			_refresh()
			return
	var payload: Dictionary = (execution.get("payload", {}) as Dictionary).duplicate(true) if execution.get("payload") is Dictionary else {}
	if host.workspace.get("map") is Dictionary: payload.map_id = str(host.workspace.map.get("id", ""))
	if target_id != "" and id in NEEDS_TARGET:
		payload.target_type = "token"
		payload.target_id = target_id
	payload.request_id = _request_id(JSON.stringify([character, id, payload.get("target_id", "")]))
	busy = true
	host.api.request_json("pow-use", str(execution.get("endpoint", "")), HTTPClient.METHOD_POST, payload)
	_refresh()

func received(key: String, payload: Variant) -> void:
	if key == "pow-contract":
		var contract: Dictionary = payload.get("contract", {}) if payload is Dictionary and payload.get("contract") is Dictionary else {}
		var spell = _id(dorn.entry) if not dorn.is_empty() else ""
		var revision = {}
		if not contract.is_empty():
			var valid = int(contract.get("schema_version", 0)) == 1 and str(contract.get("ref", "")) == "technique:dorn7:" + spell \
				and str((contract.get("executor", {}) as Dictionary).get("binding", "")) == str(DORN_BINDINGS.get(spell, "")) \
				and RegEx.create_from_string("^[a-z0-9-]{8,100}$").search(str(contract.get("revision", ""))) != null
			if not valid:
				busy = false
				host._notice("Contrato da magia não confere com a ficha. Atualize e tente de novo.")
				_refresh()
				return
			revision = {"definition_revision": str(contract.revision)}
		if not dorn.is_empty(): _send_dorn(revision)
		return
	if key.begins_with("pow-manifest:"):
		var id = key.get_slice(":", 1)
		loading.erase(id)
		manifests[id] = (payload.get("actions", []) if payload is Dictionary else [])
		_refresh()
		return
	if key == "pow-use":
		busy = false
		pending = {}
		host._notice(_summary(payload))
		manifests.clear()       # costs and availability changed
		host._load_sheet()
		host._poll()
		_refresh()

static func _summary(result: Variant) -> String:
	if not result is Dictionary: return "Feito."
	if result.get("heal_roll") != null:
		return "Recuperou 1d4 = %d · PV %d → %d" % [int(result.heal_roll), int(result.get("hp_before", 0)), int(result.get("hp_after", 0))]
	if result.get("token") is Dictionary:
		return "Invocado: " + str(result.token.get("name", "criatura")) + (" (já estava ativo)" if result.get("existing") else "")
	if result.get("animal_form"):
		return "Forma da Noite ativa: " + str(result.animal_form).capitalize()
	if result.get("state") is Dictionary:
		var form = result.state.get("animal_form")
		return ("Forma da Noite ativa: " + str(form).capitalize()) if form else "Ficha atualizada."
	return "Feito."

func failed(key: String, message: String, code: int) -> bool:
	if not handles(key): return false
	if key.begins_with("pow-manifest:"):
		loading.erase(key.get_slice(":", 1))
		manifests[key.get_slice(":", 1)] = []
		return true
	busy = false
	if host.keeper.network_error(code):
		host._notice("Sem resposta do servidor. Toque em Usar de novo: o mesmo pedido não é aplicado duas vezes.")
	else:
		pending = {}
		host._notice(message + (" Escolha um alvo acima." if "alvo" in message.to_lower() else ""))
	_refresh()
	return true

func _refresh() -> void:
	if host.panel.visible and host.active_panel == "spells": host._render_panel()
