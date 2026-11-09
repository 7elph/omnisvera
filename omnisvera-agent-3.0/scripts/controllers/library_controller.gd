extends Node
## Biblioteca do Mestre: bestiário, NPCs, itens da campanha, compêndio, grimório e mapas.
## Tudo vem do backend; colocar no mapa cria o pin oculto (o Mestre revela depois).
## Com uma cena aberta em "Cenas", cada entrada também pode ser preparada nela.

const Style = preload("res://scripts/ui_style.gd")
const TABS = [["monsters", "Monstros"], ["npcs", "NPCs"], ["items", "Itens"], ["compendium", "Compêndio"],
	["spells", "Magias"], ["maps", "Mapas"]]
const SOURCES = {"monsters": "/gm/workspace/monster-catalog", "npcs": "/npcs", "items": "/gm/workspace/items",
	"compendium": "/gm/compendium/items", "spells": "/gm/compendium/spells"}
const LIMIT = 30

var host: Node
var tab: String = "monsters"
var query: String = ""
var data: Dictionary = {}          # tab -> Array of records
var loading: Dictionary = {}
var expanded: String = ""          # record key with details open
var placed: int = 0                # spreads consecutive pins around the party
var list_box: VBoxContainer
var grant_target: String = ""
var busy: bool = false
var pending_cast: Dictionary = {}  # scene participant waiting for its catalog to load

func setup(main: Node) -> void:
	host = main

func handles(key: String) -> bool:
	return key.begins_with("lib-")

func clear() -> void:
	data.clear()
	loading.clear()
	expanded = ""
	busy = false

func open(start_tab: String = "") -> void:
	if start_tab != "": tab = start_tab
	_load(tab)

func _load(name: String) -> void:
	if name == "maps" or data.has(name) or loading.get(name, false): return
	loading[name] = true
	host.api.request_json("lib-data:" + name, SOURCES[name])

func received(key: String, payload: Variant) -> void:
	if key.begins_with("lib-data:"):
		var name = key.get_slice(":", 1)
		loading.erase(name)
		var records: Array = []
		if payload is Array: records = payload
		elif payload is Dictionary:
			for field in ["monsters", "items", "spells", "npcs"]:
				if payload.get(field) is Array: records = payload[field]; break
		data[name] = records
		if not pending_cast.is_empty() and name in ["monsters", "npcs"]:
			var cast = pending_cast
			pending_cast = {}
			place_participant(cast)
		_refresh()
		return
	busy = false
	match key:
		"lib-place":
			host._notice("Colocado no mapa, oculto. Revele pelo pin quando quiser.")
			host._poll()
		"lib-grant":
			host._notice("Item entregue.")
		"lib-scene":
			host._notice("Preparado na cena.")
			if payload is Dictionary and payload.get("id") and int(payload.id) == int(host.preparation.scene.get("id", -1)):
				host.preparation.scene = payload
		"lib-map":
			host._notice("Mapa aberto na mesa.")
	_refresh()

func failed(key: String, message: String, code: int) -> bool:
	if not handles(key): return false
	busy = false
	if key.begins_with("lib-data:"):
		loading.erase(key.get_slice(":", 1))
		data[key.get_slice(":", 1)] = []
		host._notice("Biblioteca: " + message)
	elif host.keeper.network_error(code):
		host._notice("Sem resposta do servidor. Confira o mapa antes de repetir (pode ter sido criado).")
	else:
		host._notice(message)
	_refresh()
	return true

# --- Painel --------------------------------------------------------------------
func render(body: Node) -> void:
	var scene: Dictionary = host.preparation.scene
	if not scene.is_empty():
		Style.label(body, "Preparando: " + str(scene.get("title", "Cena")), 14)
	var tabs = GridContainer.new()
	tabs.columns = 3
	body.add_child(tabs)
	for entry in TABS:
		var button = Button.new()
		button.text = entry[1]
		button.toggle_mode = true
		button.button_pressed = tab == entry[0]
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var name: String = entry[0]
		button.pressed.connect(func(): tab = name; expanded = ""; _load(name); host._render_panel())
		tabs.add_child(button)
	var search = LineEdit.new()
	search.placeholder_text = "Buscar por nome, tipo ou categoria"
	search.text = query
	search.clear_button_enabled = true
	search.text_changed.connect(func(text): query = text; _fill_list())
	body.add_child(search)
	if tab == "items":
		var row = HBoxContainer.new()
		body.add_child(row)
		Style.label(row, "Entregar a:", 14).autowrap_mode = TextServer.AUTOWRAP_OFF
		var who = OptionButton.new()
		who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		for character in host.characters:
			who.add_item(str(character.get("name", "")))
			who.set_item_metadata(who.item_count - 1, str(character.get("id", "")))
			if grant_target == "" or grant_target == str(character.get("id", "")):
				grant_target = str(character.get("id", ""))
				who.select(who.item_count - 1)
		who.item_selected.connect(func(index): grant_target = str(who.get_item_metadata(index)))
		row.add_child(who)
	list_box = VBoxContainer.new()
	list_box.add_theme_constant_override("separation", 6)
	body.add_child(list_box)
	_load(tab)
	_fill_list()

func _refresh() -> void:
	if host.panel.visible and host.active_panel == "library":
		_fill_list()

func _records() -> Array:
	if tab == "maps": return host.maps
	return data.get(tab, [])

func _fill_list() -> void:
	if list_box == null or not is_instance_valid(list_box): return
	for child in list_box.get_children():
		list_box.remove_child(child)
		child.queue_free()
	if tab != "maps" and not data.has(tab):
		Style.label(list_box, "Carregando…")
		return
	var needle = query.strip_edges().to_lower()
	var shown = 0
	var total = 0
	for record in _records():
		if not record is Dictionary: continue
		if needle != "" and not needle in _haystack(record): continue
		total += 1
		if shown >= LIMIT: continue
		shown += 1
		_row(record)
	if total == 0:
		Style.label(list_box, "Nada encontrado.")
	elif total > shown:
		Style.label(list_box, "Mostrando %d de %d. Refine a busca." % [shown, total], 13)

func _haystack(record: Dictionary) -> String:
	var parts = []
	for field in ["name", "title", "category", "class_or_role", "race", "school", "item_type", "habitat", "current_location"]:
		if record.get(field) != null: parts.append(str(record[field]))
	return " ".join(parts).to_lower()

## JSON numbers arrive as float: 2.0 -> "2".
static func _id(value: Variant) -> String:
	if value is float and value == floor(value): return str(int(value))
	return str(value if value != null else "")

static func _n(value: Variant) -> String:
	return _id(value)

func _key(record: Dictionary) -> String:
	return tab + ":" + str(record.get("id", record.get("name", "")))

func _row(record: Dictionary) -> void:
	var box = VBoxContainer.new()
	list_box.add_child(box)
	var row = HBoxContainer.new()
	box.add_child(row)
	var art = record.get("image_path", record.get("portrait_path"))
	if art: host.content.image(row, art, 40, "sheet")
	var name = Button.new()
	name.text = _title(record)
	name.flat = true
	name.alignment = HORIZONTAL_ALIGNMENT_LEFT
	name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name.clip_text = true
	name.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	var key = _key(record)
	name.pressed.connect(func(): expanded = "" if expanded == key else key; _fill_list())
	row.add_child(name)
	for action in _actions(record):
		var button = Button.new()
		button.text = action[0]
		button.disabled = busy
		button.pressed.connect(action[1])
		row.add_child(button)
	if expanded == key:
		Style.label(box, _details(record), 13)

func _title(record: Dictionary) -> String:
	match tab:
		"monsters": return "%s · PV %s · CA %s" % [record.get("name", ""), _n(record.get("average_hp", record.get("hit_points", "?"))), _n(record.get("armor_class", "?"))]
		"npcs": return str(record.get("name", "")) + (" · " + str(record.class_or_role) if record.get("class_or_role") else "")
		"items": return str(record.get("name", "")) + (" · " + str(record.item_type) if record.get("item_type") else "")
		"compendium": return "%s · %s" % [record.get("name", ""), record.get("preco", "")]
		"spells": return "%s · %s %dº" % [record.get("name", ""), str(record.get("tradition", "")).capitalize(), int(record.get("circle", 0))]
		"maps": return str(record.get("title", record.get("id", "")))
	return str(record.get("name", ""))

func _details(record: Dictionary) -> String:
	match tab:
		"monsters":
			var attacks = (record.get("attacks", []) as Array).map(func(a): return str(a.get("raw", a.get("name", ""))))
			var abilities = (record.get("abilities", []) as Array).map(func(a): return str(a.get("name", "")) + ": " + str(a.get("description", "")))
			return "%s · %s · %s\nDV %s · JP %s · MO %s · MV %s · XP %s\nAtaques: %s\n%s\n%s" % [record.get("category", ""), record.get("size", ""),
				record.get("alignment", ""), record.get("hit_dice", "—"), _n(record.get("saving_throw", "—")), _n(record.get("morale", "—")),
				record.get("movement", "—"), _n(record.get("experience_points", "—")), ", ".join(attacks), "\n".join(abilities), record.get("description", "")]
		"npcs":
			return "%s\nPúblico: %s\nMestre: %s\nLocal: %s" % [record.get("race", ""), record.get("public_description", "—"),
				record.get("private_description", "—"), record.get("current_location", "—")]
		"items": return str(record.get("description", ""))
		"compendium": return "%s\n%s · %s%s" % [record.get("description", ""), record.get("peso", ""), record.get("preco", ""),
			(" · dano " + str(record.dano)) if record.get("dano") else ""]
		"spells": return "Alcance %s · Duração %s · Proteção %s\n%s" % [record.get("alcance", "—"), record.get("duracao", "—"),
			record.get("jogada_protecao", "—"), record.get("description", "")]
		"maps": return "Visível aos jogadores" if record.get("visible_to_players") else "Oculto dos jogadores"
	return ""

func _actions(record: Dictionary) -> Array:
	var list: Array = []
	var scene: Dictionary = host.preparation.scene
	match tab:
		"monsters":
			list.append(["No mapa", func(): place_monster(record)])
			if not scene.is_empty(): list.append(["Na cena", func(): add_to_scene("creature", record)])
		"npcs":
			list.append(["No mapa", func(): place_npc(record)])
			if not scene.is_empty(): list.append(["Na cena", func(): add_to_scene("npc", record)])
		"items":
			list.append(["Entregar", func(): grant(record)])
			if not scene.is_empty(): list.append(["Na cena", func(): add_item_to_scene(record)])
		"maps":
			if str(record.get("id", "")) != str(host.workspace.get("map", {}).get("id", "")):
				list.append(["Abrir na mesa", func(): open_map(record)])
	return list

# --- Ações ---------------------------------------------------------------------
func _spot() -> Dictionary:
	## Next free-ish cell beside the party on the active map, in the backend's 0..100 coordinates.
	var map: Dictionary = host.workspace.get("map", {}) if host.workspace.get("map") is Dictionary else {}
	var geometry: Dictionary = map.get("grid", {}) if map.get("grid") is Dictionary else {}
	var cols = maxi(1, int(geometry.get("cols", 20)))
	var rows = maxi(1, int(geometry.get("rows", 20)))
	var origin = Vector2(float(geometry.get("origin_x", 0)), float(geometry.get("origin_y", 0)))
	var cell_w = (100.0 - origin.x) / cols
	var cell_h = (100.0 - origin.y) / rows
	var anchor = Vector2i(cols / 2, rows / 2)
	for token in host.workspace.get("tokens", []):
		if token is Dictionary and token.get("token_type") == "character" and token.get("latitude") != null:
			anchor = Vector2i(int((float(token.longitude) - origin.x) / cell_w), int((float(token.latitude) - origin.y) / cell_h))
			break
	var offsets = [Vector2i(3, 0), Vector2i(3, 1), Vector2i(3, -1), Vector2i(4, 0), Vector2i(4, 1), Vector2i(4, -1), Vector2i(-3, 0), Vector2i(-3, 1)]
	var cell = anchor + offsets[placed % offsets.size()] + Vector2i(0, 2 * (placed / offsets.size()))
	placed += 1
	cell = Vector2i(clampi(cell.x, 0, cols - 1), clampi(cell.y, 0, rows - 1))
	return {"latitude": clampf(origin.y + (cell.y + 0.5) * cell_h, 0, 100), "longitude": clampf(origin.x + (cell.x + 0.5) * cell_w, 0, 100),
		"map_id": str(map.get("id", "default"))}

func _post(key: String, path: String, body: Dictionary) -> void:
	if busy: return
	busy = true
	host.api.request_json(key, path, HTTPClient.METHOD_POST, body)
	_fill_list()

static func monster_token(monster: Dictionary, spot: Dictionary) -> Dictionary:
	var hp = int(monster.get("average_hp", 0))
	if hp <= 0:
		var found = RegEx.create_from_string("\\d+").search(str(monster.get("hit_points", "")))
		hp = int(found.get_string()) if found else 10
	var level_match = RegEx.create_from_string("\\d+").search(str(monster.get("hit_dice", "")))
	var attacks: Array = []
	for attack in monster.get("attacks", []):
		attacks.append({"name": str(attack.get("name", "Ataque")), "damage": str(attack.get("damage", "")),
			"bonus": attack.get("bonus", ""), "notes": ("%d× · %s" % [int(attack.count), attack.get("raw", "")]) if attack.get("count") else str(attack.get("raw", ""))})
	var sheet = {"marker": "⚔", "role": str(monster.get("category", "Inimigo")), "level": int(level_match.get_string()) if level_match else 1,
		"armor_class": int(monster.get("armor_class", 10)), "initiative": 0, "attacks": attacks,
		"abilities": (monster.get("abilities", []) as Array).map(func(a): return str(a.get("name", "")) + ": " + str(a.get("description", "")).left(400)),
		"description": str(monster.get("description", "")).left(600),
		"source": {"catalog_id": "old-dragon-2-srd", "monster_id": str(monster.get("id", "")), "url": str(monster.get("source_url", "")), "license": "CC BY-SA 4.0"}}
	for field in ["hit_dice", "hit_points", "saving_throw", "morale", "experience_points", "treasure", "movement", "category", "size", "alignment", "habitat"]:
		if monster.get(field) != null and str(monster.get(field)) != "": sheet[field] = monster[field]
	var body = {"token_type": "monster", "name": str(monster.get("name", "Criatura")).left(120), "color": "#a33a2a",
		"visible_to_players": false, "maximum_hp": maxi(1, hp), "current_hp": maxi(1, hp), "sheet": sheet}
	if monster.get("image_path"): body.image_path = str(monster.image_path)
	body.merge(spot)
	return body

func place_monster(monster: Dictionary) -> void:
	if not host.master: return
	_post("lib-place", "/gm/workspace/tokens", monster_token(monster, _spot()))

func place_npc(npc: Dictionary) -> void:
	if not host.master: return
	var body = {"token_type": "monster", "name": str(npc.get("name", "NPC")).left(120), "color": "#3f7d6b", "visible_to_players": false,
		"maximum_hp": 10, "current_hp": 10, "sheet": {"marker": "☺", "role": str(npc.get("class_or_role", "NPC")), "disposition": "neutral",
		"npc_id": npc.get("id"), "description": str(npc.get("public_description", "")).left(600), "notes": str(npc.get("private_description", "")).left(600)}}
	if npc.get("portrait_path"): body.image_path = str(npc.portrait_path)
	body.merge(_spot())
	_post("lib-place", "/gm/workspace/tokens", body)

func grant(item: Dictionary) -> void:
	if not host.master or grant_target == "" or item.get("id") == null: return
	_post("lib-grant", "/gm/workspace/items/grant", {"character_id": grant_target, "item_id": int(item.id), "quantity": 1})

func add_to_scene(kind: String, record: Dictionary) -> void:
	var scene: Dictionary = host.preparation.scene
	if scene.is_empty(): return
	var source = ("bestiary:" if kind == "creature" else "npc:") + _id(record.get("id"))
	_post("lib-scene", "/gm/scenes/%d/participants" % int(scene.id), {"participant_type": kind, "npc_name": str(record.get("name", "")).left(180),
		"npc_source": source, "public_label": str(record.get("name", "")).left(180), "visible_to_players": false})

func add_item_to_scene(item: Dictionary) -> void:
	var scene: Dictionary = host.preparation.scene
	if scene.is_empty(): return
	_post("lib-scene", "/gm/scenes/%d/elements" % int(scene.id), {"request_id": "lib-item-" + Crypto.new().generate_random_bytes(8).hex_encode(),
		"element_type": "object", "title": str(item.get("name", "Item")).left(180), "public_description": str(item.get("description", "")).left(2000),
		"private_description": "item:" + _id(item.get("id")), "status": "hidden", "visibility": "gm"})

func open_map(record: Dictionary) -> void:
	host.town.ask_travel(str(record.get("id", "")), "Abrir \"%s\" na mesa para todos?" % str(record.get("title", "mapa")))

## Scene cast: a participant prepared from the library goes to the map in one tap.
func place_participant(participant: Dictionary) -> void:
	var source = str(participant.get("npc_source", ""))
	var id = source.get_slice(":", 1)
	if source.begins_with("bestiary:"):
		for monster in data.get("monsters", []):
			if _id(monster.get("id")) == id: place_monster(monster); return
		if data.has("monsters"):
			host._notice("Criatura não encontrada no bestiário.")
			return
		pending_cast = participant
		_load("monsters")
		host._notice("Carregando o bestiário…")
	elif source.begins_with("npc:"):
		for npc in data.get("npcs", []):
			if _id(npc.get("id")) == id: place_npc(npc); return
		if data.has("npcs"):
			host._notice("NPC não encontrado.")
			return
		pending_cast = participant
		_load("npcs")
		host._notice("Carregando NPCs…")
	else:
		place_npc({"name": participant.get("npc_name", participant.get("public_label", "NPC")), "class_or_role": "NPC"})

func grant_scene_item(element: Dictionary) -> void:
	var text = str(element.get("private_description", ""))
	if grant_target == "" and not host.characters.is_empty(): grant_target = str(host.characters[0].get("id", ""))
	if not text.begins_with("item:") or grant_target == "":
		host._notice("Escolha quem recebe na aba Itens da Biblioteca.")
		return
	_post("lib-grant", "/gm/workspace/items/grant", {"character_id": grant_target, "item_id": int(float(text.get_slice(":", 1))), "quantity": 1})
