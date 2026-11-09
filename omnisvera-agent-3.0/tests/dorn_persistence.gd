extends SceneTree

func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	var main = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	main.master = true
	main.authenticated = true
	main.characters = [{"id": "raziel", "name": "Raziel"}, {"id": "dorn7", "name": "Dorn"}]
	main.selected_id = "dorn7"
	var snapshot = {"map": {"id": "fixture", "title": "Fixture", "grid": {"cols": 18, "rows": 18}}, "tokens": [], "presence": []}
	for i in range(5):
		main._received("workspace", snapshot)
		await create_timer(0.1).timeout
		assert(main.dorn.visible)
		assert(main.character_select.get_item_metadata(main.character_select.selected) == "dorn7")
	assert(main.character_select.item_count == 2) # Offline does not revoke sheet access.
	assert(main.dorn.sprite.is_playing())
	assert(main.dorn.sprite.animation == "idle")
	assert(main.dorn.sprite.sprite_frames.get_animation_loop("idle"))
	for animation in ["guard", "cast"]:
		main.dorn.play_action(animation)
		assert(main.dorn.sprite.animation == animation)
		await create_timer(2).timeout
		assert(main.dorn.sprite.animation == "idle")
		assert(main.dorn.visible)
	main.dorn.move_visual(main.dorn.position + Vector2(60, 30), true)
	await create_timer(2).timeout
	assert(main.dorn.sprite.animation == "idle")
	print("COMPANION3_DORN_PERSISTENCE_PASS")
	quit()
