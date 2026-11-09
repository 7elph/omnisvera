extends Node2D
## Visual interpolation only. Connected positions are supplied by the backend.
@export var manifest_path: String = "res://assets/sprites/dorn.json"
var sprite = AnimatedSprite2D.new()
var target_position = Vector2.ZERO
var facing: String = "down"
var selected: bool = true
var visible_name: String = "Dorn"
var preview: bool = true
var projection: Node2D
var frame_offsets: Dictionary = {}
var performing: bool = false
var frame_scales: Dictionary = {}
## Body height on the map, in world pixels (a map tile is 80 x 40). Dorn is the tallest of the party;
## goblins are small. Anything else (standees, other monsters) uses DEFAULT_HEIGHT.
const HEIGHTS = {"dorn": 30.0, "morthak": 26.0, "goblin": 17.0, "skeleton_morthak": 23.0}
const DEFAULT_HEIGHT = 26.0
var world_height: float = DEFAULT_HEIGHT
var size_k: float = 0.3
var seconds_per_meter: float = 0.5
var cell_size_m: float = 1.0
var distance_rule: String = "chebyshev"
var _waypoints: Array[Vector2] = []
var _segment_start = Vector2.ZERO
var _segment_goal = Vector2.ZERO
var _segment_elapsed: float = 0
var _segment_duration: float = 0
var _segment_active: bool = false

func _ready() -> void:
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	visible_name = str(manifest.get("display_name", visible_name))
	if manifest.get("background_filter") == "baked_light_checkerboard":
		var key = ShaderMaterial.new()
		key.shader = load("res://scripts/checkerboard_key.gdshader")
		sprite.material = key
	var frames = SpriteFrames.new()
	frames.remove_animation("default")
	for animation_name in manifest.animations:
		var animation: Dictionary = manifest.animations[animation_name]
		frames.add_animation(animation_name)
		frames.set_animation_speed(animation_name, float(animation.fps))
		frames.set_animation_loop(animation_name, bool(animation.loop))
		var offsets: Array = []
		frame_scales[animation_name] = float(animation.get("render_scale", 0.52))
		var atlas: Texture2D = load("res://assets/sprites/" + animation.sheet)
		for region in animation.frames:
			var frame = AtlasTexture.new()
			frame.atlas = atlas
			frame.region = Rect2(region[0], region[1], region[2], region[3])
			frames.add_frame(animation_name, frame)
			var calibration: Array = animation.get("calibration", [])
			if offsets.size() < calibration.size():
				var pivot: Array = calibration[offsets.size()].pivot
				# Front/back walks are symmetric: anchor on the frame center so the body doesn't sway sideways.
				var pivot_x = region[2] / 2.0 if animation_name in ["walk_up", "walk_down"] else float(pivot[0])
				offsets.append(-Vector2(pivot_x, float(pivot[1])))
			else:
				offsets.append(Vector2(-region[2] / 2.0, -region[3]))
		frame_offsets[animation_name] = offsets
	sprite.sprite_frames = frames
	# One factor for the whole sheet so every animation keeps its calibrated proportion.
	world_height = float(HEIGHTS.get(manifest_path.get_file().get_basename(), DEFAULT_HEIGHT))
	var idle: Dictionary = manifest.animations.get("idle", {})
	var body_px = 0.0
	if idle.get("calibration") is Array and not idle.calibration.is_empty():
		body_px = float(idle.calibration[0].get("body_height", 0))
	if body_px <= 0 and idle.get("frames") is Array and not idle.frames.is_empty():
		body_px = float(idle.frames[0][3])
	size_k = world_height / maxf(1.0, float(frame_scales.get("idle", 0.52)) * maxf(body_px, 1.0))
	sprite.centered = false
	sprite.scale = Vector2(0.52, 0.52) * size_k
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.frame_changed.connect(_align_frame)
	sprite.animation_changed.connect(_align_frame)
	sprite.animation_finished.connect(func():
		if performing:
			if sprite.animation=="death":
				performing=false
				sprite.pause()
				return
			performing = false
			sprite.play("walk_" + facing if _segment_active else "idle")
	)
	add_child(sprite)
	sprite.play("idle")
	_align_frame()
	target_position = position
	queue_redraw()

func _align_frame() -> void:
	if frame_offsets.has(sprite.animation):
		sprite.offset = frame_offsets[sprite.animation][mini(sprite.frame, frame_offsets[sprite.animation].size() - 1)]
		sprite.scale = Vector2.ONE * float(frame_scales.get(sprite.animation, 0.52)) * size_k

func move_visual(destination: Vector2, local_preview: bool = false, confirmed_path: Array = []) -> void:
	preview = local_preview
	if destination.is_equal_approx(target_position):
		return # Polling the same confirmed destination must not restart a step.
	var origin = target_position if _segment_active or not _waypoints.is_empty() else position
	var points: Array = confirmed_path
	if points.is_empty():
		var start = _world_cell(origin)
		var finish = _world_cell(destination)
		points = []
		while start != finish:
			start += Vector2i(signi(finish.x - start.x), signi(finish.y - start.y))
			points.append(_cell_world(start))
	if points.is_empty():
		points.append(destination)
	else:
		points[points.size() - 1] = destination
	for point in points:
		if point is Vector2 and not point.is_equal_approx(origin):
			_waypoints.append(point)
	target_position = destination
	if not _segment_active:
		_start_segment()

func _world_cell(point: Vector2) -> Vector2i:
	if projection: return projection.world_to_grid(point)
	return Vector2i(roundi((point.x / 40 + point.y / 20) / 2), roundi((point.y / 20 - point.x / 40) / 2))

func _cell_world(cell: Vector2i) -> Vector2:
	if projection: return projection.grid_to_world(cell)
	return Vector2((cell.x - cell.y) * 40, (cell.x + cell.y) * 20)

func _start_segment() -> void:
	if _waypoints.is_empty():
		_segment_active = false
		return
	_segment_start = position
	_segment_goal = _waypoints.pop_front()
	var direction = _segment_goal - _segment_start
	var logical = _world_cell(_segment_goal) - _world_cell(_segment_start)
	var dx = absf(logical.x)
	var dy = absf(logical.y)
	_segment_duration = maxf(0.0001, (dx + dy if distance_rule == "manhattan" else maxf(dx, dy)) * cell_size_m * seconds_per_meter)
	_segment_elapsed = 0
	_segment_active = true
	facing = ("right" if direction.x > 0 else "left") if absf(direction.x) > absf(direction.y) else ("down" if direction.y > 0 else "up")
	if not performing:
		sprite.play("walk_" + facing)

func snap_visual(point: Vector2) -> void:
	_waypoints.clear()
	_segment_active = false
	position = point
	target_position = point
	if sprite.animation.begins_with("walk_"):
		sprite.play("idle")

func _process(delta: float) -> void:
	if performing:
		return
	var remaining = delta
	while _segment_active and remaining > 0:
		var consumed = minf(remaining, _segment_duration - _segment_elapsed)
		_segment_elapsed += consumed
		remaining -= consumed
		position = _segment_start.lerp(_segment_goal, clampf(_segment_elapsed / _segment_duration, 0, 1))
		if _segment_duration - _segment_elapsed < 0.000001:
			position = _segment_goal
			_start_segment()
		else:
			break
	if not _segment_active and sprite.animation.begins_with("walk_"):
		sprite.play("idle")
	z_index = int(position.y)
	queue_redraw()

func play_action(action: String) -> void:
	if sprite.sprite_frames.has_animation(action):
		performing = true
		sprite.stop()
		sprite.frame = 0
		sprite.play(action)

func sheet_preview(edge: int = 72) -> Control:
	var box = Control.new()
	box.custom_minimum_size = Vector2(edge, edge)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var picture = AnimatedSprite2D.new()
	picture.sprite_frames = sprite.sprite_frames
	picture.material = sprite.material
	picture.centered = false
	picture.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	picture.position = Vector2(edge / 2.0, edge - 3)
	picture.scale = Vector2.ONE * float(frame_scales.idle) * edge * 0.82 / 93.34
	picture.frame_changed.connect(func(): picture.offset = frame_offsets.idle[picture.frame])
	picture.offset = frame_offsets.idle[0]
	box.add_child(picture)
	picture.play("idle")
	return box

func _draw() -> void:
	draw_set_transform(Vector2.ZERO, 0, Vector2(1, 0.42))
	var r = world_height * 0.45
	draw_circle(Vector2.ZERO, r, Color(0.02, 0.03, 0.03, 0.5))
	if selected:
		draw_arc(Vector2.ZERO, r + 3, 0, TAU, 48, Color("#83d5e1"), 2)
	draw_set_transform(Vector2.ZERO)
