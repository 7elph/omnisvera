extends SceneTree
func _initialize() -> void:
	call_deferred("check")
func check() -> void:
	var scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	assert(scene.screen.position.is_equal_approx(Vector2.ZERO))
	scene.connection.hide()
	scene.authenticated = true
	scene.master = true
	scene._open_panel("editor")
	await process_frame
	await process_frame
	scene._fit_drawers()
	assert(scene.panel.size.y < 500)
	assert(scene.panel.has_node("ROM2Border"))
	assert(scene.panel.get_node("ROM2Border").mouse_filter==Control.MOUSE_FILTER_IGNORE)
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("user://compact-rom2-drawer.png")
	scene._clear_body()
	for i in range(100): scene._label(scene.body,"Long content "+str(i))
	await process_frame
	scene._fit_drawers()
	assert(scene.panel.size.y<=root.size.y-28)
	assert(scene.panel.size.y>500)
	print("COMPANION3_COMPACT_DRAWERS_PASS")
	quit()
