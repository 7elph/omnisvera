extends Node
## Ações de pin no mapa, para Mestre e jogadores:
## - "Saquear espólio" em monstro derrotado com tesouro (o servidor rola e reparte entre o grupo);
## - "Negociar" em qualquer pin que tenha loja ou serviço (mesma tela de comércio da cidade).

var host: Node
var current: Dictionary = {}       # pin shown in the detail drawer
var busy: bool = false

func setup(main: Node) -> void:
	host = main

func handles(key: String) -> bool:
	return key.begins_with("pin-commerce:") or key in ["loot-collect", "summon-dismiss", "mon-resolve", "mon-confirm"]

func clear() -> void:
	current = {}
	busy = false

static func can_loot(pin: Dictionary) -> bool:
	if str(pin.get("token_type", "")) != "monster": return false
	if pin.get("current_hp") == null or int(pin.current_hp) > 0: return false
	var sheet: Dictionary = pin.get("sheet", {}) if pin.get("sheet") is Dictionary else {}
	if sheet.get("loot_collected") or sheet.get("summon") or sheet.get("disintegrated") or sheet.get("reanimated_by"): return false
	# Same rule as the 2.0 table: a treasure code like "A", "B+C" (not "-" or "(ver texto)").
	var treasure = str(sheet.get("treasure", "")).split("(")[0]
	return RegEx.create_from_string("[A-Za-z]").search(treasure) != null

## Called right after the pin drawer is filled.
func shown(pin: Dictionary) -> void:
	current = pin
	if not pin.get("id"): return
	if can_loot(pin):
		var loot = Button.new()
		loot.text = "Saquear espólio (repartir entre o grupo)"
		loot.disabled = busy
		loot.pressed.connect(func(): collect(pin))
		host.detail_body.add_child(loot)
	if host.master and str(pin.get("token_type", "")) == "monster" and pin.get("current_hp") != null and int(pin.current_hp) > 0:
		_monster_attack(pin)
	var summon: Dictionary = pin.get("sheet", {}).get("summon", {}) if pin.get("sheet") is Dictionary and pin.sheet.get("summon") is Dictionary else {}
	var caster = str(summon.get("caster", ""))
	if caster != "" and (host.master or caster == host.my_profile) and str(summon.get("technique", "")) != "clonagem" \
			and pin.get("current_hp") != null and int(pin.current_hp) > 0:
		var dismiss = Button.new()
		dismiss.text = "Dispensar invocação (o uso diário não volta)"
		dismiss.pressed.connect(func():
			host.api.request_json("summon-dismiss", "/characters/" + caster.uri_encode() + "/techniques/dispensar-invocacao", HTTPClient.METHOD_POST,
				{"request_id": "dismiss-" + str(pin.id).sha256_text().left(24), "target_type": "token", "target_id": str(pin.id)})
			host.detail_panel.hide())
		host.detail_body.add_child(dismiss)
		return
	if str(pin.get("token_type", "")) in ["location", "monster", "npc"] and int(pin.get("current_hp", 1) if pin.get("current_hp") != null else 1) > 0:
		var who = host.hud.controlled_id()
		var query = "?character_id=" + who.uri_encode() if who != "" else ""
		host.api.request_json("pin-commerce:" + str(pin.id), "/workspace/tokens/" + str(pin.id).uri_encode() + "/commerce" + query)

## GM attack with a monster from its pin, outside the battle screen (2.0 MonsterAttackPanel).
## The server checks range on gridded maps; melee reaches 1 cell, ranged uses the attack's range.
func _monster_attack(pin: Dictionary) -> void:
	var attacks: Array = pin.get("sheet", {}).get("attacks", []) if pin.get("sheet") is Dictionary else []
	if attacks.is_empty(): return
	var row = HBoxContainer.new()
	host.detail_body.add_child(row)
	var which = OptionButton.new()
	which.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for index in range(attacks.size()):
		var attack: Dictionary = attacks[index] if attacks[index] is Dictionary else {}
		which.add_item("%s %s %s" % [str(attack.get("name", "Ataque")), ("%+d" % int(attack.bonus)) if (attack.get("bonus") is float or attack.get("bonus") is int) else str(attack.get("bonus", "")), str(attack.get("damage", ""))])
		which.set_item_metadata(which.item_count - 1, index)
	row.add_child(which)
	var target = OptionButton.new()
	target.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for token in host.workspace.get("tokens", []):
		if str(token.get("id", "")) == str(pin.id) or str(token.get("token_type", "")) == "location": continue
		if token.get("current_hp") != null and int(token.current_hp) <= 0: continue
		target.add_item(str(token.get("name", "")))
		target.set_item_metadata(target.item_count - 1, token)
	if target.item_count == 0: return
	row.add_child(target)
	var go = Button.new()
	go.text = "Atacar"
	go.disabled = busy
	go.pressed.connect(func():
		var index = int(which.get_item_metadata(which.selected))
		var chosen: Dictionary = target.get_item_metadata(target.selected)
		var attack: Dictionary = attacks[index] if attacks[index] is Dictionary else {}
		var ranged = str(attack.get("slot", "")) == "ranged" or (attack.get("range_m") != null and str(attack.get("slot", "")) != "melee")
		var payload = {"request_id": "mon-" + Crypto.new().generate_random_bytes(10).hex_encode(), "attack_id": str(index),
			"target_type": "character" if chosen.get("character_id") else "token",
			"target_id": str(chosen.character_id) if chosen.get("character_id") else str(chosen.id), "roll_mode": "digital"}
		if ranged and attack.get("range_m") != null: payload.range_m = float(attack.range_m)
		else: payload.range_cells = 1
		busy = true
		host.api.request_json("mon-resolve", "/gm/combat/tokens/" + str(pin.id).uri_encode() + "/attacks/resolve", HTTPClient.METHOD_POST, payload)
		host._notice(str(pin.get("name", "Criatura")) + " ataca " + str(chosen.get("name", "")) + "…"))
	row.add_child(go)

static func attack_line(record: Dictionary) -> String:
	var labels = {"hit": "acertou", "miss": "errou", "critical": "crítico!", "critical_hit": "crítico!", "critical_failure": "falha crítica"}
	return "%s → %s · d20 %d · %s · %d de dano" % [str(record.get("actor_name", "")), str(record.get("target_name", "")), int(record.get("d20", 0)),
		labels.get(str(record.get("result", "")), str(record.get("result", ""))), int(record.get("damage_total", 0))]

func collect(pin: Dictionary) -> void:
	if busy: return
	busy = true
	host.api.request_json("loot-collect", "/workspace/loot/collect", HTTPClient.METHOD_POST,
		{"token_id": str(pin.id), "request_id": "loot-" + str(pin.id).sha256_text().left(24)})
	host.detail_panel.hide()
	host._notice("Repartindo o espólio de " + str(pin.get("name", "")) + "…")

func received(key: String, payload: Variant) -> void:
	if key.begins_with("pin-commerce:"):
		var id = key.substr("pin-commerce:".length())
		var shops: Array = payload if payload is Array else []
		if shops.is_empty() or str(current.get("id", "")) != id or not host.detail_panel.visible: return
		var trade = Button.new()
		var names = ", ".join(shops.map(func(s): return str(s.get("name", "Loja"))))
		trade.text = "Negociar · " + names
		var pin: Dictionary = current
		trade.pressed.connect(func():
			host.detail_panel.hide()
			host.town.open_place({"kind": "merchant", "label": str(pin.get("name", "Estabelecimento"))}, pin))
		host.detail_body.add_child(trade)
		return
	if key == "mon-resolve":
		var resolution: Dictionary = payload if payload is Dictionary else {}
		if resolution.get("confirmed") or not resolution.get("resolution_id"):
			busy = false
			host._notice(attack_line(resolution))
			host._poll()
		else:
			host.api.request_json("mon-confirm", "/combat/attacks/" + str(resolution.resolution_id).uri_encode() + "/confirm", HTTPClient.METHOD_POST, {})
		return
	if key == "mon-confirm":
		busy = false
		host._notice(attack_line(payload if payload is Dictionary else {}))
		host.detail_panel.hide()
		host._poll()
		return
	if key == "summon-dismiss":
		host._notice("Invocação dispensada.")
		host._poll()
		return
	if key == "loot-collect":
		busy = false
		var receipt: Dictionary = payload if payload is Dictionary else {}
		var lines: Array = []
		for share in receipt.get("shares", []):
			var items: Array = (share.get("rewards", []) as Array).map(func(r): return "%d× %s" % [int(r.get("quantity", 1)), str(r.get("name", ""))])
			lines.append(str(share.get("name", "")) + ": " + (", ".join(items) if not items.is_empty() else "nada"))
		host._show_detail({"name": "Espólio de " + str(receipt.get("source_name", "")),
			"description": "\n".join(lines) if not lines.is_empty() else "Nada de valor."})
		host._notice("Espólio repartido.")
		host._poll()

func failed(key: String, message: String, code: int) -> bool:
	if key.begins_with("pin-commerce:"): return true  # no shop here: stay quiet
	if key == "summon-dismiss":
		host._notice(message)
		return true
	if key in ["mon-resolve", "mon-confirm"]:
		busy = false
		host._notice(("Sem resposta do servidor; confira o Registro antes de repetir." if host.keeper.network_error(code) else message))
		return true
	if key != "loot-collect": return false
	busy = false
	if host.keeper.network_error(code):
		host._notice("Sem resposta ao saquear. Abra o pin de novo: se o baú sumiu, o saque já foi feito.")
	else:
		host._notice(message)
	return true
