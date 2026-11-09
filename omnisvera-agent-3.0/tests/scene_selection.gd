extends SceneTree
func _initialize() -> void:
	call_deferred("check")
func check() -> void:
	var scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	scene.authenticated = true
	scene.master = true
	scene._open_preparation({"id":1,"title":"Ensaio","elements":[{"id":2,"title":"Pista"}]})
	assert(scene.active_panel=="preparation")
	assert(scene.body.get_child(scene.body.get_child_count()-1).disabled)
	scene.preparation._toggle(scene.preparation.element_ids,2,true)
	scene._confirm_preparation()
	assert(scene.confirm_preparation.visible)
	assert(scene.preparation_intent.payload.element_ids==[2])
	assert(scene.pending_intent.is_empty())
	scene.confirm_preparation.canceled.emit()
	assert(scene.preparation_intent.is_empty())
	scene.confirm_preparation.hide()
	scene.connection.hide()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("user://scene-preparation.png")
	scene.master = false
	scene._confirm_preparation()
	assert(scene.preparation_intent.is_empty())
	print("COMPANION3_SCENE_SELECTION_UI_PASS")
	quit()
