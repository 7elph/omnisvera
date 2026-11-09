extends SceneTree
func _initialize() -> void:
	call_deferred("render_map")
func render_map() -> void:
	var viewport = SubViewport.new()
	viewport.size = Vector2i(2560,2560)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var terrain = load("res://scripts/rom2_terrain.gd").new()
	viewport.add_child(terrain)
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png("user://arredores-nimalis.png")
	print("ROM2_MAP_PREVIEW_EXPORTED")
	quit()
