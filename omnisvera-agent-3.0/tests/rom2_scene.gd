extends SceneTree
func _initialize() -> void:
	call_deferred("check")
func check() -> void:
	var scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	scene.connection.hide()
	assert(scene.grid.terrain != null)
	assert(scene.map_label.text == "Arredores de Nimalis")
	for cell in [Vector2i(6,6),Vector2i(7,6),Vector2i(8,6)]:
		assert(scene.grid.world_to_grid(scene.grid.grid_to_world(cell))==cell)
	var terrain = scene.grid.terrain
	var cell = Vector2i(6,6)
	var index = cell.y*int(terrain.model.width)+cell.x
	var before = terrain.model.tiles[index]
	var choice = int(terrain.model.visuals.tile_refs.keys()[0])
	terrain.paint(cell,choice)
	assert(int(terrain.model.tiles[index])==choice)
	terrain.undo_edit()
	assert(terrain.model.tiles[index]==before)
	terrain.paint(Vector2i(-1,-1),choice)
	assert(terrain.edit_history.is_empty())
	scene.dorn.move_visual(scene.grid.grid_to_world(Vector2i(8,6)))
	await create_timer(3).timeout
	assert(scene.dorn.position.distance_to(scene.grid.grid_to_world(Vector2i(8,6)))<1)
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("user://rom2-companion.png")
	print("ROM2_COMPANION_SCENE_PASS")
	quit()
