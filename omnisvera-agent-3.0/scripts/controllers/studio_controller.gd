extends Node
## Preparar sessão: escolhe a sessão, escreve (ou pede à IA) o roteiro inteiro e os rascunhos dela.
## Estúdio com IA: o Mestre pede em texto, a IA local gera um rascunho no servidor
## (validado lá) e o Mestre decide onde ele entra: pin oculto no mapa, item da campanha ou mapa novo.
## Nada vai para a mesa sem um toque do Mestre.

const Style = preload("res://scripts/ui_style.gd")
const KINDS = [["monster", "Monstro"], ["npc", "NPC (ficha completa)"], ["item", "Item"], ["map", "Mapa (com imagem)"]]
const LABELS = {"monster": "Monstro", "npc": "NPC", "item": "Item", "map": "Mapa"}

var host: Node
var drafts: Array = []
var kind: String = "monster"
var prompt: String = ""
var busy: bool = false
var loaded: bool = false
var context: Dictionary = {}
var context_open: bool = false
var context_draft: String = ""
var pending_generate: Dictionary = {}   # keeps the request id if the network drops mid-request
var expanded: Dictionary = {}
var sessions: Array = []
var session_id: int = 0            # 0 = rascunhos soltos (sem sessão)
var outline_draft: String = ""
var outline_dirty: bool = false
var record_draft: Dictionary = {}  # public_summary / gm_summary being edited for a played session
var brief: String = ""
var pending_plan: Dictionary = {}
var creating_session: bool = false
var session_picked: bool = false

func setup(main: Node) -> void:
	host = main

func handles(key: String) -> bool:
	return key.begins_with("studio-")

func clear() -> void:
	drafts.clear()
	loaded = false
	busy = false
	context = {}
	pending_generate = {}

func open() -> void:
	host.api.request_json("studio-sessions", "/gm/prep/sessions")
	_load_drafts()

func _load_drafts() -> void:
	host.api.request_json("studio-drafts", "/gm/prep/drafts" + ("?session_id=%d" % session_id if session_id > 0 else ""))

func _session() -> Dictionary:
	for record in sessions:
		if int(record.get("id", -1)) == session_id: return record
	return {}

func _plan() -> Dictionary:
	var plan = _session().get("plan", {})
	return plan if plan is Dictionary else {}

## Table poll: only while something is being generated and the panel is open.
func poll() -> void:
	if not host.master or not _visible(): return
	if str(_plan().get("status", "")) in ["planning", "generating"]:
		host.api.request_json("studio-sessions", "/gm/prep/sessions")
		_load_drafts()
	elif drafts.any(func(d): return d.get("status") == "generating"):
		_load_drafts()

func _visible() -> bool:
	return host.panel.visible and host.active_panel == "scenes"

func _refresh() -> void:
	if _visible(): host._render_panel()

# --- Comandos ------------------------------------------------------------------
func generate() -> void:
	var text = prompt.strip_edges()
	if busy or text.length() < 3:
		host._notice("Descreva o que você quer (ex.: \"uma bruxa do pântano para nível 3\").")
		return
	var key = kind + "|" + text
	if pending_generate.get("key") != key:
		pending_generate = {"key": key, "id": "prep-" + Crypto.new().generate_random_bytes(10).hex_encode()}
	busy = true
	host.api.request_json("studio-generate", "/gm/prep/generate", HTTPClient.METHOD_POST,
		{"request_id": pending_generate.id, "kind": kind, "prompt": text.left(1200), "session_id": session_id if session_id > 0 else null})
	_refresh()

func discard(draft: Dictionary) -> void:
	host.api.request_json("studio-discard", "/gm/prep/drafts/%d/discard" % int(draft.id), HTTPClient.METHOD_POST, {})

func _mark(draft: Dictionary, target: String, ref: String) -> void:
	host.api.request_json("studio-applied:%d" % int(draft.id), "/gm/prep/drafts/%d/applied" % int(draft.id), HTTPClient.METHOD_POST,
		{"request_id": "use-%d-" % int(draft.id) + Crypto.new().generate_random_bytes(6).hex_encode(), "target": target, "ref": ref.left(200)})

func place(draft: Dictionary) -> void:
	var payload: Dictionary = draft.get("payload", {})
	var body: Dictionary
	if draft.kind == "npc":
		body = npc_token(payload, host.library._spot())
	else:
		body = host.library.monster_token(payload, host.library._spot())
		body.sheet.source = {"prep_draft": int(draft.id), "generated_by": str(draft.get("model", "IA"))}
	host.api.request_json("studio-place:%d" % int(draft.id), "/gm/workspace/tokens", HTTPClient.METHOD_POST, body)

func create_item(draft: Dictionary) -> void:
	var payload: Dictionary = draft.get("payload", {})
	var description = str(payload.get("description", ""))
	if int(payload.get("value_po", 0)) > 0: description += "\nValor estimado: %d PO." % int(payload.value_po)
	host.api.request_json("studio-item:%d" % int(draft.id), "/gm/workspace/items", HTTPClient.METHOD_POST,
		{"name": str(payload.get("name", "Item")).left(160), "item_type": str(payload.get("item_type", "item")).left(80),
		"description": description.left(3000), "effects": payload.get("effects", []), "usable": bool(payload.get("usable", false))})

func add_map(draft: Dictionary) -> void:
	host.api.request_json("studio-map:%d" % int(draft.id), "/gm/prep/drafts/%d/apply-map" % int(draft.id), HTTPClient.METHOD_POST,
		{"request_id": "map-%d-once" % int(draft.id)})

func plan_with_ai() -> void:
	if session_id <= 0 or busy: return
	var key = str(session_id) + "|" + brief.strip_edges()
	if pending_plan.get("key") != key:
		pending_plan = {"key": key, "id": "plan-" + Crypto.new().generate_random_bytes(10).hex_encode()}
	busy = true
	host.api.request_json("studio-plan", "/gm/prep/sessions/%d/plan/generate" % session_id, HTTPClient.METHOD_POST,
		{"request_id": pending_plan.id, "brief": brief.strip_edges().left(1200)})
	_refresh()

func save_outline() -> void:
	if session_id <= 0: return
	host.api.request_json("studio-outline", "/gm/prep/sessions/%d/plan" % session_id, HTTPClient.METHOD_PUT,
		{"outline": outline_draft.left(24000), "version": int(_plan().get("version", 0))})

func save_record(extra: Dictionary = {}) -> void:
	var record = _session()
	if record.is_empty(): return
	var body = {"version": int(record.get("version", 0))}
	for field in ["title", "public_summary", "gm_summary"]:
		if record_draft.has(field): body[field] = str(record_draft[field])
	body.merge(extra, true)
	host.api.request_json("studio-record", "/gm/prep/sessions/%d/record" % session_id, HTTPClient.METHOD_PUT, body)

func new_session() -> void:
	if creating_session: return
	var next = 1
	for record in sessions:
		if record.get("session_number") != null: next = maxi(next, int(record.session_number) + 1)
	creating_session = true
	host.api.request_json("studio-new-session", "/gm/sessions", HTTPClient.METHOD_POST,
		{"request_id": "sess-%d-%s" % [next, Crypto.new().generate_random_bytes(5).hex_encode()], "title": "Sessão %d" % next, "session_number": next})

func _select(id: int) -> void:
	session_picked = true
	session_id = id
	outline_dirty = false
	outline_draft = str(_plan().get("outline", ""))
	record_draft = {}
	loaded = false
	_load_drafts()
	_refresh()

func save_context() -> void:
	host.api.request_json("studio-context-save", "/gm/prep/context", HTTPClient.METHOD_PUT,
		{"content": context_draft.left(24000), "version": int(context.get("version", 0))})

## Full NPC sheet carried on the pin (same fields as a player sheet), hidden and neutral.
static func npc_token(npc: Dictionary, spot: Dictionary) -> Dictionary:
	var sheet = {"marker": "☺", "role": "%s %s nível %d" % [str(npc.get("race", "")), str(npc.get("class_name", "")), int(npc.get("level", 1))],
		"disposition": "neutral", "level": int(npc.get("level", 1)), "armor_class": int(npc.get("armor_class", 10)),
		"initiative": int(npc.get("initiative", 0)), "saving_throw": npc.get("saving_throw"), "movement": npc.get("movement"),
		"base_attack": npc.get("base_attack"), "attributes": npc.get("attributes", {}), "race": npc.get("race"), "class_name": npc.get("class_name"),
		"alignment": npc.get("alignment"), "attacks": npc.get("attacks", []), "spells": npc.get("spells", []), "inventory": npc.get("inventory", []),
		"coins": npc.get("coins", {}), "abilities": (npc.get("abilities", []) as Array).map(func(a): return str(a.get("name", "")) + ": " + str(a.get("description", ""))),
		"description": str(npc.get("description", "")).left(600), "personality": npc.get("personality"), "appearance": npc.get("appearance"),
		"motivation": npc.get("motivation"), "notes": ("Segredo: " + str(npc.get("secret", ""))).left(600) if npc.get("secret") else "",
		"hooks": npc.get("hooks", []), "full_sheet": true}
	var hp = maxi(1, int(npc.get("maximum_hp", 10)))
	var body = {"token_type": "monster", "name": str(npc.get("name", "NPC")).left(120), "color": "#3f7d6b", "visible_to_players": false,
		"maximum_hp": hp, "current_hp": hp, "sheet": sheet}
	body.merge(spot)
	return body

# --- Respostas -------------------------------------------------------------------
func received(key: String, payload: Variant) -> void:
	if key == "studio-sessions":
		sessions = payload if payload is Array else []
		if not session_picked and (session_id == 0 or _session().is_empty()):
			for record in sessions:  # default: the next session still to be played
				if str(record.get("status", "")) in ["planned", "active"]: session_id = int(record.id)
		if not outline_dirty: outline_draft = str(_plan().get("outline", ""))
	elif key == "studio-new-session":
		creating_session = false
		session_id = int(payload.get("id", 0)) if payload is Dictionary else 0
		host._notice("Sessão criada. Escreva o roteiro ou peça à IA para preparar tudo.")
		open()
	elif key == "studio-plan":
		busy = false
		pending_plan = {}
		host._notice("A IA está preparando a sessão inteira: roteiro, NPCs, monstros, itens e mapas. Leva alguns minutos.")
		open()
	elif key == "studio-outline":
		outline_dirty = false
		host._notice("Roteiro salvo.")
		open()
	elif key == "studio-record":
		record_draft = {}
		host._notice("Registro da sessão salvo.")
		open()
	elif key == "studio-drafts":
		drafts = payload if payload is Array else []
		loaded = true
	elif key == "studio-generate":
		busy = false
		pending_generate = {}
		prompt = ""
		host._notice("Pedido enviado à IA. O rascunho aparece aqui em instantes.")
		open()
	elif key == "studio-discard":
		open()
	elif key.begins_with("studio-place:"):
		var id = int(key.get_slice(":", 1))
		_mark(_draft(id), "map", str(payload.get("id", "")) if payload is Dictionary else "")
		host._notice("Colocado no mapa, oculto. Revele pelo pin quando quiser.")
		host._poll()
	elif key.begins_with("studio-item:"):
		var id = int(key.get_slice(":", 1))
		_mark(_draft(id), "item", str(int(payload.get("id", 0))) if payload is Dictionary else "")
		host._notice("Item criado na campanha. Entregue pela Biblioteca → Itens.")
	elif key.begins_with("studio-map:"):
		host._notice("Mapa adicionado (oculto dos jogadores). Abra pela lista de Mapas.")
		open()
	elif key.begins_with("studio-applied:"):
		open()
	elif key == "studio-context":
		context = payload if payload is Dictionary else {}
		context_draft = str(context.get("content", ""))
	elif key == "studio-context-save":
		context = payload if payload is Dictionary else {}
		context_draft = str(context.get("content", ""))
		host._notice("Resumo da campanha salvo. A IA usa este texto em todos os pedidos.")
	_refresh()

func failed(key: String, message: String, code: int) -> bool:
	if not handles(key): return false
	busy = false
	if key == "studio-new-session": creating_session = false
	if key in ["studio-outline", "studio-record"] and code == 409:
		host._notice(message)
		open()
	elif key == "studio-plan" and host.keeper.network_error(code):
		host._notice("Sem resposta. Toque de novo: o mesmo pedido não é planejado duas vezes.")
	elif key in ["studio-drafts", "studio-sessions"] and code in [404, 405]:
		host._notice("O servidor ainda não tem o Estúdio com IA (precisa reiniciar o backend).")
	elif key == "studio-generate" and host.keeper.network_error(code):
		host._notice("Sem resposta. Toque em Gerar de novo: o mesmo pedido não é gerado duas vezes.")
	elif key == "studio-context-save" and code == 409:
		host._notice(message)
		host.api.request_json("studio-context", "/gm/prep/context")
	else:
		if key == "studio-generate": pending_generate = {}
		if key == "studio-plan": pending_plan = {}
		host._notice(message)
	_refresh()
	return true

func _draft(id: int) -> Dictionary:
	for draft in drafts:
		if int(draft.get("id", -1)) == id: return draft
	return {"id": id}

# --- Painel ----------------------------------------------------------------------
func render(body: Node) -> void:
	_session_box(body)
	Style.label(body, "Estúdio com IA" + (" · rascunhos desta sessão" if session_id > 0 else ""), 18)
	Style.label(body, "Peça em texto; a IA cria um rascunho com ficha validada pelo servidor. Nada vai à mesa sem você aplicar.", 13)
	var kinds = OptionButton.new()
	for entry in KINDS:
		kinds.add_item(entry[1])
		kinds.set_item_metadata(kinds.item_count - 1, entry[0])
		if entry[0] == kind: kinds.select(kinds.item_count - 1)
	kinds.item_selected.connect(func(i): kind = str(kinds.get_item_metadata(i)))
	body.add_child(kinds)
	var ask = TextEdit.new()
	ask.custom_minimum_size = Vector2(0, 70)
	ask.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	ask.placeholder_text = "Ex.: um capitão de navio corrupto que deve dinheiro ao Conclave, nível 4"
	ask.text = prompt
	ask.text_changed.connect(func(): prompt = ask.text)
	body.add_child(ask)
	var go = Button.new()
	go.text = "Gerar com a IA" if not busy else "Enviando…"
	go.disabled = busy
	go.custom_minimum_size.y = 44
	go.pressed.connect(generate)
	body.add_child(go)
	_context_box(body)
	if not loaded:
		Style.label(body, "Carregando rascunhos…", 14)
		open()
		return
	if drafts.is_empty():
		Style.label(body, "Nenhum rascunho ainda.", 14)
	for draft in drafts:
		_card(body, draft)

const STATUS = {"planned": "a jogar", "active": "em jogo", "paused": "pausada", "completed": "jogada"}

func _session_box(body: Node) -> void:
	var row = HBoxContainer.new()
	body.add_child(row)
	var pick = OptionButton.new()
	pick.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pick.add_item("Rascunhos soltos (sem sessão)")
	pick.set_item_metadata(0, 0)
	for record in sessions:
		var counts: Dictionary = record.get("draft_counts", {})
		var total = counts.values().reduce(func(a, b): return a + b, 0)
		var number = str(int(record.session_number)) if record.get("session_number") != null else "?"
		var title = str(record.get("title", "")).trim_prefix("Sessão %s — " % number).trim_prefix("Sessão %s" % number)
		pick.add_item("Sessão %s%s (%s%s)" % [number, (" — " + title) if title.strip_edges() != "" else "",
			STATUS.get(str(record.get("status", "")), str(record.get("status", ""))), " · %d rascunhos" % total if total > 0 else ""])
		pick.set_item_metadata(pick.item_count - 1, int(record.id))
		if int(record.id) == session_id: pick.select(pick.item_count - 1)
	pick.item_selected.connect(func(i): _select(int(pick.get_item_metadata(i))))
	row.add_child(pick)
	var add = Button.new()
	add.text = "+ Nova sessão"
	add.disabled = creating_session
	add.pressed.connect(new_session)
	row.add_child(add)
	var record = _session()
	if record.is_empty(): return
	if str(record.get("status", "")) == "completed":
		_record_box(body, record)
	else:
		_plan_box(body, record)

func _record_box(body: Node, record: Dictionary) -> void:
	Style.label(body, "Sessão jogada: o que ficou registrado (os jogadores veem o resumo público).", 13)
	for field in [["title", "Título", 0], ["public_summary", "Resumo público", 110], ["gm_summary", "Notas do Mestre (secretas)", 110]]:
		var key: String = field[0]
		Style.label(body, field[1], 13)
		var value = str(record_draft.get(key, record.get(key) if record.get(key) != null else ""))
		if field[2] == 0:
			var line = LineEdit.new()
			line.text = value
			line.text_changed.connect(func(t): record_draft[key] = t)
			body.add_child(line)
		else:
			var edit = TextEdit.new()
			edit.custom_minimum_size = Vector2(0, field[2])
			edit.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
			edit.text = value
			edit.text_changed.connect(func(): record_draft[key] = edit.text)
			body.add_child(edit)
	var row = HBoxContainer.new()
	body.add_child(row)
	var save = Button.new()
	save.text = "Salvar registro"
	save.pressed.connect(func(): save_record())
	row.add_child(save)
	var reopen = Button.new()
	reopen.text = "Voltar para preparação"
	reopen.pressed.connect(func(): save_record({"status": "planned"}))
	row.add_child(reopen)

func _plan_box(body: Node, record: Dictionary) -> void:
	var plan = _plan()
	var status = str(plan.get("status", "draft"))
	var state = {"planning": "A IA está escrevendo o roteiro…", "generating": "Roteiro pronto; a IA está gerando NPCs, monstros, itens e mapas…",
		"failed": "A preparação falhou: " + str(plan.get("error", "")), "ready": "Preparação pronta. Revise o roteiro e aplique os rascunhos."}.get(status, "")
	if state != "": Style.label(body, state, 13)
	Style.label(body, "Roteiro da sessão (só o Mestre vê)", 14)
	var outline = TextEdit.new()
	outline.custom_minimum_size = Vector2(0, 220)
	outline.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	outline.text = outline_draft
	outline.editable = status != "planning"
	outline.placeholder_text = "Abertura, cenas em ordem (local, objetivo, conflito, saída), ganchos, recompensas, plano B…"
	outline.text_changed.connect(func():
		outline_draft = outline.text
		outline_dirty = true)
	body.add_child(outline)
	var save = Button.new()
	save.text = "Salvar roteiro"
	save.disabled = status == "planning"
	save.pressed.connect(save_outline)
	body.add_child(save)
	var ask = LineEdit.new()
	ask.placeholder_text = "Pedido para a IA (ex.: o grupo chega a Nimalis e o Conclave cobra a dívida)"
	ask.text = brief
	ask.text_changed.connect(func(t): brief = t)
	body.add_child(ask)
	var go = Button.new()
	go.text = "Preparar a sessão inteira com a IA" if not busy else "Enviando…"
	go.disabled = busy or status in ["planning", "generating"]
	go.tooltip_text = "Escreve o roteiro e gera os NPCs, monstros, itens e mapas como rascunhos desta sessão."
	go.custom_minimum_size.y = 44
	go.pressed.connect(plan_with_ai)
	body.add_child(go)

func _context_box(body: Node) -> void:
	var toggle = Button.new()
	toggle.text = ("▾ " if context_open else "▸ ") + "Resumo da campanha (o que a IA sabe)"
	toggle.flat = true
	toggle.alignment = HORIZONTAL_ALIGNMENT_LEFT
	toggle.pressed.connect(func():
		context_open = not context_open
		if context_open and context.is_empty(): host.api.request_json("studio-context", "/gm/prep/context")
		_refresh())
	body.add_child(toggle)
	if not context_open: return
	var editor = TextEdit.new()
	editor.custom_minimum_size = Vector2(0, 180)
	editor.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	editor.text = context_draft
	editor.placeholder_text = "Resumo das sessões, lugares, facções, NPCs importantes, pontas soltas…"
	editor.text_changed.connect(func(): context_draft = editor.text)
	body.add_child(editor)
	var save = Button.new()
	save.text = "Salvar resumo"
	save.pressed.connect(save_context)
	body.add_child(save)

func _card(body: Node, draft: Dictionary) -> void:
	var panel = PanelContainer.new()
	body.add_child(panel)
	var box = VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	panel.add_child(box)
	var status = str(draft.get("status", ""))
	var head = "%s · %s" % [LABELS.get(str(draft.get("kind", "")), "Rascunho"), str(draft.get("title", ""))]
	if status == "applied": head += " · usado"
	Style.label(box, head, 16)
	if status == "generating":
		Style.label(box, "Gerando… a IA costuma levar de 30 s a 2 min. Pedido: " + str(draft.get("prompt", "")).left(160), 13)
		return
	if status == "failed":
		Style.label(box, "Não deu certo: " + str(draft.get("error", "")), 13)
		_actions(box, draft, [])
		return
	var payload: Dictionary = draft.get("payload", {}) if draft.get("payload") is Dictionary else {}
	var id = int(draft.id)
	var open = expanded.get(id, false)
	match str(draft.kind):
		"monster": _monster(box, payload, open)
		"npc": _npc(box, payload, open)
		"item": _item(box, payload)
		"map": _map(box, draft, payload)
	if str(draft.kind) in ["monster", "npc"]:
		var more = Button.new()
		more.text = "Ver ficha completa" if not open else "Resumir"
		more.flat = true
		more.pressed.connect(func(): expanded[id] = not open; _refresh())
		box.add_child(more)
	var buttons: Array = []
	match str(draft.kind):
		"monster", "npc": buttons.append(["No mapa (oculto)", func(): place(draft)])
		"item": buttons.append(["Criar item da campanha", func(): create_item(draft)])
		"map":
			if not (draft.get("applied", []) as Array).any(func(a): return a.get("target") == "map"):
				buttons.append(["Adicionar aos mapas", func(): add_map(draft)])
	_actions(box, draft, buttons)

func _actions(box: Node, draft: Dictionary, buttons: Array) -> void:
	var row = HFlowContainer.new()
	box.add_child(row)
	for entry in buttons:
		var button = Button.new()
		button.text = entry[0]
		button.pressed.connect(entry[1])
		row.add_child(button)
	var drop = Button.new()
	drop.text = "Descartar"
	drop.pressed.connect(func(): discard(draft))
	row.add_child(drop)

static func _attack_line(attacks: Array) -> String:
	return "; ".join(attacks.map(func(a): return "%s%s %+d (%s)%s" % [("%d× " % int(a.count)) if int(a.get("count", 1)) > 1 else "",
		str(a.get("name", "")), int(a.get("bonus", 0)), str(a.get("damage", "")), (" %dm" % int(a.range_m)) if a.get("range_m") else ""]))

func _monster(box: Node, m: Dictionary, full: bool) -> void:
	Style.label(box, "%s · CA %d · PV %d (DV %s) · JP %d · MO %d · Mov %d" % [str(m.get("category", "")), int(m.get("armor_class", 0)),
		int(m.get("average_hp", 0)), str(m.get("hit_dice", "")), int(m.get("saving_throw", 0)), int(m.get("morale", 0)), int(m.get("movement", 0))], 13)
	Style.label(box, "Ataques: " + _attack_line(m.get("attacks", [])), 13)
	if full:
		for ability in m.get("abilities", []): Style.label(box, "• %s: %s" % [str(ability.get("name", "")), str(ability.get("description", ""))], 13)
		if m.get("tactics"): Style.label(box, "Táticas: " + str(m.tactics), 13)
		Style.label(box, "Tesouro %s · XP %d" % [str(m.get("treasure", "-")), int(m.get("experience_points", 0))], 13)
	if m.get("description"): Style.label(box, str(m.description).left(600 if full else 160), 13)

func _npc(box: Node, n: Dictionary, full: bool) -> void:
	Style.label(box, "%s %s nível %d · %s" % [str(n.get("race", "")), str(n.get("class_name", "")), int(n.get("level", 1)), str(n.get("alignment", ""))], 13)
	var attributes: Dictionary = n.get("attributes", {}) if n.get("attributes") is Dictionary else {}
	Style.label(box, "FOR %d DES %d CON %d INT %d SAB %d CAR %d" % [int(attributes.get("strength", 10)), int(attributes.get("dexterity", 10)),
		int(attributes.get("constitution", 10)), int(attributes.get("intelligence", 10)), int(attributes.get("wisdom", 10)), int(attributes.get("charisma", 10))], 13)
	Style.label(box, "PV %d · CA %d · JP %d · BA %d · Mov %d" % [int(n.get("maximum_hp", 0)), int(n.get("armor_class", 0)),
		int(n.get("saving_throw", 0)), int(n.get("base_attack", 0)), int(n.get("movement", 0))], 13)
	if n.get("personality"): Style.label(box, "Personalidade: " + str(n.personality), 13)
	if not full: return
	Style.label(box, "Ataques: " + _attack_line(n.get("attacks", [])), 13)
	if not (n.get("spells", []) as Array).is_empty():
		Style.label(box, "Magias: " + ", ".join((n.spells as Array).map(func(s): return "%s (%dº, %d/dia)" % [str(s.name), int(s.circle), int(s.daily_uses)])), 13)
	if not (n.get("inventory", []) as Array).is_empty():
		Style.label(box, "Inventário: " + ", ".join((n.inventory as Array).map(func(i): return ("%d× " % int(i.quantity) if int(i.quantity) > 1 else "") + str(i.name))), 13)
	for ability in n.get("abilities", []): Style.label(box, "• %s: %s" % [str(ability.get("name", "")), str(ability.get("description", ""))], 13)
	for field in [["appearance", "Aparência"], ["motivation", "Motivação"], ["secret", "Segredo (só o Mestre)"], ["description", "Descrição"]]:
		if n.get(field[0]): Style.label(box, field[1] + ": " + str(n[field[0]]), 13)
	for hook in n.get("hooks", []): Style.label(box, "Gancho: " + str(hook), 13)

func _item(box: Node, item: Dictionary) -> void:
	Style.label(box, str(item.get("item_type", "item")).capitalize() + ((" · %d PO" % int(item.value_po)) if int(item.get("value_po", 0)) > 0 else ""), 13)
	if item.get("description"): Style.label(box, str(item.description), 13)
	for effect in item.get("effects", []): Style.label(box, "• " + str(effect), 13)

func _map(box: Node, draft: Dictionary, map: Dictionary) -> void:
	if draft.get("preview_path"):
		var picture = TextureRect.new()
		picture.custom_minimum_size = Vector2(0, 220)
		picture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		picture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		box.add_child(picture)
		host.media.bind(str(draft.preview_path), picture, "texture")
	if map.get("description"): Style.label(box, str(map.description), 13)
	if not (map.get("areas", []) as Array).is_empty(): Style.label(box, "Áreas: " + "; ".join(map.areas), 13)
	if not (map.get("hazards", []) as Array).is_empty(): Style.label(box, "Perigos: " + "; ".join(map.hazards), 13)
