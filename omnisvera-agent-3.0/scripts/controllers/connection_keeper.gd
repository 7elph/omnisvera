extends Node
## Keeps the table playable when the Companion connection drops: shows a banner,
## retries with backoff, keeps the last state on screen and, once back, resends the
## pending command with the same request_id (the server replays it, never duplicates).
const POLL_KEYS = ["workspace", "arena-workspace", "combat", "ledger", "presence", "health"]
const BACKOFF = [3.0, 5.0, 10.0, 15.0, 30.0]
var host: Node
var offline: bool = false
var failures: int = 0
var attempt: int = 0
var since: String = ""
var last_ok_msec: int = 0
var banner = PanelContainer.new()
var label = Label.new()
var retry_now = Button.new()
var timer = Timer.new()
var countdown: float = 0

func setup(main: Node) -> void:
	host = main
	host.api.failed.connect(_on_failed)
	host.api.received.connect(_on_received)
	banner.z_index = 90
	banner.mouse_filter = Control.MOUSE_FILTER_STOP
	var row = HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	banner.add_child(row)
	label.add_theme_font_size_override("font_size", 14)
	row.add_child(label)
	retry_now.text = "Tentar agora"
	retry_now.pressed.connect(_try)
	row.add_child(retry_now)
	banner.hide()
	host.screen.add_child(banner)
	timer.one_shot = true
	timer.timeout.connect(_try)
	add_child(timer)

## Controller interface (nothing routed here; it only observes the transport).
func handles(_key: String) -> bool: return false
func received(_key: String, _data: Variant) -> void: pass
func failed(_key: String, _message: String, _code: int) -> bool: return false
func clear() -> void:
	offline = false
	failures = 0
	timer.stop()
	banner.hide()

static func network_error(code: int) -> bool:
	return code == 0 or code in [502, 503, 504]

func _on_failed(key: String, _message: String, code: int) -> void:
	if not host.authenticated and key != "health": return
	if not network_error(code): return
	failures += 1
	if failures >= 2 or not host.pending_intent.is_empty():
		_go_offline()

func _on_received(key: String, _data: Variant) -> void:
	last_ok_msec = Time.get_ticks_msec()
	failures = 0
	if offline and key in POLL_KEYS:
		_back_online()

func _go_offline() -> void:
	if not offline:
		offline = true
		attempt = 0
		since = Time.get_time_string_from_system().substr(0, 5)
	_schedule()

func _schedule() -> void:
	countdown = BACKOFF[mini(attempt, BACKOFF.size() - 1)]
	attempt += 1
	timer.start(countdown)
	_render()

func _try() -> void:
	timer.stop()
	label.text = "Conexão perdida desde " + since + " · reconectando…"
	if host.authenticated:
		host._poll()
	else:
		host.api.request_json("health", "/health")
	# If this attempt also fails, _on_failed schedules the next one.
	await get_tree().create_timer(4.0).timeout
	if offline and timer.is_stopped():
		_schedule()

func _back_online() -> void:
	offline = false
	timer.stop()
	label.text = "Reconectado · mesa atualizada"
	banner.show()
	_layout()
	host.api.request_json("characters", "/characters?read_only=true")
	host.api.request_json("maps", "/workspace/maps")
	if not host.pending_intent.is_empty() and not host.command_inflight:
		# Same key, path, payload and request_id: the server replays its receipt.
		host.command_inflight = true
		host.api.request_json(str(host.pending_intent.key), str(host.pending_intent.path), HTTPClient.METHOD_POST, host.pending_intent.payload)
		label.text = "Reconectado · reenviando a última ação"
	await get_tree().create_timer(3.0).timeout
	if not offline: banner.hide()

func _render() -> void:
	label.text = "Conexão perdida desde %s · o jogo continua com o último estado · nova tentativa em %ds" % [since, int(countdown)]
	if not host.pending_intent.is_empty():
		label.text += " · última ação guardada para reenviar"
	banner.show()
	_layout()

func _process(delta: float) -> void:
	if offline and not timer.is_stopped():
		var left = int(ceil(timer.time_left))
		if left != int(countdown):
			countdown = left
			_render()

func _layout() -> void:
	var view = host.get_viewport_rect().size
	banner.reset_size()
	var width = minf(view.x - 40, maxf(banner.get_combined_minimum_size().x, 360))
	banner.size = Vector2(width, 0)
	banner.position = Vector2((view.x - width) / 2, 8)
