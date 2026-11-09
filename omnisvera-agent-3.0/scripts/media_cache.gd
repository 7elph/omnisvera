extends Node
signal failed(path: String)
## Bounded credential-scoped cache; no token in URLs and no external hosts.
var base_url: String = ""
var _token: String = ""
var _epoch: int = 0
var _cache: Dictionary = {}
var _queue: Array = []
var _waiting: Dictionary = {}
var _active: HTTPRequest
var _busy: bool = false
var _missing: Dictionary = {}
var _serial: int = 0

static func media_path(raw: Variant, edge: int = 128) -> String:
	var path = str(raw if raw != null else "").strip_edges().trim_prefix('"').trim_suffix('"').trim_prefix("'").trim_suffix("'")
	path = path.trim_prefix("![[").trim_prefix("[[").trim_suffix("]]").split("|")[0].strip_edges()
	# Only the preview query is accepted. Credentials never travel in URLs.
	if "?" in path:
		var query = path.split("?", true, 1)
		if query[1] not in ["preview_size=128", "preview_size=768"]:
			return ""
		path = query[0]
	var escaped = RegEx.new()
	escaped.compile("%[0-9a-fA-F]{2}")
	for match in escaped.search_all(path):
		path = path.replace(match.get_string(), match.get_string().to_upper())
	# Reject encoded control/path separators before decoding as well.
	for unsafe in ["%2E", "%2F", "%5C", "%25", "%3A", "%3F", "%23", "%00"]:
		if unsafe in path:
			return ""
	path = path.uri_decode().replace("\\", "/")
	path = path.trim_prefix("/media/").trim_prefix("/")
	if not (path.begins_with("zz_media/") or path.begins_with("companion-assets/")):
		path = "zz_media/" + path
	if ".." in path or ":" in path or "%" in path or "?" in path or "#" in path or "\\" in path:
		return ""
	if path == "zz_media/":
		return ""
	var segments = PackedStringArray()
	for segment in path.split("/"):
		segments.append(segment.uri_encode())
	return "/media/" + "/".join(segments) + "?preview_size=" + str(768 if edge == 768 else 128)

func configure(url: String, credential: String) -> void:
	_epoch += 1
	base_url = url
	_token = credential
	_cache.clear()
	_queue.clear()
	_waiting.clear()
	_missing.clear()
	_busy = false
	if is_instance_valid(_active):
		_active.cancel_request()
		_active.queue_free()
	_active = null

func bind(raw: Variant, target: Object, property: String = "texture", edge: int = 128) -> void:
	if not is_instance_valid(target) or _token.is_empty():
		return
	var paths: Array = []
	for candidate in raw if raw is Array else [raw]:
		var path = media_path(candidate, edge)
		if not path.is_empty() and path not in paths:
			paths.append(path)
	if paths.is_empty():
		return
	_serial += 1
	target.set_meta("media_binding_" + property, _serial)
	_enqueue({"target": weakref(target), "property": property, "serial": _serial, "paths": paths, "edge": edge})

func _is_current(binding: Dictionary) -> bool:
	var target = binding.target.get_ref()
	return is_instance_valid(target) and target.get_meta("media_binding_" + binding.property, -1) == binding.serial

func _enqueue(binding: Dictionary) -> void:
	if not _is_current(binding):
		return
	while not binding.paths.is_empty() and float(_missing.get(binding.paths[0], 0)) > Time.get_ticks_msec():
		binding.paths.pop_front()
	if binding.paths.is_empty():
		return
	var path: String = binding.paths[0]
	var target = binding.target.get_ref()
	if _cache.has(path):
		target.set(binding.property, _cache[path])
		return
	if binding.edge == 768:
		var thumbnail = path.replace("preview_size=768", "preview_size=128")
		if _cache.has(thumbnail):
			target.set(binding.property, _cache[thumbnail])
	if _waiting.has(path):
		_waiting[path].append(binding)
	else:
		_waiting[path] = [binding]
		if binding.edge == 768:
			_queue.push_front(path)
		else:
			_queue.append(path)
	_pump()

func _deliver(path: String, texture: ImageTexture) -> void:
	var bindings: Array = _waiting.get(path, [])
	_waiting.erase(path)
	if not texture:
		if _missing.size() >= 64:
			_missing.erase(_missing.keys()[0])
		_missing[path] = Time.get_ticks_msec() + 30000
	for binding in bindings:
		if not _is_current(binding):
			continue
		if texture:
			binding.target.get_ref().set(binding.property, texture)
		else:
			binding.paths.pop_front()
			if binding.paths.is_empty():
				failed.emit(path)
			else:
				_enqueue(binding)

func _pump() -> void:
	if _busy or _queue.is_empty():
		return
	var path: String = _queue.pop_front()
	var alive = false
	for binding in _waiting.get(path, []):
		if _is_current(binding):
			alive = true
	if not alive:
		_waiting.erase(path)
		call_deferred("_pump")
		return
	_busy = true
	var epoch = _epoch
	var request = HTTPRequest.new()
	request.timeout = 12
	request.max_redirects = 0
	request.body_size_limit = 5 * 1024 * 1024
	add_child(request)
	_active = request
	request.request_completed.connect(func(result: int, status: int, _headers: PackedStringArray, bytes: PackedByteArray):
		request.queue_free()
		if epoch != _epoch:
			return
		_busy = false
		_active = null
		var texture: ImageTexture
		if result == HTTPRequest.RESULT_SUCCESS and status == 200:
			var image = Image.new()
			var signature = bytes.slice(0, 4).hex_encode()
			var error = ERR_FILE_UNRECOGNIZED
			if signature == "52494646":
				error = image.load_webp_from_buffer(bytes)
			elif signature == "89504e47":
				error = image.load_png_from_buffer(bytes)
			elif signature.begins_with("ffd8"):
				error = image.load_jpg_from_buffer(bytes)
			elif bytes.get_string_from_utf8().strip_edges().begins_with("<svg") or bytes.get_string_from_utf8().strip_edges().begins_with("<?xml"):
				error = image.load_svg_from_buffer(bytes)
			if error == OK and image.get_width() <= 1024 and image.get_height() <= 1024:
				texture = ImageTexture.create_from_image(image)
				if _cache.size() >= 48:
					_cache.erase(_cache.keys()[0])
				_cache[path] = texture
		_deliver(path, texture)
		call_deferred("_pump")
	, CONNECT_ONE_SHOT)
	var error = request.request(base_url + path, PackedStringArray(["X-Omnisvera-Token: " + _token]))
	if error != OK:
		request.queue_free()
		_active = null
		_busy = false
		_deliver(path, null)
		call_deferred("_pump")
