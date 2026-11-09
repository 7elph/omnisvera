extends SceneTree
func _initialize() -> void:
	call_deferred("check")
func check() -> void:
	var main = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	assert(main.has_node("Morthak"))
	var actor = main.get_node("Morthak")
	actor.set_process(false)
	assert(actor.sprite.sprite_frames.get_animation_names().size() == 5)
	for name in ["idle", "walk_down", "walk_up", "walk_left", "walk_right"]:
		assert(actor.sprite.sprite_frames.get_frame_count(name) == 8)
	assert(actor.sprite.material != null) # The JPG checkerboard is filtered only at rendering.
	main.master = true
	main.authenticated = true
	main.characters = [{"id":"dorn7","name":"Dorn"},{"id":"morthak","name":"Morthak"}]
	main.selected_id = "morthak"
	var snapshot = {"map":{"id":"fixture","grid":{"cols":18,"rows":18,"cell_size_m":1}},"tokens":[
		{"id":"morthak-pin","character_id":"morthak","name":"Morthak","grid_position":{"cell_x":8,"cell_y":8}},
		{"id":"dorn-pin","character_id":"dorn7","name":"Dorn","grid_position":{"cell_x":4,"cell_y":4}}],"presence":[]}
	main._received("workspace", snapshot)
	assert(actor.visible and not actor.preview)
	assert(actor.target_position == main.grid.grid_to_world(Vector2i(8,8)))
	var dorn_position = main.dorn.target_position
	actor.snap_visual(main.grid.grid_to_world(Vector2i(8,8)))
	actor.move_visual(main.grid.grid_to_world(Vector2i(7,8)))
	assert(actor.sprite.animation == "walk_left")
	actor._process(0.5)
	assert(actor.sprite.animation == "idle")
	assert(main.dorn.target_position == dorn_position)
	main._received("workspace", {"map":snapshot.map,"tokens":[],"presence":[]})
	main.master = false
	main.my_profile = "morthak"
	main._received("workspace", {"map":snapshot.map,"tokens":[],"presence":[]})
	assert(not actor.visible) # No sprite can reveal an absent/hidden server entity.
	assert(main.status.visible and "não está" in main.status.text)
	main.camera.position = Vector2(-1000,-1000)
	main._received("workspace", snapshot)
	assert(main.camera.position == actor.position) # Newly placed own token must appear without reload.
	print("COMPANION3_MORTHAK_CONTRACT_PASS")
	quit()
