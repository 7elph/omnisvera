extends Node
## Battle mode: face-to-face screen, creature AI, proximity encounters and the manual
## arena setup. Every rule decision stays on the server; this only routes intents.
const Commands = preload("res://scripts/game_commands.gd")
var host: Node
var overlay: Control
var ai = preload("res://scripts/battle_ai.gd").new()
var watch = preload("res://scripts/encounter_watch.gd").new()
var confirm_attack = ConfirmationDialog.new()
var confirm_encounter = ConfirmationDialog.new()
var confirm_ability = ConfirmationDialog.new()
var ability: Dictionary = {}          # {actor, entry, targets} waiting for confirmation
var contract: Dictionary = {}         # server contract for the multi-target spell being aimed
var start_payload: Dictionary = {}    # battle waiting for initiative
var init_pending: Dictionary = {}     # participant index -> true while the server rolls
var init_dialog = ConfirmationDialog.new()
var init_rows: Array = []             # SpinBox per participant (manual mode)
var init_bonus: Dictionary = {}       # character id -> initiative bonus from the full sheet
var init_fill: bool = false
var attack_intent: Dictionary = {}
var attack_text = Label.new()
var attack_d20 = SpinBox.new()
var ability_text = Label.new()
var ability_d20 = SpinBox.new()
var attack_chain: Dictionary = {}
var encounter_offer: Dictionary = {}
var arena_choice: String = ""
var arena_selection: String = ""
var participants_choice: Array = []
var exploration_snapshot: Dictionary = {}
var exploration_camera = Vector2.ZERO

func setup(main: Node) -> void:
	host = main
	overlay = host.battle_overlay
	host.screen.add_child(overlay)
	overlay.media = host.media
	overlay.hide()
	overlay.move_requested.connect(arena_move)
	overlay.attack_requested.connect(arena_attack)
	overlay.next_requested.connect(func(): host._send_effect("next_turn", {}))
	overlay.end_requested.connect(func(): host._send_effect("end", {}))
	overlay.ai_toggled.connect(func(on):
		ai.enabled = on
		ai.tick())
	overlay.guard_requested.connect(func(): host._send_effect("dorn_guard", {}))
	overlay.ability_requested.connect(_ability_requested)
	overlay.ability_targets.connect(_ability_targets)
	host.screen.add_child(init_dialog)
	init_dialog.title = "Iniciativa"
	init_dialog.ok_button_text = "Começar batalha"
	init_dialog.cancel_button_text = "Cancelar"
	init_dialog.add_button("Rolar d20 para todos", false, "roll")
	init_dialog.confirmed.connect(_start_with_manual_initiative)
	init_dialog.canceled.connect(func(): start_payload = {}; watch.pending = false)
	init_dialog.custom_action.connect(func(action): if action == "roll": _roll_initiative(true))
	# Confirmation dialogs carry a d20 field for the physical-dice table mode.
	for pair in [[confirm_attack, attack_text, attack_d20], [confirm_ability, ability_text, ability_d20]]:
		var box = VBoxContainer.new()
		pair[1].autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		pair[1].custom_minimum_size = Vector2(300, 0)
		box.add_child(pair[1])
		pair[2].min_value = 1
		pair[2].max_value = 20
		pair[2].value = 10
		pair[2].prefix = "d20 rolado na mesa:"
		box.add_child(pair[2])
		pair[0].add_child(box)
	confirm_attack.title = "Confirmar ataque"
	confirm_attack.ok_button_text = "Atacar"
	confirm_attack.cancel_button_text = "Cancelar"
	confirm_ability.title = "Confirmar"
	host.screen.add_child(confirm_ability)
	confirm_ability.ok_button_text = "Usar"
	confirm_ability.cancel_button_text = "Cancelar"
	confirm_ability.confirmed.connect(_send_ability)
	confirm_ability.canceled.connect(func(): ability = {})
	host.screen.add_child(confirm_attack)
	confirm_attack.confirmed.connect(func():
		if attack_d20.visible:
			attack_intent.payload.roll_mode = "physical"
			attack_intent.payload.d20 = int(attack_d20.value)
		host._send_intent("arena-resolve", attack_intent))
	ai.host = host
	add_child(ai)
	add_child(watch)
	host.screen.add_child(confirm_encounter)
	confirm_encounter.title = "Inimigos à vista!"
	confirm_encounter.ok_button_text = "Batalhar"
	confirm_encounter.cancel_button_text = "Agora não"
	confirm_encounter.add_button("Não é hostil", true, "friendly")
	confirm_encounter.confirmed.connect(func(): start_encounter(encounter_offer))
	confirm_encounter.canceled.connect(func():
		watch.snooze(encounter_offer.get("monsters", []))
		encounter_offer = {})
	confirm_encounter.custom_action.connect(func(action):
		if action == "friendly":
			for monster in encounter_offer.get("monsters", []): watch.ignored[str(monster.id)] = true
			watch.save()
			encounter_offer = {}
			confirm_encounter.hide())

func active() -> bool:
	var enc: Dictionary = host.combat_state.get("encounter", {})
	return enc.get("active", false) and enc.get("battle_mode", false)

func handles(key: String) -> bool:
	return key.begins_with("ai-") or key.begins_with("battle-") or key.begins_with("encounter-") or key.begins_with("arena-") or (key == "move" and active())

func received(key: String, data: Variant) -> void:
	if key.begins_with("ai-"):
		ai.received(key, data)
	elif key.begins_with("battle-sheet:"):
		if data is Dictionary and data.get("definition") is Dictionary:
			overlay.set_sheet(data)
	elif key.begins_with("battle-actions:"):
		if data is Dictionary and data.get("actions") is Array:
			overlay.set_actions(key.get_slice(":", 1), data.actions)
	elif key.begins_with("battle-initsheet:"):
		var index = int(key.get_slice(":", 1))
		var members: Array = start_payload.get("participants", [])
		if index < members.size():
			init_bonus[str(members[index].get("target_id", ""))] = sheet_initiative(data.get("definition", {}) if data is Dictionary and data.get("definition") is Dictionary else {})
			_roll_one(index)
	elif key.begins_with("battle-init:"):
		_initiative_rolled(int(key.get_slice(":", 1)), int(data.get("total", 0)) if data is Dictionary else 0)
	elif key == "battle-contract":
		contract = data.get("contract", {}) if data is Dictionary and data.get("contract") is Dictionary else {}
		if contract.is_empty() or ability.is_empty():
			overlay.notice("Contrato da magia indisponível agora.")
			ability = {}
			return
		overlay.begin_targeting(ability.entry, int(contract.get("targeting", {}).get("max_targets", 1)))
	elif key == "arena-technique":
		host.command_inflight = false
		host.pending_intent.clear()
		host.retry_button.hide()
		var used: Dictionary = ability
		ability = {}
		overlay.notice(str(used.get("entry", {}).get("label", "Habilidade")) + " usada")
		battle_sheets(str(used.get("actor", {}).get("character_id", "")))
		host._poll()
	elif key == "encounter-arena":
		encounter_arena(data if data is Dictionary else {})
	elif key == "encounter-grid":
		host.command_inflight = false
		host.pending_intent.clear()
		host.api.request_json("encounter-arena", "/workspace?map_id=" + arena_choice.uri_encode())
	elif key == "arena-pending":
		_confirm_pending(data)
	elif key == "move":
		host.command_inflight = false
		host.pending_intent.clear()
		host.retry_button.hide()
		host._poll()
		if not attack_chain.is_empty():
			var chain = attack_chain
			attack_chain = {}
			confirm_arena_attack(chain.actor, chain.target)
		ai.moved_ok()
	elif key == "arena-workspace":
		if not host.combat_state.get("encounter", {}).get("active", false): return
		host.arena_snapshot = data
		overlay.update_view(host.combat_state, host.arena_snapshot, host.master, host.my_profile)
		battle_sheets()
		ai.tick()
	elif key == "arena-resolve":
		var path = "/combat/attacks/" + str(data.resolution_id).uri_encode() + "/confirm"
		host.pending_intent = {"key": "arena-confirm", "path": path, "payload": {}}
		host.api.request_json("arena-confirm", path, HTTPClient.METHOD_POST, {})
	elif key == "arena-confirm":
		ability = {}
		host.pending_intent.clear()
		host.command_inflight = false
		host.retry_button.hide()
		overlay.resolved(data)
		battle_sheets(str(data.get("target_id", "")))
		host._poll()
	elif key == "arena-options":
		host.arena_snapshot = data
		if host.active_panel == "combat": host._render_panel()
	elif key == "arena-goblin":
		_add_goblin(data)
	elif key in ["arena-add", "arena-grid"]:
		host.command_inflight = false
		host.pending_intent.clear()
		host.api.request_json("arena-options", "/workspace?map_id=" + arena_selection.uri_encode())

func failed(key: String, message: String, _code: int) -> bool:
	if overlay.visible and not host.keeper.network_error(_code) and not (key in ["hud-sheet", "city", "ledger", "presence", "workspace", "characters", "maps", "sessions"] or key.begins_with("battle-") or key.begins_with("sheet:")):
		overlay.notice(message)
	if key.begins_with("ai-") or (ai.phase in ["wait", "attacking", "think"] and key in ["arena-resolve", "arena-confirm", "move"]):
		ai.failed(key)
	if key.begins_with("battle-sheet:") or key.begins_with("battle-actions:"): return true
	if key == "arena-technique" and not ability.is_empty() and ability.get("targets", []).is_empty() and ("alvo" in message.to_lower() or "selecione" in message.to_lower()):
		# The server says this one needs a target: aim and send again.
		host.command_inflight = false
		host.pending_intent.clear()
		overlay.begin_targeting(ability.entry, 1)
		return true
	if key in ["arena-technique", "battle-contract"]: ability = {}
	if key.begins_with("battle-initsheet:"):
		var index = int(key.get_slice(":", 1))
		var members: Array = start_payload.get("participants", [])
		if index < members.size(): init_bonus[str(members[index].get("target_id", ""))] = 0
		_roll_one(index)
		return true
	if key.begins_with("battle-init:"):
		overlay.notice("Rolagem de iniciativa falhou; participante fica com 0.")
		_initiative_rolled(int(key.get_slice(":", 1)), 0)
		return true
	if key in ["encounter-arena", "encounter-grid"]:
		host.command_inflight = false
		host.pending_intent.clear()
		watch.pending = false
	attack_chain = {}
	return false

## During battle the polled /workspace is the arena. Returns true when consumed.
func on_workspace(data: Variant) -> bool:
	if not active(): return false
	host.arena_snapshot = data
	overlay.update_view(host.combat_state, host.arena_snapshot, host.master, host.my_profile)
	return true

func on_combat() -> void:
	sync()
	ai.tick()

func sync() -> void:
	var enc: Dictionary = host.combat_state.get("encounter", {})
	if active():
		if exploration_snapshot.is_empty():
			exploration_snapshot = host.workspace.duplicate(true)
			exploration_camera = host.camera.position
		host.panel.hide()
		host.hud.view.hide()
		confirm_encounter.hide()
		encounter_offer = {}
		host.api.request_json("arena-workspace", "/workspace?map_id=" + str(enc.map_id).uri_encode())
		if not host.command_inflight: host.api.request_json("arena-pending", "/combat/attacks/pending")
	else:
		overlay.hide()
		if not exploration_snapshot.is_empty():
			watch.snooze(host.arena_snapshot.get("tokens", []).filter(func(t): return t.get("token_type") == "monster"), 180)
			host.workspace = exploration_snapshot
			exploration_snapshot = {}
			host.camera.position = exploration_camera
			host._received("workspace", host.workspace)
			host.api.request_json("workspace", "/workspace")

func _confirm_pending(data: Variant) -> void:
	if host.command_inflight or not host.pending_intent.is_empty() or not host.combat_state.get("encounter", {}).get("active", false): return
	var encounter: Dictionary = host.combat_state.get("encounter", {})
	var members: Array = encounter.get("participants", [])
	if members.is_empty(): return
	var current: Dictionary = members[int(encounter.get("turn_index", 0))]
	var identity = [encounter.get("started_at"), encounter.get("turn_sequence"), current.get("target_type"), current.get("target_id")]
	for item in data if data is Array else []:
		if item.get("breakdown", {}).get("combat_turn") != identity: continue
		if str(item.get("request_id", "")).begins_with("arena-attack-") and not item.get("confirmed", false):
			host._send_intent("arena-confirm", {"path": "/combat/attacks/" + str(item.resolution_id).uri_encode() + "/confirm", "payload": {}})
			break

func battle_sheets(refresh: String = "") -> void:
	for token in overlay._battle_tokens():
		if not token.get("character_id"): continue
		var id = str(token.character_id)
		if (not overlay.states.has(id) or id == refresh):
			host.api.request_json("battle-sheet:" + id, "/characters/" + id.uri_encode() + "?read_only=true")
			host.api.request_json("battle-actions:" + id, "/characters/" + id.uri_encode() + "/action-manifest")

# --- Magias e habilidades -------------------------------------------------------
func _ability_requested(actor: Dictionary, entry: Dictionary) -> void:
	ability = {"actor": actor, "entry": entry, "targets": []}
	var binding = str(entry.get("binding", ""))
	var execution: Dictionary = entry.get("execution", {}) if entry.get("execution") is Dictionary else {}
	if binding == "dorn_spell":
		if not host.master:
			overlay.notice("Magias do Dorn com área usam o contrato do Mestre.")
			ability = {}
			return
		host.api.request_json("battle-contract", "/gm/actions/describe?ref=" + str(entry.get("ref", "")).uri_encode())
	elif execution.get("confirmation_endpoint") or binding == "vine_bracelet":
		overlay.begin_targeting(entry, 1)
	else:
		_ask_ability("Usar " + str(entry.get("label", "habilidade")) + "?", false)

func _ability_targets(entry: Dictionary, targets: Array) -> void:
	if ability.is_empty() or ability.entry != entry: return
	ability.targets = targets
	var names = targets.map(func(t): return str(t.get("name", "alvo")))
	var execution: Dictionary = entry.get("execution", {}) if entry.get("execution") is Dictionary else {}
	_ask_ability(str(entry.get("label", "Habilidade")) + " em " + ", ".join(names) + "?", execution.get("confirmation_endpoint") != null and ability.get("actor", {}).get("character_id") != null)

func _ask_ability(text: String, attack_like: bool) -> void:
	ability_text.text = text
	ability_d20.visible = attack_like and host.dice.physical()
	confirm_ability.popup_centered(Vector2i(380, 190 if ability_d20.visible else 150))

func _send_ability() -> void:
	if ability.is_empty(): return
	var entry: Dictionary = ability.entry
	var actor: Dictionary = ability.actor
	var targets: Array = ability.targets
	var execution: Dictionary = entry.get("execution", {}) if entry.get("execution") is Dictionary else {}
	var binding = str(entry.get("binding", ""))
	var request_id = "arena-ability-" + Crypto.new().generate_random_bytes(10).hex_encode()
	if binding == "dorn_protocol":
		ability = {}
		host._send_effect(str(execution.get("action", "dorn_guard")), {})
		return
	if binding == "dorn_spell":
		var list: Array = targets.map(func(t): return {"type": "token", "id": str(t.id)})
		var spell: Dictionary = execution.get("payload", {}) if execution.get("payload") is Dictionary else {}
		ability = {}
		host._send_effect("dorn_spell_cast", {"spell_id": str(spell.get("spell_id", "")), "grid_selection": true,
			"map_id": str(host.arena_snapshot.get("map", {}).get("id", "")), "definition_revision": contract.get("revision"), "targets": list})
		return
	# Items and state powers use the same commands as the "Poderes" panel; the server validates turn and uses.
	var owner = str(actor.get("character_id", ""))
	var label = str(entry.get("label", "Poder"))
	if binding in ["inventory_item", "character_state_action"] and owner != "":
		var action = str(execution.get("action", "use_item" if binding == "inventory_item" else "consume_resource"))
		var inner: Dictionary = (execution.get("payload", {}) as Dictionary).duplicate(true) if execution.get("payload") is Dictionary else {}
		if str(entry.get("ref", "")).ends_with(":forma-da-noite"):
			var sheet_definition: Dictionary = overlay.states.get(owner, {}).get("definition", {}) if overlay.states.get(owner) is Dictionary else {}
			inner = {"resource_key": host.powers._resource_key(sheet_definition, "forma-da-noite", "forma_da_noite"), "amount": 1, "animal": host.powers.animal}
			label = "Forma da Noite: " + str(host.powers.animal)
		host._send_intent("arena-technique", {"path": "/characters/" + owner.uri_encode() + "/actions",
			"payload": {"action": action, "payload": inner, "reason": ("Usou " + label).left(400), "request_id": request_id}})
		return
	if binding == "vine_bracelet":
		if targets.is_empty(): return
		host._send_intent("arena-technique", {"path": str(execution.get("endpoint", "")),
			"payload": {"target_type": "token", "target_id": str(targets[0].id), "request_id": request_id}})
		return
	var payload: Dictionary = (execution.get("payload", {}) as Dictionary).duplicate(true) if execution.get("payload") is Dictionary else {}
	payload.request_id = request_id
	payload.roll_mode = "digital"
	if ability_d20.visible:
		payload.roll_mode = "physical"
		payload.d20 = int(ability_d20.value)
	if not targets.is_empty():
		var target: Dictionary = targets[0]
		payload.target_type = "character" if target.get("character_id") else "token"
		payload.target_id = str(target.character_id) if target.get("character_id") else str(target.id)
	if str(execution.get("endpoint", "")).ends_with("/attacks/resolve"):
		payload.grid_automatic = true
	# Attack-like abilities return a resolution that is then confirmed, exactly like weapons.
	host._send_intent("arena-resolve" if execution.get("confirmation_endpoint") else "arena-technique", {"path": str(execution.get("endpoint", "")), "payload": payload})

func arena_move(token: Dictionary, cell: Vector2i, route: Array = []) -> void:
	var position: Dictionary = token.get("grid_position", {})
	if position.is_empty(): return
	var dims: Vector2i = overlay._grid_size()
	var steps: Array = route if not route.is_empty() else Commands.path_around(Vector2i(int(position.cell_x), int(position.cell_y)), cell, overlay.blocked, dims.x, dims.y)
	if steps.is_empty():
		overlay.notice("Sem caminho livre até lá.")
		return
	var snapshot: Dictionary = host.arena_snapshot
	host._send_intent("move", {"path": "/workspace/maps/" + str(snapshot.map.id).uri_encode() + "/move", "payload": {
		"request_id": "arena-move-" + Crypto.new().generate_random_bytes(12).hex_encode(), "token_id": token.id, "mode": "COMBAT_MOVE", "path": steps,
		"expected_position_version": int(position.version), "expected_grid_version": int(snapshot.map.grid.version),
		"expected_combat_version": int(host.combat_state.version)}})

func arena_attack(actor: Dictionary, target: Dictionary) -> void:
	# Melee from the rear line: step to the front first (server checks the budget).
	if overlay.attack_melee and overlay.reach(actor, target) > 1:
		var cell = overlay.forward_cell(actor, target)
		if cell != overlay.cell_of(actor):
			attack_chain = {"actor": actor, "target": target}
			overlay.notice(str(actor.get("name", "")) + " avança até " + str(target.get("name", "o alvo")))
			arena_move(actor, cell)
			return
	confirm_arena_attack(actor, target)

func confirm_arena_attack(actor: Dictionary, target: Dictionary) -> void:
	var path = "/characters/" + str(actor.character_id) + "/attacks/resolve" if actor.get("character_id") else "/gm/combat/tokens/" + str(actor.id).uri_encode() + "/attacks/resolve"
	var payload = {"request_id": "arena-attack-" + Crypto.new().generate_random_bytes(12).hex_encode(), "attack_id": overlay.attack_id,
		"target_type": "character" if target.get("character_id") else "token", "target_id": target.get("character_id") if target.get("character_id") else target.id,
		"roll_mode": "digital", "grid_automatic": true}
	if not actor.get("character_id"):
		# Same rule as the server proposals: melee reaches 1 cell; ranged uses the attack's own range.
		var attacks: Array = actor.get("sheet", {}).get("attacks", []) if actor.get("sheet") is Dictionary else []
		var index = int(overlay.attack_id) if str(overlay.attack_id).is_valid_int() else -1
		var raw: Dictionary = attacks[index] if index >= 0 and index < attacks.size() and attacks[index] is Dictionary else {}
		if not overlay.attack_melee and raw.get("range_m") != null: payload.range_m = float(raw.range_m)
		else: payload.range_cells = 1
	attack_intent = {"path": path, "payload": payload}
	attack_text.text = str(actor.get("name", "Atacante")) + " ataca " + str(target.get("name", "alvo")) + "?"
	attack_d20.visible = host.dice.physical() and actor.get("character_id") != null
	confirm_attack.popup_centered(Vector2i(380, 200 if attack_d20.visible else 160))

# --- Proximity encounters (GM only) -------------------------------------------
func watch_exploration(data: Dictionary) -> void:
	if not host.master or watch.pending or not encounter_offer.is_empty() or confirm_encounter.visible: return
	if not host.combat_state.has("version") or overlay.visible or host.town.screen_visible(): return
	if host.combat_state.get("encounter", {}).get("active", false): return
	if not data.get("map", {}).get("grid") is Dictionary: return
	# No encounters inside the city: its map is a menu of places, not a battlefield.
	if host.town.city_map_id() != "" and str(data.get("map", {}).get("id", "")) == host.town.city_map_id(): return
	var found = watch.scan(data, Time.get_ticks_msec())
	if found.is_empty(): return
	encounter_offer = found
	var names = found.monsters.map(func(m): return str(m.get("name", "Criatura")))
	if watch.auto_mode:
		host._notice("Batalha automática · " + ", ".join(names))
		start_encounter(found)
	else:
		confirm_encounter.dialog_text = ", ".join(names) + " perto do grupo.\nEntrar na tela de batalha agora?"
		confirm_encounter.popup_centered(Vector2i(380, 170))

func arena_candidates() -> Array:
	var current = str(host.workspace.get("map", {}).get("id", ""))
	var list = host.maps.filter(func(m): return m.get("visible_to_players", false) and str(m.id) != current and str(m.id) != host.town.city_map_id())
	list.sort_custom(func(a, b): return ("arena" in str(a.title).to_lower()) and not ("arena" in str(b.title).to_lower()))
	return list

func start_encounter(found: Dictionary) -> void:
	if not host.master or found.is_empty(): return
	watch.pending = true
	var candidates = arena_candidates()
	arena_choice = watch.arena_map_id
	if arena_choice == "" or not candidates.any(func(m): return str(m.id) == arena_choice):
		arena_choice = str(candidates[0].id) if not candidates.is_empty() else ""
	if arena_choice == "":
		watch.pending = false
		encounter_offer = {}
		host._notice("Nenhum mapa de arena visível. Revele um mapa na biblioteca.")
		return
	host.api.request_json("encounter-arena", "/workspace?map_id=" + arena_choice.uri_encode())

func encounter_arena(arena: Dictionary) -> void:
	if encounter_offer.is_empty():
		watch.pending = false
		return
	if not arena.get("map", {}).get("grid") is Dictionary:
		host._send_intent("encounter-grid", {"path": "/workspace/maps/" + arena_choice.uri_encode() + "/grid", "payload": {"request_id": "encounter-grid-" + Crypto.new().generate_random_bytes(10).hex_encode(), "expected_version": 0, "cols": 12, "rows": 8, "cell_size_m": 1}})
		return
	var payload = watch.build_payload(encounter_offer.monsters, encounter_offer.heroes, arena)
	watch.snooze(encounter_offer.monsters, 30)
	encounter_offer = {}
	watch.pending = false
	begin_start(payload)

# --- GM drawer: encounter settings and manual battle --------------------------
func render_panel(body: Node) -> void:
	if host.combat_state.get("encounter", {}).get("active", false):
		var reopen = Button.new()
		reopen.text = "Abrir arena"
		reopen.pressed.connect(func(): overlay.show())
		body.add_child(reopen)
		return
	if not host.master: return
	_encounter_settings(body)
	host._label(body, "Batalha manual", 16)
	var choices = OptionButton.new()
	for map in host.maps:
		if not map.get("visible_to_players", false) or str(map.id) == str(host.workspace.get("map", {}).get("id", "")): continue
		choices.add_item(str(map.title))
		choices.set_item_metadata(choices.item_count - 1, str(map.id))
		if str(map.id) == arena_selection: choices.select(choices.item_count - 1)
	choices.item_selected.connect(func(i):
		arena_selection = str(choices.get_item_metadata(i))
		participants_choice.clear()
		host.api.request_json("arena-options", "/workspace?map_id=" + arena_selection.uri_encode()))
	body.add_child(choices)
	if arena_selection.is_empty() and choices.item_count:
		arena_selection = str(choices.get_item_metadata(0))
		host.api.request_json("arena-options", "/workspace?map_id=" + arena_selection.uri_encode())
	var displayed: Array = []
	for token in host.workspace.get("tokens", []) + host.arena_snapshot.get("tokens", []):
		if token.get("token_type") == "location": continue
		var id = str(token.get("character_id") if token.get("character_id") else token.id)
		if id in displayed or not token.get("visible_to_players", true): continue
		displayed.append(id)
		var check = CheckBox.new()
		check.text = str(token.get("name", id))
		check.button_pressed = id in participants_choice
		check.toggled.connect(func(on):
			if on and not id in participants_choice: participants_choice.append(id)
			elif not on: participants_choice.erase(id))
		body.add_child(check)
	var ready_grid = host.arena_snapshot.get("map", {}).get("id") == arena_selection and host.arena_snapshot.get("map", {}).get("grid") is Dictionary
	if not ready_grid:
		var prepare = Button.new()
		prepare.text = "Preparar grade 12 × 8 (1 m)"
		prepare.pressed.connect(func(): host._send_intent("arena-grid", {"path": "/workspace/maps/" + arena_selection.uri_encode() + "/grid", "payload": {"request_id": "arena-grid-" + Crypto.new().generate_random_bytes(12).hex_encode(), "expected_version": 0, "cols": 12, "rows": 8, "cell_size_m": 1}}))
		body.add_child(prepare)
	var goblin = Button.new()
	goblin.disabled = not ready_grid
	goblin.text = "Adicionar Goblin do bestiário"
	goblin.pressed.connect(func(): host.api.request_json("arena-goblin", "/gm/workspace/monster-catalog?q=Goblin"))
	body.add_child(goblin)
	var start = Button.new()
	start.disabled = not ready_grid
	start.text = "Iniciar batalha"
	start.pressed.connect(start_manual)
	body.add_child(start)

func start_manual() -> void:
	if not host.master or arena_selection.is_empty() or participants_choice.is_empty(): return
	if arena_selection == str(host.workspace.get("map", {}).get("id", "")):
		host._notice("Escolha uma arena diferente do mapa de exploração para preservar as posições.")
		return
	var heroes: Array = []
	var monsters: Array = []
	var seen: Array = []
	for token in host.workspace.get("tokens", []) + host.arena_snapshot.get("tokens", []):
		var id = str(token.get("character_id") if token.get("character_id") else token.id)
		if not id in participants_choice or id in seen: continue
		seen.append(id)
		if token.get("character_id"): heroes.append(token)
		else: monsters.append(token)
	var payload = watch.build_payload(monsters, heroes, host.arena_snapshot)
	payload.title = "Batalha"
	begin_start(payload)

func _add_goblin(data: Variant) -> void:
	var options: Array = data.get("monsters", []) if data is Dictionary else []
	var base: Dictionary = {}
	for item in options:
		if item.get("id") == "goblin": base = item
	if base.is_empty(): return
	var sheet_data = base.duplicate(true)
	if base.get("encounter_defaults") is Dictionary:
		sheet_data.attacks = base.encounter_defaults.get("attacks", base.get("attacks", []))
	var geometry: Dictionary = host.arena_snapshot.get("map", {}).get("grid", {})
	var cols = maxi(1, int(geometry.get("cols", 12)))
	var rows = maxi(1, int(geometry.get("rows", 8)))
	var spawn = Vector2i(cols / 2 + 1, rows / 2)
	host._send_intent("arena-add", {"path": "/gm/workspace/tokens", "payload": {"token_type": "monster", "name": base.name, "map_id": arena_selection,
		"image_path": base.get("image_path"), "latitude": (spawn.y + 0.5) * 100 / rows, "longitude": (spawn.x + 0.5) * 100 / cols,
		"maximum_hp": int(base.get("average_hp", 4)), "current_hp": int(base.get("average_hp", 4)), "sheet": sheet_data}})

func _encounter_settings(parent: Node) -> void:
	host._label(parent, "Encontros por proximidade", 17)
	var auto = CheckButton.new()
	auto.text = "Modo automático (sem perguntar)"
	auto.button_pressed = watch.auto_mode
	auto.toggled.connect(func(on): watch.auto_mode = on; watch.save())
	parent.add_child(auto)
	var radius_row = HBoxContainer.new()
	parent.add_child(radius_row)
	var radius_text = host._label(radius_row, "Raio de alerta (células)", 14)
	radius_text.autowrap_mode = TextServer.AUTOWRAP_OFF
	radius_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var radius = SpinBox.new()
	radius.min_value = 1
	radius.max_value = 12
	radius.value = watch.radius
	radius.value_changed.connect(func(v): watch.radius = int(v); watch.save())
	radius_row.add_child(radius)
	var arenas = OptionButton.new()
	arenas.add_item("Arena: escolher automaticamente")
	arenas.set_item_metadata(0, "")
	for map in arena_candidates():
		arenas.add_item("Arena: " + str(map.title))
		arenas.set_item_metadata(arenas.item_count - 1, str(map.id))
		if str(map.id) == watch.arena_map_id: arenas.select(arenas.item_count - 1)
	arenas.item_selected.connect(func(i): watch.arena_map_id = str(arenas.get_item_metadata(i)); watch.save())
	parent.add_child(arenas)
	var initiative = OptionButton.new()
	for entry in [["d20", "Iniciativa: d20 + bônus da ficha (servidor)"], ["manual", "Iniciativa: o Mestre digita"], ["fixed", "Iniciativa: ordem fixa (heróis primeiro)"]]:
		initiative.add_item(entry[1])
		initiative.set_item_metadata(initiative.item_count - 1, entry[0])
		if entry[0] == watch.initiative_mode: initiative.select(initiative.item_count - 1)
	initiative.item_selected.connect(func(i): watch.initiative_mode = str(initiative.get_item_metadata(i)); watch.save())
	parent.add_child(initiative)
	host._label(parent, "Formação inicial", 15)
	for character in host.characters:
		var id = str(character.id)
		var toggle = CheckButton.new()
		toggle.text = str(character.name) + " na linha de frente"
		toggle.button_pressed = watch.row_of(id) == "front"
		toggle.toggled.connect(func(on): watch.rows[id] = "front" if on else "back"; watch.save())
		parent.add_child(toggle)
	if not watch.ignored.is_empty():
		var reset = Button.new()
		reset.text = "Voltar a considerar hostis (%d)" % watch.ignored.size()
		reset.pressed.connect(func(): watch.ignored.clear(); watch.save(); host._render_panel())
		parent.add_child(reset)

func clear() -> void:
	overlay.hide()
	exploration_snapshot = {}
	encounter_offer = {}
	attack_chain = {}


# --- Iniciativa ----------------------------------------------------------------
## Server dice (POST /rolls, visible on the table log) or GM-typed values. The server
## orders by initiative on start; ties keep the formation order (heroes first).
func begin_start(payload: Dictionary) -> void:
	start_payload = payload
	init_bonus.clear()
	match watch.initiative_mode:
		"fixed":
			_send_start()
		"manual":
			_show_initiative_dialog()
		_:
			_roll_initiative(false)

func _roll_initiative(fill_dialog: bool) -> void:
	init_pending.clear()
	init_fill = fill_dialog
	var members: Array = start_payload.get("participants", [])
	for index in range(members.size()):
		init_pending[index] = fill_dialog
	for index in range(members.size()):
		var member: Dictionary = members[index]
		var id = str(member.get("target_id", ""))
		if member.get("target_type") == "character" and not init_bonus.has(id):
			# Bonus lives in the full sheet (DEX modifier unless the sheet sets initiative).
			host.api.request_json("battle-initsheet:" + str(index), "/characters/" + id.uri_encode() + "?read_only=true")
		else:
			_roll_one(index)
	if members.is_empty(): _send_start()

func _roll_one(index: int) -> void:
	var members: Array = start_payload.get("participants", [])
	if index >= members.size() or not init_pending.has(index): return
	var member: Dictionary = members[index]
	var bonus = initiative_bonus(member)
	member["initiative_bonus"] = bonus
	var formula = "1d20" + ("%+d" % bonus if bonus != 0 else "")
	var body = {"request_id": "initiative-" + Crypto.new().generate_random_bytes(10).hex_encode(), "formula": formula,
		"label": "Iniciativa · " + str(member.get("name", "")), "visibility": "table"}
	if member.get("target_type") == "character": body.character_id = str(member.target_id)
	host.api.request_json("battle-init:" + str(index), "/rolls", HTTPClient.METHOD_POST, body)

## Sheet initiative bonus: characters from /characters, monsters from token sheet.
func initiative_bonus(member: Dictionary) -> int:
	var id = str(member.get("target_id", ""))
	var raw: Variant = null
	if member.get("target_type") == "character":
		if init_bonus.has(id): return int(init_bonus[id])
		for summary in host.characters:
			if summary is Dictionary and str(summary.get("id", "")) == id: raw = summary.get("initiative")
	else:
		var pool: Array = []
		for snapshot in [host.workspace, exploration_snapshot, host.arena_snapshot]:
			if snapshot is Dictionary: pool.append_array(snapshot.get("tokens", []))
		for token in pool:
			if token is Dictionary and str(token.get("id", "")) == id and token.get("sheet") is Dictionary: raw = token.sheet.get("initiative")
	return parse_bonus(raw)

## Configured sheet initiative wins; otherwise Old Dragon DEX modifier, floor((DES-10)/2).
static func sheet_initiative(definition: Dictionary) -> int:
	var defenses: Dictionary = definition.get("defenses", {}) if definition.get("defenses") is Dictionary else {}
	if defenses.get("initiative_configured") and defenses.get("initiative") != null:
		return parse_bonus(defenses.initiative)
	var attributes: Dictionary = definition.get("attributes", {}) if definition.get("attributes") is Dictionary else {}
	if attributes.has("dexterity"):
		return int(floor((float(attributes.dexterity) - 10.0) / 2.0))
	return 0

static func parse_bonus(raw: Variant) -> int:
	if raw is int or raw is float: return clampi(int(raw), -50, 50)
	if raw is Dictionary:
		for key in ["total", "value", "bonus", "modifier"]:
			if raw.has(key): return parse_bonus(raw[key])
		return 0
	var text = str(raw if raw != null else "").strip_edges().replace(" ", "")
	var found = RegEx.create_from_string("[+-]?\\d+").search(text)
	return clampi(int(found.get_string()), -50, 50) if found else 0

func _initiative_rolled(index: int, total: int) -> void:
	if not init_pending.has(index) or start_payload.is_empty(): return
	var into_dialog: bool = init_pending[index]
	init_pending.erase(index)
	var members: Array = start_payload.participants
	if index < members.size(): members[index].initiative = total
	if into_dialog and index < init_rows.size():
		init_rows[index].value = total
	if init_pending.is_empty() and not into_dialog:
		var order = members.map(func(m): return str(m.get("name", "")) + " " + str(m.initiative) + (" (%+d)" % int(m.initiative_bonus) if int(m.get("initiative_bonus", 0)) != 0 else ""))
		overlay.notice("Iniciativa: " + ", ".join(order))
		_send_start()

func _show_initiative_dialog() -> void:
	for child in init_dialog.get_children():
		if child is VBoxContainer: child.queue_free()
	init_rows.clear()
	var box = VBoxContainer.new()
	init_dialog.add_child(box)
	for member in start_payload.get("participants", []):
		var row = HBoxContainer.new()
		var name = Label.new()
		name.text = str(member.get("name", ""))
		name.custom_minimum_size.x = 180
		row.add_child(name)
		var value = SpinBox.new()
		value.min_value = -99
		value.max_value = 999
		value.value = int(member.get("initiative", 0))
		row.add_child(value)
		box.add_child(row)
		init_rows.append(value)
	init_dialog.popup_centered(Vector2i(360, 120 + 40 * init_rows.size()))

func _start_with_manual_initiative() -> void:
	var members: Array = start_payload.get("participants", [])
	for index in range(mini(members.size(), init_rows.size())):
		members[index].initiative = int(init_rows[index].value)
	_send_start()

func _send_start() -> void:
	if start_payload.is_empty(): return
	var payload = start_payload
	start_payload = {}
	init_pending.clear()
	for member in payload.get("participants", []):
		if member is Dictionary: member.erase("initiative_bonus")
	host._send_effect("start", payload)
