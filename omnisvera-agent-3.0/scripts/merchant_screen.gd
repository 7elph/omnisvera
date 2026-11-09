extends Control
## ROM2-style shop/inn screen. Offers, prices, haggling and receipts come from the
## existing commerce routes; the client only asks for a quote and confirms it.
signal request(key: String, path: String, method: int, payload: Dictionary)
signal closed
const Gothic = preload("res://scripts/gothic_theme.gd")
const ROM = "res://assets/rom2_local/"
var media: Node
var merchants: Array = []
var merchant: Dictionary = {}
var spot: Dictionary = {}
var place: Dictionary = {}
var character_id: String = ""
var character_name: String = ""
var purse_text: String = ""
var selection: Dictionary = {}
var quote: Dictionary = {}
var goods_page: int = 0
var bag_page: int = 0
var canvas = Control.new()
var scene_art = TextureRect.new()
var vitrine = TextureRect.new()
var shelf = TextureRect.new()
var bag = TextureRect.new()
var menu = TextureRect.new()
var item_icon = TextureRect.new()
var item_title = Label.new()
var item_text = Label.new()
var item_price = Label.new()
var action = Button.new()
var haggle = CheckBox.new()
var npc_label = Label.new()
var purse_label = Label.new()
var message = Label.new()
var services_box = VBoxContainer.new()
var goods_slots: Array = []
var bag_slots: Array = []
var confirm = ConfirmationDialog.new()
var goods_prev = Button.new()
var goods_next = Button.new()
var bag_prev = Button.new()
var bag_next = Button.new()
const DESIGN = Vector2(960, 540)
var frames: String = "rom2"
var framed: Array = []   # [TextureRect, rom2 file, fallback panel]

func _ready() -> void:
	z_index = 70
	mouse_filter = Control.MOUSE_FILTER_STOP
	var back = ColorRect.new()
	back.color = Color(0.02, 0.015, 0.01, 0.97)
	back.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(back)
	canvas.size = DESIGN
	canvas.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(canvas)
	_art(scene_art, "shop/shopmain.png", Rect2(8, 8, 288, 288))
	_art(menu, "shop/shopmenu.png", Rect2(8, 300, 288, 232))
	_art(vitrine, "shop/shopframe.png", Rect2(304, 8, 316, 303))
	_art(bag, "shop/shopinv.png", Rect2(628, 8, 164, 303))
	_art(shelf, "shop/shoptable.png", Rect2(304, 318, 488, 90))
	var portrait_box = VBoxContainer.new()
	portrait_box.position = Vector2(800, 8)
	portrait_box.size = Vector2(152, 300)
	canvas.add_child(portrait_box)
	Gothic.title(npc_label, 18)
	npc_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	portrait_box.add_child(npc_label)
	Gothic.shadowed(purse_label)
	purse_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	purse_label.add_theme_font_size_override("font_size", 14)
	portrait_box.add_child(purse_label)
	var leave = Button.new()
	leave.text = "Sair"
	leave.custom_minimum_size = Vector2(0, 42)
	leave.pressed.connect(func():
		hide()
		closed.emit())
	portrait_box.add_child(leave)
	# Vitrine: selected item.
	item_icon.position = Vector2(334, 30)
	item_icon.size = Vector2(110, 110)
	item_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	item_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	item_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(item_icon)
	Gothic.title(item_title, 18)
	item_title.position = Vector2(452, 30)
	item_title.size = Vector2(150, 60)
	item_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	canvas.add_child(item_title)
	Gothic.shadowed(item_price)
	item_price.position = Vector2(452, 96)
	item_price.size = Vector2(150, 44)
	item_price.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	item_price.add_theme_color_override("font_color", Color("#f5d27a"))
	canvas.add_child(item_price)
	item_text.position = Vector2(334, 148)
	item_text.size = Vector2(268, 90)
	item_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	item_text.add_theme_font_size_override("font_size", 13)
	item_text.max_lines_visible = 6
	canvas.add_child(item_text)
	haggle.text = "Barganhar"
	haggle.tooltip_text = "Teste de Carisma resolvido pelo servidor; vale até o próximo descanso"
	haggle.position = Vector2(334, 246)
	canvas.add_child(haggle)
	action.position = Vector2(466, 244)
	action.size = Vector2(136, 40)
	action.pressed.connect(_ask_quote)
	canvas.add_child(action)
	# Shelf (merchant goods) and bag (sellable items).
	for index in range(5):
		var slot = _slot(Vector2(330 + index * 88, 330), Vector2(72, 66))
		slot.pressed.connect(func(): _pick_goods(index))
		goods_slots.append(slot)
	for index in range(6):
		var slot = _slot(Vector2(640 + (index % 2) * 72, 40 + int(index / 2) * 84), Vector2(62, 70))
		slot.pressed.connect(func(): _pick_bag(index))
		bag_slots.append(slot)
	for pair in [[goods_prev, Vector2(304, 412), "<", -1, true], [goods_next, Vector2(744, 412), ">", 1, true], [bag_prev, Vector2(628, 270), "<", -1, false], [bag_next, Vector2(744, 270), ">", 1, false]]:
		var button: Button = pair[0]
		button.text = pair[2]
		button.position = pair[1]
		button.size = Vector2(46, 34)
		var delta: int = pair[3]
		var goods: bool = pair[4]
		button.pressed.connect(func():
			if goods: goods_page = maxi(0, goods_page + delta)
			else: bag_page = maxi(0, bag_page + delta)
			_render())
		canvas.add_child(button)
	services_box.position = Vector2(30, 320)
	services_box.size = Vector2(244, 214)
	services_box.add_theme_constant_override("separation", 5)
	canvas.add_child(services_box)
	Gothic.shadowed(message)
	message.position = Vector2(304, 452)
	message.size = Vector2(648, 80)
	message.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	canvas.add_child(message)
	add_child(confirm)
	confirm.ok_button_text = "Confirmar"
	confirm.cancel_button_text = "Desistir"
	confirm.confirmed.connect(_confirm_quote)
	confirm.canceled.connect(func(): quote = {})
	resized.connect(_fit)

func _art(rect: TextureRect, file: String, area: Rect2) -> void:
	rect.position = area.position
	rect.size = area.size
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_SCALE
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var fill = Panel.new()
	fill.add_theme_stylebox_override("panel", Gothic.panel_box(0.96, 3))
	fill.size = area.size
	fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fill.show_behind_parent = true
	rect.add_child(fill)
	framed.append([rect, file, fill])
	canvas.add_child(rect)
	_apply_frame(framed[-1])

func _apply_frame(entry: Array) -> void:
	var rect: TextureRect = entry[0]
	if str(entry[1]) != "shop/shopmain.png":
		var use_rom2 = frames == "rom2" and ResourceLoader.exists(ROM + str(entry[1]))
		rect.texture = load(ROM + str(entry[1])) if use_rom2 else null
	entry[2].visible = rect.texture == null

## "rom2" = original game frames (local files); "gothic" = drawn panels, shareable.
func set_frames(kind: String) -> void:
	frames = kind
	for entry in framed: _apply_frame(entry)

func _slot(at: Vector2, extent: Vector2) -> Button:
	var slot = Button.new()
	slot.position = at
	slot.size = extent
	slot.flat = true
	slot.expand_icon = true
	slot.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	slot.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
	slot.add_theme_constant_override("icon_max_width", 46)
	slot.add_theme_font_size_override("font_size", 11)
	slot.clip_text = true
	slot.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	canvas.add_child(slot)
	return slot

func _fit() -> void:
	var factor = minf(size.x / DESIGN.x, size.y / DESIGN.y)
	canvas.scale = Vector2.ONE * factor
	canvas.position = (size - DESIGN * factor) / 2

## Open for a pin. Inn mode swaps the art and emphasises services.
func open(target_spot: Dictionary, target_pin: Dictionary, character: String, display_name: String, purse: String) -> void:
	spot = target_spot
	place = target_pin
	character_id = character
	character_name = display_name
	purse_text = purse
	merchants.clear()
	merchant = {}
	selection = {}
	quote = {}
	goods_page = 0
	bag_page = 0
	var inn = str(spot.get("kind", "")) == "tavern"
	var art_path = str(spot.get("art", ""))
	if art_path != "" and ResourceLoader.exists(art_path):
		scene_art.texture = load(art_path)
	elif frames == "rom2" and ResourceLoader.exists(ROM + "shop/shopmain.png"):
		scene_art.texture = load(ROM + "shop/shopmain.png")
	else:
		scene_art.texture = null
	for entry in framed: _apply_frame(entry)
	npc_label.text = str(spot.get("label", place.get("name", "Estabelecimento")))
	message.text = "Consultando o estabelecimento…" if not place.is_empty() else "Local sem marcador no mapa da cidade."
	shelf.visible = not inn
	for slot in goods_slots: slot.visible = not inn
	goods_prev.visible = not inn
	goods_next.visible = not inn
	show()
	_fit()
	_render()
	if not place.is_empty():
		var query = "?character_id=" + character.uri_encode() if character != "" else ""
		request.emit("shop-offers", "/workspace/tokens/" + str(place.id).uri_encode() + "/commerce" + query, HTTPClient.METHOD_GET, {})

func received(key: String, data: Variant) -> void:
	match key:
		"shop-offers":
			merchants = data if data is Array else []
			merchant = merchants[0] if not merchants.is_empty() else {}
			if merchant.is_empty():
				var description = str(place.get("sheet", {}).get("description", place.get("description", "")))
				message.text = (description + "\n" if description != "" else "") + "Ninguém atende aqui agora. O estabelecimento precisa estar aberto pelo Mestre."
			else:
				var npc: Dictionary = merchant.get("responsible_npc", {})
				npc_label.text = str(merchant.get("name", "")) + ("\n" + str(npc.name) if npc.get("name") else "")
				if not message.text.begins_with("Feito:"):
					message.text = str(npc.get("public_description", ""))
				if npc.get("portrait_path") and media and str(spot.get("art", "")) == "":
					pass  # Keep the shop scene; the NPC portrait belongs to the sheet.
			_render()
		"shop-quote":
			quote = data if data is Dictionary else {}
			if quote.is_empty(): return
			var verb = {"buy": "Comprar", "sell": "Vender", "service": "Contratar"}.get(str(quote.get("kind", "")), "Confirmar")
			var bargain: Dictionary = quote.get("bargain", {}) if quote.get("bargain") is Dictionary else {}
			var extra = ""
			if not bargain.is_empty():
				extra = "\nBarganha: d20 %d %+d = %d (%s)" % [int(bargain.get("d20", 0)), int(bargain.get("modifier", 0)), int(bargain.get("total", 0)), str(bargain.get("label", ""))]
			confirm.dialog_text = "%s %d× %s por %s?%s\nA oferta vale 10 minutos." % [verb, int(quote.get("quantity", 1)), str(quote.get("name", "")), money(int(quote.get("total_copper", 0))), extra]
			confirm.popup_centered(Vector2i(380, 190))
		"shop-confirm":
			quote = {}
			var receipt: Dictionary = data if data is Dictionary else {}
			purse_text = "Bolsa: " + money(int(receipt.get("balance_after_copper", 0)))
			message.text = "Feito: " + {"buy": "Comprado", "sell": "Vendido", "service": "Contratado"}.get(str(receipt.get("kind", "")), "Feito") + ": " + str(receipt.get("name", "")) + " · " + money(int(receipt.get("total_copper", 0)))
			if receipt.get("service_status") == "reserved":
				message.text += " · reservado para o próximo descanso concedido pelo Mestre"
			selection = {}
			open_refresh()

func failed(key: String, text: String) -> void:
	if key.begins_with("shop-"):
		message.text = text
		quote = {}

func open_refresh() -> void:
	if not place.is_empty():
		request.emit("shop-offers", "/workspace/tokens/" + str(place.id).uri_encode() + "/commerce?character_id=" + character_id.uri_encode(), HTTPClient.METHOD_GET, {})

static func money(copper: int) -> String:
	var gold = copper / 100
	var silver = (copper % 100) / 10
	var rest = copper % 10
	var parts = PackedStringArray()
	if gold: parts.append(str(gold) + " PO")
	if silver: parts.append(str(silver) + " PP")
	if rest or parts.is_empty(): parts.append(str(rest) + " PC")
	return " ".join(parts)

func _render() -> void:
	purse_label.text = character_name + "\n" + purse_text
	var offers: Array = merchant.get("offers", [])
	var owned: Array = merchant.get("sellable", [])
	goods_page = clampi(goods_page, 0, maxi(0, (offers.size() - 1) / 5))
	bag_page = clampi(bag_page, 0, maxi(0, (owned.size() - 1) / 6))
	_fill(goods_slots, offers.slice(goods_page * 5, goods_page * 5 + 5))
	_fill(bag_slots, owned.slice(bag_page * 6, bag_page * 6 + 6))
	goods_prev.disabled = goods_page == 0
	goods_next.disabled = (goods_page + 1) * 5 >= offers.size()
	bag_prev.disabled = bag_page == 0
	bag_next.disabled = (bag_page + 1) * 6 >= owned.size()
	for child in services_box.get_children():
		services_box.remove_child(child)
		child.queue_free()
	var services: Array = merchant.get("services", [])
	for service in services.slice(0, 4):
		var button = Button.new()
		button.flat = true
		button.add_theme_color_override("font_color", Color("#f3dfb0"))
		button.add_theme_font_size_override("font_size", 13)
		button.text = str(service.get("name", "")) + " · " + money(int(service.get("price_copper", 0)))
		button.clip_text = true
		button.custom_minimum_size = Vector2(0, 41)
		button.tooltip_text = str(service.get("unavailable_reason", button.text))
		button.disabled = service.get("available", true) == false
		button.pressed.connect(func(): _select({"kind": "service", "id": str(service.id), "name": str(service.get("name", "")), "price_copper": int(service.get("price_copper", 0)), "description": _service_text(service)}))
		services_box.add_child(button)
	if selection.is_empty():
		item_icon.texture = null
		item_title.text = "Escolha um item"
		item_price.text = ""
		var inn = str(spot.get("kind", "")) == "tavern"
		item_text.text = ("Serviços à esquerda. Bolsa à direita: o que você pode vender." if inn else "Prateleira: mercadorias do estabelecimento. Bolsa à direita: o que você pode vender.") if not merchant.is_empty() else ""
		action.disabled = true
		action.text = "—"
		haggle.visible = false
	else:
		item_title.text = str(selection.get("name", ""))
		item_price.text = money(int(selection.get("price_copper", 0))) + (" cada" if selection.kind != "service" else "")
		item_text.text = str(selection.get("description", ""))
		action.text = {"buy": "Comprar", "sell": "Vender", "service": "Contratar"}[selection.kind]
		action.disabled = character_id == "" or not quote.is_empty()
		haggle.visible = selection.kind == "buy"
		item_icon.texture = load("res://assets/ui/items.svg")
		if media and selection.get("image_path"):
			media.bind(selection.image_path, item_icon, "texture", 128)

func _service_text(service: Dictionary) -> String:
	var kinds = {"lodging": "Hospedagem: aplicada no próximo descanso concedido pelo Mestre.", "spell": "Magia conjurada pelo estabelecimento.", "appraisal": "Avaliação do que você carrega.", "repair": "Reparo de encantamento corroído.", "delivery": "Entrega de item."}
	return kinds.get(str(service.get("kind", "")), "") + ("\n" + str(service.unavailable_reason) if service.get("unavailable_reason") else "")

func _fill(slots: Array, entries: Array) -> void:
	for index in range(slots.size()):
		var slot: Button = slots[index]
		if index < entries.size():
			var entry: Dictionary = entries[index]
			slot.disabled = false
			slot.text = "\n\n\n" + str(entry.get("name", "")).substr(0, 12)
			slot.tooltip_text = str(entry.get("name", "")) + " · " + money(int(entry.get("price_copper", 0))) + (" · estoque " + str(entry.quantity) if entry.get("quantity") != null and int(entry.quantity) >= 0 else "")
			slot.icon = load("res://assets/ui/items.svg")
			slot.set_meta("entry", entry)
			if media and entry.get("image_path"):
				media.bind(entry.image_path, slot, "icon", 128)
		else:
			slot.disabled = true
			slot.text = ""
			slot.icon = null
			slot.tooltip_text = ""
			slot.set_meta("entry", {})

func _pick_goods(index: int) -> void:
	var entry: Dictionary = goods_slots[index].get_meta("entry", {})
	if not entry.is_empty(): _select({"kind": "buy", "id": str(entry.id), "name": str(entry.get("name", "")), "price_copper": int(entry.get("price_copper", 0)), "image_path": entry.get("image_path"), "description": str(entry.get("description", ""))})

func _pick_bag(index: int) -> void:
	var entry: Dictionary = bag_slots[index].get_meta("entry", {})
	if not entry.is_empty(): _select({"kind": "sell", "id": str(entry.id), "name": str(entry.get("name", "")), "price_copper": int(entry.get("price_copper", 0)), "image_path": entry.get("image_path"), "description": "Você tem " + str(entry.get("quantity", 1)) + ". O mercador paga este valor por unidade."})

func _select(entry: Dictionary) -> void:
	selection = entry
	quote = {}
	_render()

func _ask_quote() -> void:
	if selection.is_empty() or merchant.is_empty() or character_id == "": return
	var payload = {"request_id": "godot-quote-" + Crypto.new().generate_random_bytes(10).hex_encode(), "character_id": character_id,
		"kind": selection.kind, "target_id": selection.id, "quantity": 1, "negotiate": haggle.button_pressed and selection.kind == "buy"}
	request.emit("shop-quote", "/commerce/" + str(merchant.id).uri_encode() + "/quotes", HTTPClient.METHOD_POST, payload)

func _confirm_quote() -> void:
	if quote.is_empty(): return
	request.emit("shop-confirm", "/commerce/quotes/" + str(quote.id).uri_encode() + "/confirm", HTTPClient.METHOD_POST, {"request_id": "godot-buy-" + Crypto.new().generate_random_bytes(10).hex_encode()})
