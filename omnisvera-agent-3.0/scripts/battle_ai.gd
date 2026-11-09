extends Node
## Simple creature AI for the GM client. It only chooses among the server's own
## assisted proposals (GET /gm/combat/tokens/{id}/action-proposals) or walks toward
## the nearest hero with COMBAT_MOVE; the server validates and resolves everything.
const Commands = preload("res://scripts/game_commands.gd")
var host: Node
var enabled: bool = true
var turn_key: String = ""
var phase: String = "idle"
var moved: bool = false
var waiting_since: int = 0
var timer = Timer.new()

func _ready() -> void:
	timer.one_shot = true
	timer.timeout.connect(_act)
	add_child(timer)

func current_monster() -> Dictionary:
	var enc: Dictionary = host.combat_state.get("encounter", {})
	if not host.master or not enabled or not enc.get("active", false) or not enc.get("battle_mode", false):
		return {}
	var members: Array = enc.get("participants", [])
	if members.is_empty(): return {}
	var current: Dictionary = members[int(enc.get("turn_index", 0)) % members.size()]
	if current.get("target_type") != "token": return {}
	for token in host.arena_snapshot.get("tokens", []):
		if str(token.get("id")) == str(current.get("target_id")):
			if token.get("sheet", {}).get("summon", {}).get("caster"): return {}
			return token
	return {}

## Called whenever combat or arena state refreshes.
func tick() -> void:
	var token = current_monster()
	if token.is_empty():
		phase = "idle"
		return
	var enc: Dictionary = host.combat_state.encounter
	var key = str(enc.get("started_at", "")) + ":" + str(enc.get("turn_sequence", 0))
	if key != turn_key:
		turn_key = key
		moved = false
		phase = "think"
		waiting_since = Time.get_ticks_msec()
		_schedule(0.45)
		return
	if enc.get("action_committed", false) and phase != "ending":
		phase = "ending"
		_schedule(0.6)
	elif phase == "wait" and Time.get_ticks_msec() - waiting_since > 6000:
		phase = "ending"  # Watchdog: never stall the table.
		_schedule(0.2)

func _schedule(seconds: float) -> void:
	timer.start(seconds)

func _busy() -> bool:
	return host.command_inflight or not host.pending_intent.is_empty()

func _act() -> void:
	var token = current_monster()
	if token.is_empty(): return
	if _busy():
		_schedule(0.4)
		return
	match phase:
		"think":
			var heroes: Array = host.battle_overlay.enemies_of(token)
			if heroes.is_empty():
				phase = "ending"; _schedule(0.5); return
			var query = PackedStringArray()
			for hero in heroes: query.append("target_token_ids=" + str(hero.id).uri_encode())
			phase = "wait"
			waiting_since = Time.get_ticks_msec()
			host.api.request_json("ai-proposals", "/gm/combat/tokens/" + str(token.id).uri_encode() + "/action-proposals?" + "&".join(query))
		"ending":
			phase = "done"
			host.battle_overlay.notice(str(token.get("name", "Criatura")) + " encerra o turno")
			host._send_effect("next_turn", {})

func received(key: String, data: Variant) -> void:
	if key != "ai-proposals" or phase != "wait": return
	var token = current_monster()
	if token.is_empty() or not data is Dictionary: return
	var proposals: Array = data.get("proposals", [])
	if not proposals.is_empty():
		var choice: Dictionary = proposals[0]
		var nearest = float(choice.get("distance", {}).get("meters", 0))
		for proposal in proposals:
			if float(proposal.get("distance", {}).get("meters", 0)) > nearest: continue
			if _target_hp(proposal) < _target_hp(choice): choice = proposal
		var payload: Dictionary = choice.get("request", {}).duplicate(true)
		payload.request_id = "arena-attack-ai-" + Crypto.new().generate_random_bytes(10).hex_encode()
		payload.roll_mode = "digital"
		phase = "attacking"
		host.battle_overlay.notice(str(token.get("name", "Criatura")) + " ataca " + str(choice.get("target_name", "")) + " com " + str(choice.get("name", "ataque")))
		host._send_intent("arena-resolve", {"path": str(choice.get("resolve_endpoint")), "payload": payload})
		return
	if not moved:
		moved = true
		var target: Dictionary = host.battle_overlay.nearest_enemy(token)
		var goal: Vector2i = host.battle_overlay.forward_cell(token, target)
		var origin: Vector2i = host.battle_overlay.cell_of(token)
		var path: Array = Commands.path_between(origin, goal)
		var budget = _movement_cells(token)
		if path.size() > budget + 1: path = path.slice(0, budget + 1)
		if path.size() > 1:
			phase = "think"
			waiting_since = Time.get_ticks_msec()
			host.battle_overlay.notice(str(token.get("name", "Criatura")) + " avança")
			var last: Array = path[path.size() - 1]
			host.battle.arena_move(token, Vector2i(int(last[0]), int(last[1])), path)
			return
	phase = "ending"
	_schedule(0.6)

func failed(key: String) -> void:
	if key.begins_with("ai-") or phase in ["wait", "attacking"]:
		phase = "ending"
		_schedule(0.8)

## After a confirmed move the AI looks for an attack again.
func moved_ok() -> void:
	if phase == "think":
		_schedule(0.35)

func _target_hp(proposal: Dictionary) -> float:
	var id = str(proposal.get("request", {}).get("target_id", ""))
	for token in host.arena_snapshot.get("tokens", []):
		if str(token.get("character_id", "")) == id or str(token.get("id")) == id:
			return float(token.get("current_hp") if token.get("current_hp") != null else 999)
	return 999.0

func _movement_cells(token: Dictionary) -> int:
	var raw = str(token.get("sheet", {}).get("movement", "6"))
	var digits = RegEx.new()
	digits.compile("[0-9]+([.,][0-9]+)?")
	var found = digits.search(raw)
	var meters = float(found.get_string().replace(",", ".")) if found else 6.0
	var cell = float(host.arena_snapshot.get("map", {}).get("grid", {}).get("cell_size_m", 1))
	return maxi(1, int(floor(meters / maxf(cell, 0.1))))
