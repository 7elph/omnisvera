extends Node
## Serialized authenticated transport. The token stays in memory.
signal received(key: String, payload: Variant)
signal failed(key: String, message: String, status: int)
var base_url: String = ""
var _token: String = ""
var _epoch: int = 0
var _queue: Array = []
var _pending: Dictionary = {}
var _busy: bool = false
var _active: HTTPRequest

func configure(url: String, credential: String) -> void:
	_epoch += 1
	_queue.clear()
	_pending.clear()
	_busy = false
	if is_instance_valid(_active):
		_active.cancel_request()
		_active.queue_free()
	_active = null
	base_url = url.trim_suffix("/")
	_token = credential.strip_edges()

func request_json(key: String, path: String, method: int = HTTPClient.METHOD_GET, payload: Dictionary = {}) -> void:
	if _pending.has(key) or _token.is_empty():
		return
	_pending[key] = true
	_queue.append({"key": key, "path": path, "method": method, "payload": payload, "epoch": _epoch})
	_pump()

func _pump() -> void:
	if _busy or _queue.is_empty():
		return
	_busy = true
	var command: Dictionary = _queue.pop_front()
	var request = HTTPRequest.new()
	# Short reads detect a dropped table quickly; commands get more time.
	# Generous on purpose: a busy host PC or a slow phone link must not look like a dropped table.
	request.timeout = 20 if command.method == HTTPClient.METHOD_GET else 30
	request.body_size_limit = 4 * 1024 * 1024
	add_child(request)
	_active = request
	var headers = PackedStringArray(["Accept: application/json", "X-Omnisvera-Token: " + _token])
	var body = ""
	if command.method != HTTPClient.METHOD_GET:
		headers.append("Content-Type: application/json")
		body = JSON.stringify(command.payload)
	request.request_completed.connect(func(result: int, status: int, _headers: PackedStringArray, bytes: PackedByteArray):
		if command.epoch != _epoch:
			request.queue_free()
			return
		_busy = false
		_pending.erase(command.key)
		_active = null
		request.queue_free()
		if result != HTTPRequest.RESULT_SUCCESS:
			failed.emit(command.key, "Conexão interrompida. Tente atualizar.", status)
		elif status < 200 or status >= 300:
			var error_data: Variant = JSON.parse_string(bytes.get_string_from_utf8())
			var message = "Acesso inválido." if status == 401 or status == 403 else "Não foi possível concluir a ação."
			if error_data is Dictionary and error_data.get("detail") is String:
				message = str(error_data.detail).substr(0, 240)
			failed.emit(command.key, message, status)
		else:
			var parser = JSON.new()
			if bytes.is_empty():
				received.emit(command.key, {})  # 204 No Content (e.g. pin removed)
			elif parser.parse(bytes.get_string_from_utf8()) == OK:
				received.emit(command.key, parser.data)
			else:
				failed.emit(command.key, "Resposta do Companion inválida.", status)
		call_deferred("_pump")
	, CONNECT_ONE_SHOT)
	var error = request.request(base_url + command.path, headers, command.method, body)
	if error != OK:
		_pending.erase(command.key)
		_busy = false
		_active = null
		request.queue_free()
		failed.emit(command.key, "Não foi possível iniciar a conexão.", 0)
		call_deferred("_pump")
