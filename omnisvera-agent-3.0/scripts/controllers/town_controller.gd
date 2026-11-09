extends Node
## City screen, shops/inns and GM travel between the city and its surroundings.
const CITY_CONFIG = "res://assets/city/nimalis.json"
var host: Node
var config: Dictionary = {}
var snapshot: Dictionary = {}
var city_screen = preload("res://scripts/city_screen.gd").new()
var shop = preload("res://scripts/merchant_screen.gd").new()
var confirm_travel = ConfirmationDialog.new()
var travel_target: String = ""
var variant: String = ""
const PREFS = "user://companion_v3.cfg"

func setup(main: Node) -> void:
	host = main
	if FileAccess.file_exists(CITY_CONFIG):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(CITY_CONFIG))
		if parsed is Dictionary: config = parsed
	city_screen.media = host.media
	city_screen.hide()
	host.screen.add_child(city_screen)
	var prefs = ConfigFile.new()
	prefs.load(PREFS)
	variant = str(prefs.get_value("town", "variant", config.get("variant", "original")))
	apply_variant(variant)
	city_screen.variant_requested.connect(func():
		var options: Array = config.get("variants", {}).keys()
		if options.size() < 2: return
		apply_variant(options[(options.find(variant) + 1) % options.size()])
		var store = ConfigFile.new()
		store.load(PREFS)
		store.set_value("town", "variant", variant)
		store.save(PREFS))
	city_screen.place_opened.connect(open_place)
	city_screen.enter_requested.connect(func(): ask_travel(str(config.get("map_id", "")), "Levar o grupo a " + str(config.get("title", "cidade")) + "? O mapa ativo da mesa muda para todos."))
	city_screen.exit_requested.connect(func(): ask_travel(str(config.get("exit_map_id", "")), "Sair para " + str(config.get("exit_title", "os Arredores")) + "? O mapa ativo da mesa muda para todos."))
	city_screen.closed.connect(func(): host.hud.refresh_visibility())
	shop.media = host.media
	shop.hide()
	host.screen.add_child(shop)
	shop.request.connect(func(key, path, method, payload): host.api.request_json(key, path, method, payload))
	shop.closed.connect(func(): host.hud.load_sheet())
	host.screen.add_child(confirm_travel)
	confirm_travel.title = "Viagem"
	confirm_travel.ok_button_text = "Ir"
	confirm_travel.cancel_button_text = "Cancelar"
	confirm_travel.confirmed.connect(func():
		if host.master and travel_target != "":
			host.api.request_json("active-map", "/gm/workspace/maps/active", HTTPClient.METHOD_PATCH, {"map_id": travel_target}))

## Art set: "original" (Flux, shareable) or "rom2" (local game files, private use).
func apply_variant(name: String) -> void:
	var variants: Dictionary = config.get("variants", {})
	var chosen: Dictionary = variants.get(name, {})
	var background = str(chosen.get("background", ""))
	if chosen.is_empty() or (background != "" and not ResourceLoader.exists(background)):
		for other in variants:
			var candidate: Dictionary = variants[other]
			if ResourceLoader.exists(str(candidate.get("background", ""))):
				name = other
				chosen = candidate
				break
	variant = name
	var merged = config.duplicate(true)
	merged.merge(chosen, true)
	merged.erase("variants")
	city_screen.configure(merged)
	city_screen.variant_label(variant, variants.size() > 1)
	shop.set_frames(str(chosen.get("frames", "rom2")))

func city_map_id() -> String:
	return str(config.get("map_id", ""))

func screen_visible() -> bool:
	return city_screen.visible or shop.visible

func handles(key: String) -> bool:
	return key.begins_with("shop-") or key in ["city", "active-map"]

func received(key: String, data: Variant) -> void:
	if key.begins_with("shop-"):
		shop.received(key, data)
		if key == "shop-confirm": host.hud.load_sheet()
	elif key == "city":
		snapshot = data if data is Dictionary else {}
		present()
	elif key == "active-map":
		host.command_inflight = false
		city_screen.hide()
		host._poll()

func failed(key: String, message: String, _code: int) -> bool:
	if key.begins_with("shop-"):
		shop.failed(key, message)
		return true
	if key == "city": return true
	if key == "active-map":
		host.command_inflight = false
		host.pending_intent.clear()
	return false

## Exploration snapshot: the city opens for everyone when it is the table's active map.
func after_exploration(data: Dictionary) -> void:
	if not config.is_empty() and str(data.get("map", {}).get("id", "")) == city_map_id():
		snapshot = data
		if not shop.visible: present()
	elif city_screen.visible and city_screen.active_on_table:
		city_screen.hide()

func open_city() -> void:
	if config.is_empty(): return
	host.panel.hide()
	host.active_panel = ""
	if str(host.workspace.get("map", {}).get("id", "")) == city_map_id():
		snapshot = host.workspace
		present()
	else:
		host.api.request_json("city", "/workspace?map_id=" + city_map_id().uri_encode())

func present() -> void:
	var on_table = str(host.workspace.get("map", {}).get("id", "")) == city_map_id()
	city_screen.present(snapshot, host.master, on_table)
	if host.battle.confirm_encounter.visible:
		host.battle.confirm_encounter.hide()
		host.battle.encounter_offer = {}
	host.hud.refresh_visibility()

func ask_travel(map_id: String, text: String) -> void:
	if not host.master or map_id == "": return
	travel_target = map_id
	confirm_travel.dialog_text = text
	confirm_travel.popup_centered(Vector2i(380, 160))

func open_place(spot: Dictionary, pin: Dictionary) -> void:
	if str(spot.get("kind", "")) in ["merchant", "tavern"]:
		var id = host.hud.controlled_id()
		var name = ""
		for character in host.characters:
			if str(character.id) == id: name = str(character.name)
		var purse = host.hud.purse_label(host.hud.state()) if not host.hud.state().is_empty() else ""
		shop.open(spot, pin, id, name if name != "" else "Sem personagem", purse)
	else:
		var info: Dictionary = pin.get("sheet", {}).duplicate(true) if pin.get("sheet") is Dictionary else {}
		info.name = pin.get("name", spot.get("label", "Local"))
		info.image_path = pin.get("image_path")
		host._show_detail(info)

func clear() -> void:
	city_screen.hide()
	shop.hide()
	snapshot = {}
