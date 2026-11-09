extends SceneTree
const Actor = preload("res://scripts/dorn.gd")

func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	var actor = Actor.new()
	root.add_child(actor)
	actor.set_process(false)
	# Equal time per metre: later steps must not ease out, and distant clicks
	# must not make the first step faster than a one-cell click.
	actor.move_visual(Vector2(200, 100), true)
	for step in range(5):
		for tick in range(30):
			actor._process(1.0 / 60)
		assert(actor.position.is_equal_approx(Vector2(40, 20) * (step + 1)))
	assert(actor.sprite.animation == "idle")
	actor.snap_visual(Vector2.ZERO)
	actor.move_visual(Vector2(40, 20))
	actor._process(0.25)
	assert(actor.position.is_equal_approx(Vector2(20, 10)))
	actor.move_visual(Vector2(40, 20)) # A refresh must not restart the half-finished step.
	actor._process(0.25)
	assert(actor.position.is_equal_approx(Vector2(40, 20)))
	actor.snap_visual(Vector2.ZERO)
	actor.move_visual(Vector2(0, 40), false, [Vector2(-40, 20), Vector2(0, 40)])
	actor._process(0.5)
	assert(actor.position.is_equal_approx(Vector2(-40, 20)))
	assert(actor.sprite.animation == "walk_right") # Next confirmed step points right.
	actor._process(0.5)
	assert(actor.position.is_equal_approx(Vector2(0, 40)))
	for animation in ["idle", "walk_left", "walk_right", "guard", "cast"]:
		actor.sprite.play(animation)
		actor.sprite.frame = 0
		actor._align_frame()
		var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/sprites/dorn.json"))
		var entry: Dictionary = manifest.animations[animation]
		var body_height = float(entry.calibration[0].body_height) * actor.sprite.scale.y
		assert(absf(body_height - 94) < 5)
	print("COMPANION3_DORN_MOTION_PASS")
	quit()
