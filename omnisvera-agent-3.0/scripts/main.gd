extends Node2D
## Persistent world scene with temporary native HUD panels.
const Backend = preload("res://scripts/api_client.gd")
const Navigation = preload("res://scripts/navigation_panel.gd")
const Roster = preload("res://scripts/hud_player.gd")
const Media = preload("res://scripts/media_cache.gd")
const Style = preload("res://scripts/ui_style.gd")
const Content = preload("res://scripts/panel_content.gd")
const MapViewer = preload("res://scripts/map_viewer.gd")
const Commands = preload("res://scripts/game_commands.gd")
const Gothic = preload("res://scripts/gothic_theme.gd")
@onready var grid = $GridMap
@onready var dorn = $Dorn
@onready var morthak = $Morthak
var animated_actors: Dictionary = {}
var sprite_map_id: String = ""
var missing_actor_notice: bool = false
@onready var camera: Camera2D = $Camera2D
@onready var screen: Control = $UILayer/Screen

var api = Backend.new()
var media = Media.new()
var content = Content.new()
var map_viewer = MapViewer.new()
var detail_panel = PanelContainer.new()
var detail_body = VBoxContainer.new()
var detail_title = Label.new()
var maps: Array = []
var sessions: Array = []
var scenes: Array = []
var preparation = preload("res://scripts/scene_preparation.gd").new()
var confirm_preparation = ConfirmationDialog.new()
var preparation_intent: Dictionary = {}
var selected_session: Dictionary = {}
var session_id: int = -1
var requested_map: String = ""
var my_profile: String = ""
var nav = Navigation.new()
var roster = Roster.new()
var status = Label.new()
var map_label = Label.new()
var combat_state: Dictionary = {}
var battle_overlay = preload("res://scripts/battle_overlay.gd").new()
# Feature controllers (scripts/controllers). main.gd keeps connection, polling,
# exploration, drawers and sessions; each controller owns one area of the game.
var battle = preload("res://scripts/controllers/battle_controller.gd").new()
var town = preload("res://scripts/controllers/town_controller.gd").new()
var hud = preload("res://scripts/controllers/hud_controller.gd").new()
var keeper = preload("res://scripts/controllers/connection_keeper.gd").new()
var library = preload("res://scripts/controllers/library_controller.gd").new()
var dice = preload("res://scripts/controllers/dice_controller.gd").new()
var pins = preload("res://scripts/controllers/pin_actions_controller.gd").new()
var powers = preload("res://scripts/controllers/powers_controller.gd").new()
var progress = preload("res://scripts/controllers/progress_controller.gd").new()
var studio = preload("res://scripts/controllers/studio_controller.gd").new()
var map_editor = preload("res://scripts/map_editor.gd").new()
var controllers: Array = []
var arena_snapshot: Dictionary = {}
var pending_intent: Dictionary = {}
var command_inflight: bool = false
var targeting: Dictionary = {}
var target_ids: Array = []
var confirm_action = ConfirmationDialog.new()
var confirm_session = ConfirmationDialog.new()
var confirm_remove_pin = ConfirmationDialog.new()
var remove_pin_id: String = ""
var session_change: Dictionary = {}
var retry_button = Button.new()
var connection = PanelContainer.new()
var token_input = LineEdit.new()
var url_input = LineEdit.new()
var connect_button = Button.new()
var panel = PanelContainer.new()
var body = VBoxContainer.new()
var title = Label.new()
var log_box = VBoxContainer.new()
var recent = Label.new()
var message_input = LineEdit.new()
var character_select = OptionButton.new()
var characters: Array = []
var presence: Array = []
var workspace: Dictionary = {}
var sheet: Dictionary = {}
var ledger: Array = []
var selected_id: String = ""
var active_panel: String = ""
var authenticated: bool = false
var master: bool = false
var first_map: bool = true
var editor_brush: int = -1
var local_preview: bool = true
var drag_start = Vector2.ZERO
var drag_distance: float = 0
var dragging: bool = false
var preview_target = Vector2i(6, 6)
var last_message: String = ""
var notice_serial: int = 0
var recent_serial: int = 0

func _ready() -> void:
	if FileAccess.file_exists("res://assets/rom2_local/map.json"):
		var terrain = load("res://scripts/rom2_terrain.gd").new()
		terrain.z_index = -10
		add_child(terrain)
		grid.terrain = terrain
		terrain.edited.connect(grid._build_blocked)  # map editor: new trees/houses block movement at once
	animated_actors = {"dorn7": dorn, "morthak": morthak}
	for actor in animated_actors.values(): actor.projection = grid
	add_child(api)
	add_child(media)
	content.media = media
	content.details = _show_detail
	content.open_map = _open_map
	content.open_session = _open_session
	content.activate = _activate_ability
	roster.media = media
	api.received.connect(_received)
	api.failed.connect(_failed)
	_build_hud()
	controllers = [battle, town, hud, keeper, library, dice, pins, powers, progress, studio, map_editor]
	for controller in controllers:
		add_child(controller)
	keeper.setup(self)
	hud.setup(self)
	town.setup(self)
	battle.setup(self)
	library.setup(self)
	dice.setup(self)
	pins.setup(self)
	powers.setup(self)
	progress.setup(self)
	studio.setup(self)
	map_editor.setup(self)
	preparation.library = library

	Style.rom_frame(panel)
	Style.rom_frame(detail_panel)
	body.minimum_size_changed.connect(func(): call_deferred("_fit_drawers"))
	detail_body.minimum_size_changed.connect(func(): call_deferred("_fit_drawers"))
	screen.add_child(confirm_preparation)
	screen.add_child(confirm_remove_pin)
	confirm_remove_pin.title = "Remover marcador"
	confirm_remove_pin.ok_button_text = "Remover"
	confirm_remove_pin.cancel_button_text = "Cancelar"
	confirm_remove_pin.confirmed.connect(func():
		if master and remove_pin_id != "":
			api.request_json("pin-remove", "/gm/workspace/tokens/" + remove_pin_id, HTTPClient.METHOD_DELETE)
			detail_panel.hide()
		remove_pin_id = "")
	confirm_preparation.confirmed.connect(func():
		if master and authenticated and not preparation_intent.is_empty(): _send_intent("scene-selection", preparation_intent))
	confirm_preparation.canceled.connect(func(): preparation_intent.clear())
	preparation.changed.connect(func(): call_deferred("_refresh_preparation"))
	screen.add_child(confirm_session)
	confirm_session.confirmed.connect(_commit_session_status)
	confirm_session.canceled.connect(func(): session_change.clear())
	grid.queue_redraw()
	dorn.snap_visual(grid.grid_to_world(Vector2i(6, 6)))
	camera.position = dorn.position
	get_viewport().size_changed.connect(_layout)
	_layout()
	var poll = Timer.new()
	poll.wait_time = 8
	poll.timeout.connect(_poll)
	add_child(poll)
	# The battle board covers the world: stop drawing the map underneath it (big saving on slow notebooks/phones).
	battle_overlay.world_ref = grid
	grid.media = media
	battle_overlay.visibility_changed.connect(func():
		grid.visible = not battle_overlay.visible
		if grid.terrain: grid.terrain.visible = not battle_overlay.visible)
	# During a battle the board refreshes fast, so turns and enemy moves show up at once.
	var battle_poll = Timer.new()
	battle_poll.wait_time = 1.5
	battle_poll.timeout.connect(_battle_poll)
	add_child(battle_poll)
	battle_poll.start()
	poll.start()
	var bootstrap: Dictionary = {}
	if OS.has_feature("web"):
		var raw = JavaScriptBridge.eval("JSON.stringify(window.omniBootstrap || {})")
		if raw is String:
			var parsed: Variant = JSON.parse_string(raw)
			if parsed is Dictionary:
				bootstrap = parsed
				JavaScriptBridge.eval("delete window.omniBootstrap.token")
	url_input.text = str(bootstrap.get("base_url", "http://127.0.0.1:8787"))
	token_input.text = str(bootstrap.get("token", ""))
	if OS.has_feature("web"):
		url_input.visible = false
	if not token_input.text.is_empty():
		_connect()
	if "--smoke-test" in OS.get_cmdline_user_args():
		_smoke_test()

func _build_hud() -> void:
	screen.theme = Gothic.build()
	screen.add_child(nav)
	nav.panel_requested.connect(_open_panel)
	screen.add_child(roster)
	roster.character_selected.connect(func(id: String):
		selected_id = id
		_open_panel("sheet")
	)
	screen.add_child(status)
	screen.add_child(retry_button)
	retry_button.text = "Reenviar"
	retry_button.tooltip_text = "Reenviar o mesmo comando, sem duplicar"
	retry_button.hide()
	retry_button.pressed.connect(func():
		if not pending_intent.is_empty() and not command_inflight:
			command_inflight = true
			api.request_json(str(pending_intent.key), str(pending_intent.path), HTTPClient.METHOD_POST, pending_intent.payload)
	)
	add_child(confirm_action)
	confirm_action.title = "Relâmpago"
	confirm_action.ok_button_text = "Confirmar"
	confirm_action.cancel_button_text = "Cancelar"
	confirm_action.confirmed.connect(func():
		var targets: Array = []
		for id in target_ids:
			targets.append({"type": "token", "id": id})
		_send_effect("dorn_spell_cast", {"spell_id": "relampago", "grid_selection": true,
			"map_id": workspace.get("map", {}).get("id"), "definition_revision": targeting.get("revision"), "targets": targets})
	)
	confirm_action.canceled.connect(_cancel_targeting)
	screen.add_child(map_label)
	map_label.text = "Arredores de Nimalis"
	map_label.add_theme_font_size_override("font_size", 16)
	map_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	status.text = "Prévia local · conecte seu acesso"
	status.add_theme_color_override("font_color", Color("#bfd5c8"))
	status.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var notice_box = StyleBoxFlat.new()
	notice_box.bg_color = Color(0.05, 0.035, 0.03, 0.88)
	notice_box.border_color = Color(0.48, 0.36, 0.17, 0.8)
	notice_box.set_border_width_all(1)
	notice_box.set_content_margin_all(6)
	status.add_theme_stylebox_override("normal", notice_box)
	recent.add_theme_stylebox_override("normal", notice_box)
	status.hide()
	screen.add_child(connection)
	connection.z_index = 30
	var access_box = VBoxContainer.new()
	access_box.add_theme_constant_override("separation", 12)
	connection.add_child(access_box)
	_label(access_box, "OMNISVERA", 24)
	_label(access_box, "Companion 3.0 · acesso à mesa", 15)
	url_input.placeholder_text = "Endereço do backend"
	access_box.add_child(url_input)
	token_input.placeholder_text = "Seu token de acesso"
	token_input.secret = true
	access_box.add_child(token_input)
	token_input.text_submitted.connect(func(_text: String): _connect())
	connect_button.text = "Conectar"
	connect_button.pressed.connect(_connect)
	access_box.add_child(connect_button)
	var demo = Button.new()
	demo.text = "Explorar prévia local"
	demo.pressed.connect(func():
		connection.hide()
		status.text = "Prévia local · clique para caminhar · arraste para navegar"
	)
	access_box.add_child(demo)
	screen.add_child(panel)
	panel.z_index = 20
	panel.hide()
	var panel_box = VBoxContainer.new()
	panel_box.add_theme_constant_override("separation", 12)
	panel.add_child(panel_box)
	var heading = HBoxContainer.new()
	panel_box.add_child(heading)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.add_theme_font_size_override("font_size", 21)
	heading.add_child(title)
	var close_button = Button.new()
	Style.icon_button(close_button, load("res://assets/ui/close.svg"), "Fechar painel", 24)
	close_button.pressed.connect(func(): panel.hide(); active_panel = "")
	heading.add_child(close_button)
	character_select.item_selected.connect(func(index: int):
		selected_id = str(character_select.get_item_metadata(index))
		roster.controlled_id = selected_id if master else my_profile
		roster.update_roster(characters, presence)
		_load_sheet()
		_received("workspace", workspace)
	)
	panel_box.add_child(character_select)
	var scroll = ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel_box.add_child(scroll)
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 12)
	scroll.add_child(body)
	screen.add_child(log_box)
	recent.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	recent.add_theme_font_size_override("font_size", 13)
	recent.hide()
	screen.add_child(recent)
	recent.mouse_filter = Control.MOUSE_FILTER_IGNORE
	recent.max_lines_visible = 4
	log_box.mouse_entered.connect(func(): recent.show())
	log_box.mouse_exited.connect(func(): recent.hide())
	# Chat row: input and the full-log button side by side, flush to the bottom-right corner.
	var chat_row = HBoxContainer.new()
	chat_row.add_theme_constant_override("separation", 4)
	log_box.add_child(chat_row)
	message_input.placeholder_text = "Mensagem para a mesa…"
	message_input.text_submitted.connect(_send_message)
	message_input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	message_input.custom_minimum_size.y = 40
	chat_row.add_child(message_input)
	var expand = Button.new()
	Style.icon_button(expand, load("res://assets/ui/log.svg"), "Registro completo da sessão", 30)
	expand.custom_minimum_size = Vector2(42, 40)
	expand.pressed.connect(func(): _open_panel("log"))
	chat_row.add_child(expand)
	screen.add_child(map_viewer)
	map_viewer.media = media
	media.failed.connect(map_viewer.media_failed)
	map_viewer.z_index = 25
	map_viewer.pin_selected.connect(_show_pin)
	screen.add_child(detail_panel)
	detail_panel.z_index = 40
	detail_panel.hide()
	var detail_column = VBoxContainer.new()
	detail_panel.add_child(detail_column)
	var detail_heading = HBoxContainer.new()
	detail_column.add_child(detail_heading)
	detail_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail_title.clip_text = true
	detail_title.add_theme_font_size_override("font_size", 20)
	detail_heading.add_child(detail_title)
	var detail_close = Button.new()
	Style.icon_button(detail_close, load("res://assets/ui/close.svg"), "Fechar detalhes", 24)
	detail_close.pressed.connect(detail_panel.hide)
	detail_heading.add_child(detail_close)
	var detail_scroll = ScrollContainer.new()
	detail_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	detail_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	detail_column.add_child(detail_scroll)
	detail_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail_body.add_theme_constant_override("separation", 12)
	detail_scroll.add_child(detail_body)

func _label(parent: Node, text: String, font_size: int = 15) -> Label:
	var label = Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.add_theme_font_size_override("font_size", font_size)
	parent.add_child(label)
	return label

func _number(value: Variant) -> String:
	if value is float and is_equal_approx(value, roundf(value)):
		return str(int(value))
	return str(value)

func _layout() -> void:
	var size = get_viewport_rect().size
	battle_overlay.position=Vector2.ZERO
	battle_overlay.size=size
	# City and shops open as a framed window over the map (full screen only on small phones).
	var frame = Vector2(minf(size.x - 40, 1000), minf(size.y - 90, 660)) if size.x > 760 else size
	for overlay in [town.city_screen, town.shop]:
		overlay.size = frame
		overlay.position = ((size - frame) / 2).floor()
	# Bottom row: vitals bar centered between the side menu and the chat, chat flush to the bottom-right corner.
	var chat_width = clampf(size.x * 0.30, 210, 340)
	hud.view.slot_size = 36.0 if size.y < 500 else 44.0
	var hud_height = hud.view.slot_size * 1.45 * 1.55 + 4
	var lane_start = 70.0
	var lane_end = size.x - chat_width - 6
	var hud_width = minf(hud.view.preferred_width(), lane_end - lane_start)
	var centered = (size.x - hud_width) / 2
	hud.view.position = Vector2(clampf(centered, lane_start, maxf(lane_start, lane_end - hud_width)), size.y - hud_height)
	hud.view.size = Vector2(hud_width, hud_height)
	nav.fit_height(size.y)
	nav.position = Vector2(10, (size.y - nav.size.y) / 2)
	var drawer_x = nav.position.x + nav.size.x + 14
	map_label.position = Vector2(14, 10)
	map_label.size = Vector2(240, 24)
	map_label.clip_text = true
	roster.position = Vector2(maxf(75, size.x - maxf(1, roster.get_child_count()) * 52 - 14), 10)
	# Notices sit right above the chat box, wrapped inside its width (never past the screen edge).
	status.size = Vector2(chat_width - 8, 0)
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status.clip_text = false
	status.max_lines_visible = 3
	status.reset_size()
	status.size.x = chat_width - 8
	status.position = Vector2(size.x - chat_width + 4, size.y - 48 - status.get_combined_minimum_size().y)
	retry_button.position = Vector2(drawer_x, 64)
	connection.position = Vector2(maxf(70, (size.x - 340) / 2), maxf(14, (size.y - 270) / 2))
	connection.size = Vector2(minf(340, size.x - 84), 0)
	panel.position = Vector2(drawer_x, 14)
	panel.size.x = minf(420, size.x - drawer_x - 14)
	detail_panel.position = Vector2(drawer_x + 8, 14)
	detail_panel.size.x = minf(460, size.x - drawer_x - 22)
	map_viewer.position = Vector2(drawer_x, 14)
	map_viewer.size = Vector2(maxf(240, size.x - drawer_x - 14), maxf(150, size.y - 28))
	log_box.size = Vector2(chat_width, 42)
	log_box.position = Vector2(size.x - chat_width, size.y - 42)
	_place_recent()
	if active_panel == "log":
		# The full log opens on the right, above the chat row.
		panel.size.x = minf(420, size.x - drawer_x - 14)
		panel.position = Vector2(size.x - panel.size.x, 14)
	call_deferred("_fit_drawers")
	if size.x < 600 and first_map:
		camera.zoom = Vector2(0.9, 0.9)

func _fit_drawers() -> void:
	var available = maxf(150,get_viewport_rect().size.y-28)
	panel.size.y = clampf(body.get_combined_minimum_size().y+100+(48 if character_select.visible else 0),150,available - (48.0 if active_panel == "log" else 0.0))
	detail_panel.size.y = clampf(detail_body.get_combined_minimum_size().y+90,150,available)
	for window in [panel,detail_panel]:
		var border = window.get_node_or_null("ROM2Border")
		if border:
			border.global_position = window.global_position
			border.size = window.size

func _connect() -> void:
	battle_overlay.hide()
	battle.exploration_snapshot.clear()
	arena_snapshot.clear()
	preparation.select({})
	preparation_intent.clear()
	confirm_preparation.hide()
	if token_input.text.strip_edges().is_empty():
		status.text = "Informe seu acesso à mesa"
		return
	api.configure(url_input.text, token_input.text)
	pending_intent.clear()
	targeting.clear()
	target_ids.clear()
	combat_state.clear()
	command_inflight = false
	media.configure(api.base_url, token_input.text)
	map_viewer.clear()
	detail_panel.hide()
	maps.clear()
	sessions.clear()
	selected_session.clear()
	requested_map = ""
	authenticated = false
	master = false
	characters.clear()
	presence.clear()
	ledger.clear()
	sheet.clear()
	workspace.clear()
	grid.configure_grid({}, [])
	dorn.snap_visual(grid.grid_to_world(Vector2i(6, 6)))
	morthak.snap_visual(grid.grid_to_world(Vector2i(7, 6)))
	morthak.visible = false
	sprite_map_id = ""
	camera.position = dorn.position
	roster.update_roster([], [])
	nav.set_master(false)
	panel.hide()
	active_panel = ""
	dorn.visible = true
	dorn.preview = true
	local_preview = true
	first_map = true
	connect_button.disabled = true
	status.text = "Conectando ao Companion…"
	api.request_json("health", "/health")

func _battle_poll() -> void:
	var enc: Dictionary = combat_state.get("encounter", {}) if combat_state.get("encounter") is Dictionary else {}
	if not authenticated or not enc.get("active", false) or not enc.get("battle_mode", false): return
	api.request_json("arena-workspace", "/workspace?map_id=" + str(enc.get("map_id", "")).uri_encode())
	api.request_json("combat", "/combat/effects")

func _poll() -> void:
	if not authenticated:
		return
	if combat_state.get("encounter",{}).get("active",false) and combat_state.get("encounter",{}).get("battle_mode",false):
		api.request_json("arena-workspace","/workspace?map_id="+str(combat_state.encounter.map_id).uri_encode())
	else:
		api.request_json("workspace", "/workspace")
	api.request_json("combat", "/combat/effects")
	api.request_json("ledger", "/workspace/ledger?limit=80")
	api.request_json("presence", "/workspace/heartbeat", HTTPClient.METHOD_POST)
	if not selected_id.is_empty() and panel.visible:
		_load_sheet()
	hud.load_sheet()
	dice.poll()
	studio.poll()
	map_editor.poll()

func _received(key: String, data: Variant) -> void:
	for controller in controllers:
		if controller.handles(key):
			controller.received(key, data)
			return
	if key.begins_with("preparation:"):
		if master and int(key.get_slice(":",1))==int(preparation.scene.get("id",-1)):
			preparation.scene = data if data is Dictionary else {}
			if preparation.scene.get("map_id"): api.request_json("preparation-pins:"+str(preparation.scene.id),"/workspace?map_id="+str(preparation.scene.map_id).uri_encode())
			_refresh_preparation()
		return
	if key.begins_with("preparation-pins:"):
		if master and int(key.get_slice(":",1))==int(preparation.scene.get("id",-1)):
			preparation.pins = data.get("tokens",[]) if data is Dictionary else []
			_refresh_preparation()
		return
	if key=="scene-selection":
		command_inflight = false
		pending_intent.clear()
		preparation_intent.clear()
		retry_button.hide()
		panel.hide()
		active_panel = ""
		api.request_json("scenes","/scenes")
		_poll()
		if data.get("map") is Dictionary: _open_map(str(data.map.id))
		_notice("Seleção enviada à mesa · resultado no Registro")
		return
	if key in ["city-place", "city-toggle"]:
		_notice("Cidade colocada no mapa (oculta). Abra para os jogadores nas ferramentas do Mestre." if key == "city-place" else "Visibilidade da cidade atualizada")
		_poll()
		if panel.visible and active_panel == "gm": _render_panel.call_deferred()
		return
	if key in ["pin-edit", "pin-remove"]:
		_notice("Marcador removido" if key == "pin-remove" else "Marcador atualizado")
		_poll()
		return
	if key == "disposition":
		_notice("Disposição do marcador atualizada")
		_poll()
		return
	if key == "session-status":
		session_change.clear()
		selected_session = data if data is Dictionary else {}
		api.request_json("sessions", "/sessions")
		api.request_json("ledger", "/workspace/ledger?limit=80")
		if panel.visible and active_panel in ["gm", "sessions"]: _render_panel()
		return
	if key == "move":
		retry_button.hide()
		command_inflight = false
		var token_id = str(pending_intent.get("payload", {}).get("token_id", ""))
		var accepted_path: Array = pending_intent.get("payload", {}).get("path", [])
		pending_intent.clear()
		if data is Dictionary and data.get("position") is Dictionary:
			for token in workspace.get("tokens", []):
				if token.id == token_id:
					token.grid_position = data.position
					if animated_actors.has(str(token.get("character_id"))):
						var points: Array = []
						for cell in accepted_path:
							points.append(grid.grid_to_world(Vector2i(int(cell[0]), int(cell[1]))))
						animated_actors[str(token.character_id)].move_visual(grid.grid_to_world(Vector2i(int(data.position.cell_x), int(data.position.cell_y))), false, points)
			_received("workspace", workspace)
		_poll()
		return
	if key == "effect":
		retry_button.hide()
		command_inflight = false
		var action = str(pending_intent.get("payload", {}).get("action", ""))
		pending_intent.clear()
		combat_state = data if data is Dictionary else {}
		battle.sync()
		if action in ["dorn_guard", "dorn_spell_cast"]:
			panel.hide()
			dorn.play_action("guard" if action == "dorn_guard" else "cast")
		status.text = "Guarda ativada" if action == "dorn_guard" else ("Relâmpago resolvido · resultado no Registro" if action == "dorn_spell_cast" else "Combate atualizado")
		status.show()
		if action in ["dorn_spell_cast", "dorn_diagnose"] and data.get("protocol_result") is Dictionary:
			status.text = powers.dorn_outcome(data.protocol_result)
		elif action == "dorn_vanguard":
			status.text = "Protocolo de Vanguarda ativado"
		_cancel_targeting()
		_poll()
		return
	if key == "place":
		command_inflight = false
		pending_intent.clear()
		first_map = true
		_poll()
		return
	if key == "lightning-contract":
		if data is Dictionary and data.get("contract") is Dictionary:
			targeting = data.contract
			target_ids.clear()
			grid.range_m = float(targeting.get("range", {}).get("meters", 0))
			for token in workspace.get("tokens", []):
				if token.get("character_id") == "dorn7" and token.get("grid_position") is Dictionary:
					grid.range_origin = Vector2i(int(token.grid_position.cell_x), int(token.grid_position.cell_y))
			grid.queue_redraw()
			panel.hide()
			status.text = "Relâmpago · clique em um alvo no mapa"
			status.show()
		return
	if key.begins_with("map:"):
		if key == "map:" + requested_map and data is Dictionary:
			panel.hide()
			map_viewer.present(data, characters, master)
		return
	if key.begins_with("session:"):
		if key == "session:" + str(session_id) and data is Dictionary:
			selected_session = data
			if active_panel == "sessions":
				_render_panel()
		return
	if key.begins_with("sheet:"):
		if not data is Dictionary or str(data.get("definition", {}).get("id", "")) != selected_id:
			return
		sheet = data
		if selected_id=="dorn7":battle_overlay.set_attacks(data.get("definition",{}))
		if panel.visible and active_panel in ["sheet", "attacks", "spells", "items"]:
			_render_panel()
		return
	match key:
		"health":
			if not data is Dictionary or not data.has("access_mode"):
				_failed(key, "Identidade do acesso inválida.", 0)
				return
			master = data.access_mode == "gm"
			my_profile = str(data.get("player_profile_id", "")) if not master else ""
			selected_id = ""
			nav.set_master(master)
			authenticated = true
			local_preview = false
			connection.hide()
			token_input.clear()
			connect_button.disabled = false
			status.hide()
			api.request_json("characters", "/characters?read_only=true")
			api.request_json("maps", "/workspace/maps")
			api.request_json("sessions", "/sessions")
			_poll()
		"characters":
			if not data is Array:
				return
			characters = data
			_sync_online()
		"workspace":
			if battle.on_workspace(data):
				return
			if not data is Dictionary:
				return
			workspace = data
			presence = data.get("presence", [])
			_sync_online()
			var map: Dictionary = data.get("map") if data.get("map") is Dictionary else {}
			var geometry: Dictionary = map.get("grid", {})
			grid.configure_grid(geometry, data.get("tokens", []))
			_sync_actor_sprites(data, geometry)
			grid.set_city_near(_city_near())
			first_map = false
			map_label.text = "Arredores de Nimalis"
			town.after_exploration(data)
			hud.render()
			battle.watch_exploration(data)
			var own_missing = not master and animated_actors.has(my_profile) and not animated_actors[my_profile].visible
			if own_missing:
				status.text = "Seu personagem não está neste mapa. A ficha está disponível; o Mestre precisa posicioná-lo."
				status.show()
			elif missing_actor_notice:
				status.hide()
			missing_actor_notice = own_missing
		"presence":
			# The heartbeat reply is not a roster. Refresh the native snapshot.
			api.request_json("workspace", "/workspace")
		"maps":
			if data is Array:
				maps = data
				if active_panel == "maps":
					_render_panel()
		"scenes":
			if data is Array:
				scenes = data
				if active_panel == "scenes": _render_panel()
		"sessions":
			if data is Array:
				sessions = data
				if active_panel == "sessions":
					_render_panel()
		"ledger":
			if not data is Array:
				return
			ledger = data
			var lines = PackedStringArray()
			for event in ledger.slice(maxi(0, ledger.size() - 4)):
				lines.append(str(event.get("title", "")))
			var fresh = "\n".join(lines)
			if fresh != recent.text and not fresh.is_empty():
				# New table events float above the chat box for a few seconds, like a game chat.
				recent.text = fresh
				_place_recent()
				recent.show()
				recent_serial += 1
				var serial = recent_serial
				get_tree().create_timer(10.0).timeout.connect(func(): if serial == recent_serial and not log_box.get_global_rect().has_point(get_viewport().get_mouse_position()): recent.hide())
			if active_panel == "log":
				_render_panel()
		"message":
			message_input.editable = true
			message_input.clear()
			api.request_json("ledger", "/workspace/ledger?limit=80")
		"combat":
			combat_state = data if data is Dictionary else {}
			battle.on_combat()
			if active_panel == "combat":
				_render_panel()

func _failed(key: String, message: String, code: int) -> void:
	for controller in controllers:
		if controller.failed(key, message, code):
			return
	if key in ["move", "effect", "place", "scene-selection", "arena-resolve", "arena-confirm", "arena-technique", "arena-add", "arena-grid", "encounter-grid"]:
		command_inflight = false
		var network = keeper.network_error(code)
		if not network:
			pending_intent.clear()
		retry_button.visible = network and not pending_intent.is_empty() and key != "place"
		if key == "place":
			pending_intent.clear()
		_poll()
	status.text = message
	status.show()
	connect_button.disabled = false
	if code == 401 or code == 403:
		api.configure(api.base_url, "")
		media.configure(api.base_url, "")
		map_viewer.clear()
		detail_panel.hide()
		maps.clear()
		sessions.clear()
		selected_session.clear()
		authenticated = false
		master = false
		nav.set_master(false)
		characters.clear()
		presence.clear()
		workspace.clear()
		grid.configure_grid({}, [])
		dorn.snap_visual(grid.grid_to_world(Vector2i(6, 6)))
		morthak.snap_visual(grid.grid_to_world(Vector2i(7, 6)))
		morthak.visible = false
		sprite_map_id = ""
		camera.position = dorn.position
		sheet.clear()
		ledger.clear()
		recent.text = ""
		roster.update_roster([], [])
		for controller in controllers: controller.clear()
		panel.hide()
		connection.show()
		local_preview = true
		dorn.visible = true
		dorn.preview = true
	if key == "health":
		connection.show()
	if key.begins_with("sheet:") and panel.visible:
		_clear_body()
		_label(body, message)
		var retry = Button.new()
		retry.text = "Tentar novamente"
		retry.pressed.connect(_load_sheet)
		body.add_child(retry)
	if key == "message":
		message_input.editable = true
		status.text = "Entrega não confirmada. Confira o Registro antes de reenviar."

func _load_sheet() -> void:
	if authenticated and not selected_id.is_empty():
		if str(sheet.get("definition", {}).get("id", "")) != selected_id:
			sheet.clear()
		api.request_json("sheet:" + selected_id, "/characters/" + selected_id.uri_encode() + "?read_only=true")

func _open_panel(name: String) -> void:
	if name in ["gm", "library", "scenes"] and not master:
		return
	if not authenticated:
		connection.show()
		return
	if name == "city":
		town.open_city()
		return
	if active_panel == name and panel.visible:
		panel.hide()
		active_panel = ""
		return
	active_panel = name
	_layout()
	requested_map = ""
	map_viewer.hide()
	detail_panel.hide()
	panel.show()
	if str(sheet.get("definition", {}).get("id", "")) != selected_id:
		sheet.clear()
	_render_panel()
	if name in ["sheet", "attacks", "spells", "items"]:
		_load_sheet()
	if name == "combat":
		api.request_json("combat", "/combat/effects")
	if name == "maps":
		api.request_json("maps", "/workspace/maps")
	if name == "scenes" and master:
		api.request_json("scenes", "/scenes")
		studio.open()
	if name == "library" and master:
		library.open()
	if name == "dice":
		dice.open()
	if name == "sessions":
		session_id = -1
		selected_session.clear()
		api.request_json("sessions", "/sessions")

func _clear_body() -> void:
	for child in body.get_children():
		body.remove_child(child)
		child.queue_free()

func _render_panel() -> void:
	_clear_body()
	var names = {"sheet": "Ficha", "attacks": "Ataques", "spells": "Poderes",
		"items": "Inventário", "maps": "Mapas", "combat": "Combate", "log": "Registro", "sessions": "Sessões", "gm": "Mestre", "scenes": "Preparar sessão", "library": "Biblioteca do Mestre", "dice": "Dados e testes"}
	title.text = names.get(active_panel, "")
	character_select.visible = active_panel in ["sheet", "attacks", "spells", "items"] and character_select.item_count > 0
	for index in range(character_select.item_count):
		if str(character_select.get_item_metadata(index)) == selected_id:
			character_select.select(index)
	var definition: Dictionary = sheet.get("definition", {})
	var state: Dictionary = sheet.get("state") if sheet.get("state") is Dictionary else {}
	match active_panel:
		"sheet", "attacks", "spells", "items":
			if selected_id.is_empty():
				_label(body, "Nenhuma ficha disponível para este acesso.")
			elif definition.is_empty():
				_label(body, "Carregando ficha…")
			elif active_panel == "sheet":
				if master and _actor_pin().is_empty():
					var place = Button.new()
					place.text = "Colocar este personagem no mapa"
					place.custom_minimum_size.y = 46
					place.pressed.connect(_place_dorn)
					body.add_child(place)
				content.ficha(body, definition, state, sheet.get("inventory", []), morthak.sheet_preview() if selected_id == "morthak" else null)
				progress.render(body, selected_id, definition)
			elif active_panel in ["attacks", "spells"]:
				# One informational place for everything the character can do; the bar choice sits on top.
				powers.render(body, selected_id, definition, state)
				if not (definition.get("attacks", []) as Array).is_empty():
					_label(body, "Ataques")
					content.attacks(body, definition)
				if not (definition.get("session_abilities", []) as Array).is_empty():
					_label(body, "Magias e habilidades")
					content.spells(body, definition, state)
			else:
				content.inventory(body, sheet.get("inventory", []))
		"editor":
			if not grid.terrain or (authenticated and not master): return
			# Full-screen editor (whole terrain, every tool); the old side panel stays below as a fallback.
			panel.hide()
			active_panel = ""
			map_editor.open()
			return
		"maps":
			content.maps(body, maps, master)
		"sessions":
			if not selected_session.is_empty():
				var back = Button.new()
				back.text = "Sessões"
				back.icon = load("res://assets/ui/sessions.svg")
				back.pressed.connect(func(): session_id = -1; selected_session.clear(); _render_panel())
				body.add_child(back)
				content.session_detail(body, selected_session, master)
				if master: _session_controls(selected_session)
			else:
				content.sessions(body, sessions)
		"log":
			for event in ledger.slice(maxi(0, ledger.size() - 80)):
				_label(body, str(event.get("title", "")))
		"combat":
			battle.render_panel(body)
		"preparation":
			if not master: return
			title.text = "Preparação"
			preparation.render(body,content,_open_map,_confirm_preparation)
		"dice":
			dice.render(body)
		"library":
			if master: library.render(body)
		"scenes":
			if not master: return
			studio.render(body)
			var shelf = Button.new()
			shelf.text = "Biblioteca: monstros, NPCs, itens, magias, mapas"
			shelf.custom_minimum_size.y = 44
			shelf.pressed.connect(func(): _open_panel("library"))
			body.add_child(shelf)
			for record in scenes:
				content.card(body,str(record.get("title","Cena")),record.get("image_path"),str(record.get("summary",record.get("description",""))),func(): _open_preparation(record),"sessions")
		"gm":
			if not master: return
			for entry in [["sessions","Sessões"],["scenes","Preparar sessão (roteiro, NPCs, monstros, itens, mapas)"],["library","Biblioteca (monstros, NPCs, itens, magias)"],["combat","Combate e turnos"],["maps","Biblioteca de mapas"],["sheet","Personagens"],["log","Registro da sessão"],["editor","Editor de terreno"]]:
				var destination: String = entry[0]
				var button = Button.new()
				button.text = entry[1]
				button.icon = load("res://assets/ui/"+destination+(".svg" if destination == "editor" else ".png")) if destination not in ["log", "scenes", "library"] else load("res://assets/ui/sessions.png")
				button.pressed.connect(func(): _open_panel(destination))
				body.add_child(button)
			var city_row = HBoxContainer.new()
			body.add_child(city_row)
			if grid.city_token.is_empty():
				var place_city = Button.new()
				place_city.text = "Colocar " + str(town.config.get("title", "a cidade")) + " no mapa (onde o Dorn está)"
				place_city.pressed.connect(_place_city)
				city_row.add_child(place_city)
			else:
				var open_city = Button.new()
				open_city.text = ("Fechar " if grid.city_token.get("visible_to_players", false) else "Abrir ") + str(grid.city_token.get("name", "a cidade")) + " para os jogadores"
				open_city.pressed.connect(_toggle_city)
				city_row.add_child(open_city)
				var move_city = Button.new()
				move_city.text = "Mover a cidade"
				move_city.tooltip_text = "Depois clique no mapa onde a cidade fica de vez."
				move_city.pressed.connect(func():
					moving_pin = grid.city_token
					panel.hide()
					_notice("Clique no mapa onde a cidade deve ficar."))
				city_row.add_child(move_city)
			progress.render_gm(body)
			character_select.visible = character_select.item_count > 0
			progress.render_gm_progress(body)
			if not selected_session.is_empty(): _session_controls(selected_session)
	if body.get_child_count() == 0:
		_label(body, "Nenhum registro disponível.")

func _sync_online() -> void:
	var online = Roster.online_characters(characters, presence)
	var ids: Array = characters.map(func(character: Dictionary): return str(character.id))
	var previous = selected_id
	if not selected_id in ids:
		selected_id = my_profile if my_profile in ids else ("dorn7" if master and "dorn7" in ids else (str(ids[0]) if not ids.is_empty() else ""))
		sheet.clear()
		detail_panel.hide()
	character_select.clear()
	for character in characters:
		character_select.add_item(str(character.name))
		character_select.set_item_metadata(character_select.item_count - 1, character.id)
		if str(character.id) == selected_id:
			character_select.select(character_select.item_count - 1)
	roster.controlled_id = selected_id if master or selected_id == my_profile else my_profile
	roster.update_roster(characters, presence)
	_layout()
	if previous != selected_id:
		for profile in animated_actors:
			if animated_actors[profile].preview:
				animated_actors[profile].visible = master and profile == selected_id
		if animated_actors.has(selected_id) and master and _actor_pin().is_empty():
			animated_actors[selected_id].visible = true
			animated_actors[selected_id].preview = true
		if panel.visible and active_panel in ["sheet", "attacks", "spells", "items"]:
			_render_panel()
		_load_sheet()

func _selected_visual() -> Node2D:
	return animated_actors.get(selected_id, dorn)

func _sync_actor_sprites(data: Dictionary, geometry: Dictionary) -> void:
	var map_id = str(data.get("map", {}).get("id", ""))
	for profile in animated_actors:
		var actor = animated_actors[profile]
		var previously_visible: bool = actor.visible and not actor.preview
		actor.visible = false
		actor.cell_size_m = float(geometry.get("cell_size_m", 1))
		actor.distance_rule = str(geometry.get("distance_rule", "chebyshev"))
		actor.selected = selected_id == profile
		for token in data.get("tokens", []):
			if token.get("character_id", "") != profile or not token.get("grid_position") is Dictionary:
				continue
			var pos: Dictionary = token.grid_position
			var point = grid.grid_to_world(Vector2i(int(pos.cell_x), int(pos.cell_y)))
			actor.visible = true
			actor.preview = false
			actor.visible_name = str(token.get("name", profile))
			if first_map or sprite_map_id != map_id or not previously_visible:
				actor.snap_visual(point)
				if not master and profile == my_profile:
					camera.position = point
			else:
				actor.move_visual(point)
			break
		if not actor.visible and master and selected_id == profile:
			actor.visible = true
			actor.preview = true
	if first_map and _selected_visual().visible:
		camera.position = _selected_visual().position
	sprite_map_id = map_id
	local_preview = not authenticated or (master and _selected_visual().preview)

func _open_map(id: String) -> void:
	requested_map = id
	api.request_json("map:" + id, "/workspace?map_id=" + id.uri_encode())

func _open_session(id: int) -> void:
	session_id = id
	selected_session.clear()
	api.request_json("session:" + str(id), "/sessions/" + str(id))

## 12.0 -> "12" (the API returns JSON numbers as floats).
static func _fmt(value: Variant) -> String:
	if value is float and is_equal_approx(value, roundf(value)): return str(int(value))
	return str(value)

func _show_pin(pin: Dictionary) -> void:
	var info = pin.get("sheet", {}).duplicate(true)
	info.name = pin.get("name", "Pin")
	info.image_path = pin.get("image_path")
	info.description = str(info.get("description", ""))
	if pin.get("maximum_hp") and master:
		info.description += "\nVida %s / %s" % [_fmt(pin.get("current_hp", "—")), _fmt(pin.get("maximum_hp", "—"))]
	_show_detail(info)
	if master and pin.get("id"):
		_pin_controls(pin)
	if master and pin.get("token_type") == "monster" and pin.get("id"):
		_disposition_controls(pin)
	pins.shown(pin)

## GM pin tools during play: reveal/hide, HP and removal (pins from the Library start hidden).
func _pin_controls(pin: Dictionary) -> void:
	var id = str(pin.id).uri_encode()
	var shown = bool(pin.get("visible_to_players", false))
	_label(detail_body, "Jogadores: " + ("veem este marcador" if shown else "não veem (oculto)"), 13)
	var row = HFlowContainer.new()
	detail_body.add_child(row)
	var reveal = Button.new()
	reveal.text = "Ocultar" if shown else "Revelar"
	reveal.pressed.connect(func():
		api.request_json("pin-edit", "/gm/workspace/tokens/" + id, HTTPClient.METHOD_PATCH, {"visible_to_players": not shown})
		detail_panel.hide())
	row.add_child(reveal)
	if pin.get("token_type") != "location":
		var edit = Button.new()
		edit.text = "Editar ficha"
		edit.pressed.connect(func(): _pin_editor(pin))
		row.add_child(edit)
	if pin.get("token_type") in ["monster", "npc"] and pin.get("maximum_hp"):
		var current = int(pin.get("current_hp", pin.maximum_hp))
		for delta in [-5, -1, 1, 5]:
			var button = Button.new()
			button.text = "PV %+d" % delta
			button.pressed.connect(func():
				var value = clampi(current + delta, 0, int(pin.maximum_hp))
				api.request_json("pin-edit", "/gm/workspace/tokens/" + id, HTTPClient.METHOD_PATCH, {"current_hp": value})
				detail_panel.hide())
			row.add_child(button)
	var move = Button.new()
	move.text = "Mover"
	move.tooltip_text = "Depois clique no mapa onde ele deve ficar (vale para a cidade também)."
	move.pressed.connect(func():
		moving_pin = pin
		detail_panel.hide()
		_notice("Clique no mapa onde \"%s\" deve ficar." % str(pin.get("name", "marcador"))))
	row.add_child(move)
	var remove = Button.new()
	remove.text = "Remover do mapa"
	remove.pressed.connect(func():
		confirm_remove_pin.dialog_text = "Remover \"%s\" deste mapa?" % str(pin.get("name", "marcador"))
		remove_pin_id = id
		confirm_remove_pin.popup_centered(Vector2i(360, 150)))
	row.add_child(remove)

## GM quick editor for a map marker: name, life, AC and description (the rest of the sheet is kept).
func _pin_editor(pin: Dictionary) -> void:
	for child in detail_body.get_children():
		detail_body.remove_child(child)
		child.queue_free()
	detail_title.text = "Editar · " + str(pin.get("name", ""))
	var sheet_data: Dictionary = pin.get("sheet", {}).duplicate(true) if pin.get("sheet") is Dictionary else {}
	var grid_box = GridContainer.new()
	grid_box.columns = 2
	detail_body.add_child(grid_box)
	var fields: Dictionary = {}
	for spec in [["name", "Nome", str(pin.get("name", ""))], ["current_hp", "Vida atual", pin.get("current_hp")], ["maximum_hp", "Vida máxima", pin.get("maximum_hp")], ["armor_class", "CA", sheet_data.get("armor_class")]]:
		_label(grid_box, spec[1], 14)
		if spec[0] == "name":
			var line = LineEdit.new()
			line.text = spec[2]
			line.custom_minimum_size.x = 200
			grid_box.add_child(line)
			fields[spec[0]] = line
		else:
			var number = SpinBox.new()
			number.min_value = 0
			number.max_value = 9999
			number.value = int(spec[2]) if spec[2] != null and str(spec[2]).is_valid_int() or spec[2] is float or spec[2] is int else 0
			grid_box.add_child(number)
			fields[spec[0]] = number
	_label(detail_body, "Descrição", 14)
	var description = TextEdit.new()
	description.custom_minimum_size = Vector2(0, 120)
	description.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	description.text = str(sheet_data.get("description", ""))
	detail_body.add_child(description)
	var save = Button.new()
	save.text = "Salvar"
	save.custom_minimum_size.y = 40
	save.pressed.connect(func():
		sheet_data["armor_class"] = int(fields.armor_class.value)
		sheet_data["description"] = description.text.left(4000)
		var body_data = {"name": fields.name.text.strip_edges().left(120), "sheet": sheet_data}
		if pin.get("maximum_hp") != null or fields.maximum_hp.value > 0:
			body_data["maximum_hp"] = maxi(1, int(fields.maximum_hp.value))
			body_data["current_hp"] = clampi(int(fields.current_hp.value), 0, body_data.maximum_hp)
		if body_data.name == "": body_data.erase("name")
		api.request_json("pin-edit", "/gm/workspace/tokens/" + str(pin.id).uri_encode(), HTTPClient.METHOD_PATCH, body_data)
		detail_panel.hide())
	detail_body.add_child(save)
	call_deferred("_fit_drawers")

## GM marker used by proximity encounters and by the battle sides.
func _disposition_controls(pin: Dictionary) -> void:
	var current = str(pin.get("sheet", {}).get("disposition", "")) if pin.get("sheet") is Dictionary else ""
	_label(detail_body, "Disposição: " + {"hostile": "hostil", "neutral": "neutra", "ally": "aliada"}.get(current, "automática (tem ataques = hostil)"), 13)
	var row = HFlowContainer.new()
	detail_body.add_child(row)
	for entry in [["hostile", "Hostil"], ["neutral", "Neutro"], ["ally", "Aliado"], ["", "Automático"]]:
		var choice: String = entry[0]
		var button = Button.new()
		button.text = entry[1]
		button.disabled = choice == current
		button.pressed.connect(func():
			api.request_json("disposition", "/gm/workspace/tokens/" + str(pin.id).uri_encode() + "/disposition", HTTPClient.METHOD_PATCH, {"disposition": choice if choice != "" else null})
			detail_panel.hide())
		row.add_child(button)

func _show_detail(record: Dictionary) -> void:
	for child in detail_body.get_children():
		detail_body.remove_child(child)
		child.queue_free()
	detail_title.text = str(record.get("name", "Detalhes"))
	var art = record.get("image_path")
	if art:
		var picture = content.image(detail_body, art, 140)
		media.bind(art, picture, "texture", 768)
	if record.get("description"):
		_label(detail_body, str(record.description))
	for pair in [["armor_class", "CA"], ["saving_throw", "JP"], ["hit_dice", "DV"], ["movement", "Movimento"], ["damage_formula", "Dano"], ["charges_current", "Cargas"], ["quantity", "Quantidade"]]:
		if record.get(pair[0]) != null:
			_label(detail_body, pair[1] + "  " + _fmt(record[pair[0]]))
	if record.get("attacks") is Array:
		for attack in record.attacks:
			if attack is Dictionary:
				_label(detail_body, str(attack.get("name", "Ataque")) + " · " + str(attack.get("damage", attack.get("damage_formula", ""))))
	if record.get("equipped", false):
		_label(detail_body, "Equipado · " + str(record.get("equipment_slot", "")))
	if record.get("blocked", false):
		_label(detail_body, str(record.get("blocked_reason", "Indisponível nas regras atuais.")))
	if record.get("source"):
		_label(detail_body, str(record.source), 12)
	detail_panel.show()

func _send_message(text: String) -> void:
	if not authenticated or not message_input.editable or text.strip_edges().is_empty():
		return
	message_input.editable = false
	last_message = text.strip_edges().substr(0, 2000)
	api.request_json("message", "/workspace/messages", HTTPClient.METHOD_POST, {"text": last_message})

func _actor_pin() -> Dictionary:
	for token in workspace.get("tokens", []):
		if token.get("character_id") == selected_id:
			return token
	return {}

func _place_recent() -> void:
	recent.reset_size()
	recent.size.x = log_box.size.x - 8
	var above = status.size.y + 4 if status.visible else 0.0
	recent.position = Vector2(log_box.position.x + 4, log_box.position.y - 6 - above - recent.get_combined_minimum_size().y)

func _notice(text: String) -> void:
	status.text = text
	status.show()
	status.reset_size()
	status.size.x = log_box.size.x - 8
	status.position = Vector2(log_box.position.x + 4, log_box.position.y - 6 - status.get_combined_minimum_size().y)
	notice_serial += 1
	var serial = notice_serial
	get_tree().create_timer(9.0).timeout.connect(func(): if serial == notice_serial: status.hide())

func _send_intent(key: String, intent: Dictionary) -> void:
	if command_inflight:
		return
	if not pending_intent.is_empty():
		_notice("Confira ou reenvie o comando pendente antes de outra ação.")
		retry_button.show()
		return
	command_inflight = true
	pending_intent = intent.duplicate(true)
	pending_intent.key = key
	api.request_json(key, str(intent.path), HTTPClient.METHOD_POST, intent.payload)

func _send_effect(action: String, payload: Dictionary) -> void:
	if not combat_state.has("version"):
		api.request_json("combat", "/combat/effects")
		_notice("Carregando o estado do combate…")
		return
	_send_intent("effect", {"path": "/combat/next-turn" if action == "next_turn" else "/gm/combat/effects", "payload": {
		"request_id": "godot-effect-" + Crypto.new().generate_random_bytes(12).hex_encode(),
		"expected_version": int(combat_state.version), "action": action, "payload": payload}})

## A hero of this client (any hero for the GM) stands within 3 cells of the city sprite.
func _city_near() -> bool:
	if grid.city_token.is_empty(): return false
	for token in workspace.get("tokens", []):
		if not token.get("character_id"): continue
		if not master and str(token.character_id) != my_profile: continue
		var at = grid.token_cell(token)
		if maxi(absi(at.x - grid.city_cell.x), absi(at.y - grid.city_cell.y)) <= 3: return true
	return false

## GM: put the city sprite where Dorn stands (Nimalis), hidden until opened to the players.
func _place_city() -> void:
	var anchor = _actor_pin() if selected_id == "dorn7" else {}
	for token in workspace.get("tokens", []):
		if token.get("character_id") == "dorn7": anchor = token
	if anchor.is_empty() or grid.token_cell(anchor).x < -50:
		_notice("Coloque o Dorn no mapa: a cidade aparece onde ele está.")
		return
	var geometry: Dictionary = workspace.map.get("grid", {}) if workspace.map.get("grid") is Dictionary else {}
	var cols = maxi(1, int(geometry.get("cols", 20)))
	var rows = maxi(1, int(geometry.get("rows", 20)))
	var origin = Vector2(float(geometry.get("origin_x", 0)), float(geometry.get("origin_y", 0)))
	var anchor_cell = grid.token_cell(anchor)
	var cell = Vector2i(clampi(anchor_cell.x + 1, 0, cols - 1), clampi(anchor_cell.y - 1, 0, rows - 1))
	api.request_json("city-place", "/gm/workspace/tokens", HTTPClient.METHOD_POST, {
		"token_type": "location", "name": str(town.config.get("title", "Nimalis")), "map_id": str(workspace.map.id),
		"latitude": origin.y + (cell.y + 0.5) * (100.0 - origin.y) / rows, "longitude": origin.x + (cell.x + 0.5) * (100.0 - origin.x) / cols,
		"visible_to_players": false, "color": "#c9a45a", "sheet": {"kind": "city", "city_map_id": town.city_map_id(), "marker": "⌂"}})

func _toggle_city() -> void:
	var city = grid.city_token
	if city.is_empty(): return
	api.request_json("city-toggle", "/gm/workspace/tokens/" + str(city.id).uri_encode(), HTTPClient.METHOD_PATCH,
		{"visible_to_players": not city.get("visible_to_players", false)})

var moving_pin: Dictionary = {}

## GM: put a pin (monster, NPC, city...) on another cell.
func _move_pin_to(pin: Dictionary, cell: Vector2i) -> void:
	var geometry: Dictionary = workspace.map.get("grid", {}) if workspace.get("map") is Dictionary and workspace.map.get("grid") is Dictionary else {}
	var cols = maxi(1, int(geometry.get("cols", 20)))
	var rows = maxi(1, int(geometry.get("rows", 20)))
	var origin = Vector2(float(geometry.get("origin_x", 0)), float(geometry.get("origin_y", 0)))
	api.request_json("pin-edit", "/gm/workspace/tokens/" + str(pin.id).uri_encode() + "/position", HTTPClient.METHOD_PATCH, {
		"latitude": clampf(origin.y + (cell.y + 0.5) * (100.0 - origin.y) / rows, 0, 100),
		"longitude": clampf(origin.x + (cell.x + 0.5) * (100.0 - origin.x) / cols, 0, 100)})

func _click_cell(cell: Vector2i) -> void:
	if master and not moving_pin.is_empty():
		_move_pin_to(moving_pin, cell)
		moving_pin = {}
		return
	if combat_state.get("encounter",{}).get("active",false) and combat_state.get("encounter",{}).get("battle_mode",false):return
	if grid.city_hit(cell) and active_panel != "editor":
		if _city_near() or master:
			town.open_city()
		else:
			_notice("Chegue mais perto de " + str(grid.city_token.get("name", "cidade")) + " para entrar.")
		return
	if active_panel == "editor" and grid.terrain and (master or not authenticated):
		grid.terrain.paint(cell, editor_brush)
		return
	grid.selected = cell
	grid.queue_redraw()
	for token in workspace.get("tokens", []):
		var pos: Dictionary = token.get("grid_position", {})
		if int(pos.get("cell_x", -1)) != cell.x or int(pos.get("cell_y", -1)) != cell.y:
			continue
		if not targeting.is_empty() and token.get("character_id") != "dorn7" and token.get("token_type") != "location":
			if token.id in target_ids:
				confirm_action.dialog_text = "Aplicar Relâmpago em %d alvo(s)?" % target_ids.size()
				confirm_action.popup_centered(Vector2i(340, 150))
			else:
				target_ids.append(token.id)
				_notice("Relâmpago · %d/3 · toque novamente no selecionado para concluir" % target_ids.size())
				if target_ids.size() == 3:
					confirm_action.dialog_text = "Aplicar Relâmpago em 3 alvos?"
					confirm_action.popup_centered(Vector2i(340, 150))
			return
		if token.get("character_id"):
			selected_id = str(token.character_id)
			_sync_online()
			_load_sheet()
			return
	if not targeting.is_empty():
		return
	if authenticated and (master or selected_id == my_profile):
		if grid.blocked.has(cell):
			_notice("Não dá para ficar aí: árvore ou construção.")
			return
		var intent = Commands.move(workspace, selected_id, cell, combat_state, grid.blocked)
		if not intent.is_empty() and (intent.payload.path as Array).is_empty():
			_notice("Não há caminho livre até lá.")
			return
		if not intent.is_empty():
			_send_intent("move", intent)
			return
	if not authenticated and (selected_id.is_empty() or animated_actors.has(selected_id)):
		var actor = _selected_visual()
		actor.preview = true
		actor.visible = true
		actor.move_visual(grid.grid_to_world(cell), true)
		_notice("Prévia local de " + actor.visible_name + " · sem alterar a mesa")

func _activate_ability(ability: Dictionary) -> void:
	var id = str(ability.get("id", ""))
	if selected_id == "dorn7" and id in ["dorn_guard", "relampago"]:
		if _actor_pin().is_empty():
			panel.hide()
			camera.position = dorn.position
			dorn.visible = true
			dorn.play_action("guard" if id == "dorn_guard" else "cast")
			_notice("Teste visual local · sem gastar recursos")
		elif not master:
			_notice("Dorn é controlado pelo Mestre neste cadastro.")
		elif id == "dorn_guard":
			_send_effect("dorn_guard", {})
		else:
			api.request_json("lightning-contract", "/gm/actions/describe?ref=technique%3Adorn7%3Arelampago")
	else:
		_show_detail(ability)

func _cancel_targeting() -> void:
	targeting.clear()
	target_ids.clear()
	grid.range_m = 0
	grid.queue_redraw()

func _place_dorn() -> void:
	if not master or not _actor_pin().is_empty() or not workspace.get("map") is Dictionary:
		return
	var cell = grid.world_to_grid(_selected_visual().position)
	var geometry: Dictionary = workspace.map.get("grid", {})
	var cols = maxi(1, int(geometry.get("cols", grid.cols)))
	var rows = maxi(1, int(geometry.get("rows", grid.rows)))
	if not animated_actors.has(selected_id):
		cell.x += maxi(1, character_select.selected)
	cell = Vector2i(clampi(cell.x, 0, cols - 1), clampi(cell.y, 0, rows - 1))
	var origin = Vector2(float(geometry.get("origin_x", 0)), float(geometry.get("origin_y", 0)))
	_send_intent("place", {"path": "/gm/workspace/tokens", "payload": {
		"token_type": "character", "character_id": selected_id, "name": selected_id, "map_id": workspace.map.id,
		"latitude": origin.y + (cell.y + 0.5) * (100.0 - origin.y) / rows,
		"longitude": origin.x + (cell.x + 0.5) * (100.0 - origin.x) / cols,
		"visible_to_players": true}})

func _preview_controls(parent: Node) -> void:
	_label(parent, "Prévias visuais · não gastam recursos", 13)
	var row = HBoxContainer.new()
	parent.add_child(row)
	for action in [["guard", "Testar Guarda"], ["cast", "Testar Relâmpago"]]:
		var button = Button.new()
		button.text = action[1]
		_bind_ability_art(button, "dorn_guard" if action[0] == "guard" else "relampago")
		button.expand_icon = true
		button.add_theme_constant_override("icon_max_width", 34)
		button.custom_minimum_size.y = 48
		button.pressed.connect(func():
			panel.hide()
			camera.position = dorn.position
			dorn.visible = true
			dorn.play_action(action[0])
			_notice("Prévia visual local · " + action[1])
		)
		row.add_child(button)

func _dorn_controls(parent: Node) -> void:
	var row = HBoxContainer.new()
	parent.add_child(row)
	for spec in [["dorn_guard", "Guarda", "guard"], ["relampago", "Relâmpago", "cast"]]:
		var button = Button.new()
		button.text = ("Testar " if _actor_pin().is_empty() else "Usar ") + spec[1]
		_bind_ability_art(button, spec[0])
		button.expand_icon = true
		button.add_theme_constant_override("icon_max_width", 28)
		button.custom_minimum_size.y = 50
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.pressed.connect(func(): _activate_ability({"id": spec[0]}))
		row.add_child(button)

func _bind_ability_art(button: Button, id: String) -> void:
	button.icon = load("res://assets/ui/combat.svg" if id == "dorn_guard" else "res://assets/ui/spells.svg")
	for ability in sheet.get("definition", {}).get("session_abilities", []):
		if ability.get("id") == id:
			media.bind(ability.get("image_path"), button, "icon")
			break

func _zoom(factor: float) -> void:
	var old = get_global_mouse_position()
	camera.zoom = Vector2.ONE * clampf(camera.zoom.x * factor, 0.45, 2.5)
	camera.position += old - get_global_mouse_position()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			_zoom(1.12)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			_zoom(0.89)
		elif event.button_index == MOUSE_BUTTON_LEFT or event.button_index == MOUSE_BUTTON_MIDDLE:
			dragging = event.pressed
			if event.pressed:
				drag_start = event.position
				drag_distance = 0
			elif drag_distance < 10:
				var cell = grid.world_to_grid(get_canvas_transform().affine_inverse() * event.position)
				if grid.is_cell_valid(cell) or (active_panel == "editor" and grid.terrain):
					_click_cell(cell)

	if event is InputEventMouseMotion and dragging:
		drag_distance += event.relative.length()
		camera.position -= event.relative / camera.zoom
	if event is InputEventMagnifyGesture:
		_zoom(event.factor)
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		if detail_panel.visible:
			detail_panel.hide()
			return
		if map_viewer.visible:
			map_viewer.hide()
			return
		panel.hide()
		active_panel = ""

func _process(delta: float) -> void:
	if battle_overlay.visible:return
	if grid.terrain:
		var extent = Vector2(grid.terrain.model.width, grid.terrain.model.height) * 32
		var view = get_viewport_rect().size
		var minimum = maxf(view.x / extent.x, view.y / extent.y)
		camera.zoom = Vector2.ONE * maxf(camera.zoom.x, minimum)
		var half = view / camera.zoom / 2
		camera.position = camera.position.clamp(half, extent-half)
	if get_viewport().gui_get_focus_owner() is LineEdit or get_viewport().gui_get_focus_owner() is TextEdit:
		return
	var direction = Vector2(float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A)),
		float(Input.is_physical_key_pressed(KEY_S)) - float(Input.is_physical_key_pressed(KEY_W)))
	camera.position += direction.normalized() * delta * 350 / camera.zoom.x

func _smoke_test() -> void:
	for x in range(8):
		for y in range(8):
			var cell = Vector2i(x, y)
			assert(grid.world_to_grid(grid.grid_to_world(cell)) == cell)
	assert(dorn.sprite.sprite_frames.get_frame_count("idle") == 8)
	for direction in ["up", "down", "left", "right"]:
		assert(dorn.sprite.sprite_frames.get_frame_count("walk_" + direction) == 8)
	var old_camera = camera.position
	authenticated = true
	selected_id = "test"
	sheet = {"definition": {"id": "test", "name": "Ensaio", "attributes": {"strength": 13}}, "access_level": "owner"}
	_open_panel("sheet")
	assert(panel.visible)
	_open_panel("sheet")
	assert(not panel.visible)
	assert(camera.position == old_camera)
	selected_id = "test"
	_received("sheet:other", {"definition": {"id": "other", "name": "Resposta antiga"}})
	assert(sheet.definition.name == "Ensaio")
	_failed("workspace", "Acesso inválido.", 401)
	assert(grid.tokens.is_empty())
	assert(not authenticated)
	assert(dorn.position == grid.grid_to_world(Vector2i(6, 6)))
	nav.set_master(true)
	for viewport_size in [Vector2i(844, 390), Vector2i(740, 360), Vector2i(640, 320), Vector2i(1440, 900)]:
		get_window().size = viewport_size
		await get_tree().process_frame
		_layout()
		await get_tree().process_frame
		assert(nav.position.y >= 0)
		assert(nav.position.y + nav.size.y <= get_viewport_rect().size.y)
		assert(panel.position.y + panel.size.y <= get_viewport_rect().size.y)
		assert(connection.position.y + connection.size.y <= get_viewport_rect().size.y)
		assert(not nav.get_rect().intersects(status.get_rect()))
	print("COMPANION3_NATIVE_SMOKE_PASS")
	get_tree().quit()


func _session_controls(record: Dictionary) -> void:
	if not master or not record.has("id"): return
	var current = str(record.get("status", "planned"))
	var actions: Array = [["active", "Iniciar sessão"]] if current == "planned" else ([["active", "Retomar sessão"], ["completed", "Encerrar sessão"]] if current == "paused" else ([["paused", "Pausar sessão"], ["completed", "Encerrar sessão"]] if current == "active" else []))
	for action in actions:
		var next_status: String = action[0]
		var caption: String = action[1]
		var button = Button.new()
		button.text = caption
		button.pressed.connect(func():
			session_change = {"id": int(record.id), "status": next_status}
			confirm_session.dialog_text = caption+" — "+str(record.get("title", "Sessão"))+"?"
			confirm_session.popup_centered(Vector2i(340,160)))
		body.add_child(button)

func _commit_session_status() -> void:
	if not authenticated or not master or session_change.is_empty(): return
	api.request_json("session-status", "/gm/sessions/"+str(session_change.id)+"/status", HTTPClient.METHOD_POST, {"status":session_change.status})

func _open_preparation(record: Dictionary) -> void:
	if not master: return
	preparation.select(record)
	active_panel = "preparation"
	panel.show()
	_render_panel()
	api.request_json("preparation:"+str(record.id),"/scenes/"+str(record.id))

func _refresh_preparation() -> void:
	if master and panel.visible and active_panel=="preparation": _render_panel()

func _confirm_preparation() -> void:
	if not master or not authenticated or preparation.scene.is_empty(): return
	var selection = preparation.payload()
	if not selection.include_map and selection.element_ids.is_empty() and selection.token_ids.is_empty(): return
	selection.request_id = "godot-scene-"+Crypto.new().generate_random_bytes(12).hex_encode()
	preparation_intent = {"path":"/gm/scenes/"+str(preparation.scene.id)+"/selection-on-table","payload":selection}
	confirm_preparation.dialog_text = "Enviar à mesa %d elemento(s), %d pin(s)%s? Os selecionados serão revelados aos jogadores." % [selection.element_ids.size(),selection.token_ids.size()," e o mapa" if selection.include_map else ""]
	confirm_preparation.popup_centered(Vector2i(360,180))
