extends SceneTree
func _initialize() -> void:
	call_deferred("check")
func check() -> void:
	var scene = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	scene.authenticated = true
	scene.master = true
	scene.selected_session = {"id":42,"title":"Sessão isolada","status":"active"}
	scene._open_panel("gm")
	assert(scene.body.get_child_count()==9)
	var pause = scene.body.get_child(7)
	assert(pause.text=="Pausar sessão")
	pause.pressed.emit()
	assert(scene.confirm_session.visible)
	assert(scene.session_change=={"id":42,"status":"paused"})
	scene.confirm_session.canceled.emit()
	assert(scene.session_change.is_empty())
	scene.master = false
	scene._clear_body()
	scene._session_controls({"id":42,"status":"active"})
	assert(scene.body.get_child_count()==0)
	print("COMPANION3_GM_SESSION_CONTROLS_PASS")
	quit()
