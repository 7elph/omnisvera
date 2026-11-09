extends SceneTree
func _initialize() -> void:
	call_deferred("check")
func check() -> void:
	var scene=load("res://scenes/main.tscn").instantiate();root.add_child(scene);await process_frame
	scene.connection.hide();scene.authenticated=true;scene.master=true
	var before=scene.camera.position
	var effects={"round":1,"version":1,"encounter":{"active":true,"battle_mode":true,"started_at":"fixture-only","map_id":"arena","return_map_id":"explore","turn_index":0,"participants":[{"target_type":"character","target_id":"dorn7","token_id":"dorn","name":"Dorn"},{"target_type":"token","target_id":"goblin","token_id":"goblin","name":"Goblin"}]}}
	var table={"map":{"id":"arena","title":"Arena isolada","grid":{"cols":12,"rows":8,"cell_size_m":1,"version":1}},"tokens":[{"id":"dorn","token_type":"character","character_id":"dorn7","name":"Dorn","grid_position":{"cell_x":3,"cell_y":4,"version":1}},{"id":"goblin","character_id":null,"token_type":"monster","name":"Goblin","grid_position":{"cell_x":4,"cell_y":4,"version":1},"sheet":{"attacks":[{"name":"Espada curta","damage":"1d6","bonus":2}]}}]}
	scene.combat_state=effects;scene.arena_snapshot=table
	scene.battle_overlay.update_view(effects,table,true,"")
	await process_frame;scene.battle_overlay._layout_arena()
	assert(scene.battle_overlay.visible)
	assert(scene.battle_overlay.actors.size()==2)
	assert(scene.camera.position==before)
	assert(not scene.battle_overlay.attack.disabled)
	scene.battle_overlay.hide();scene.battle_overlay.update_view(effects,table,true,"")
	assert(not scene.battle_overlay.visible)
	scene.battle_overlay.show()
	scene.battle_overlay.update_view(effects,table,false,"raziel")
	assert(scene.battle_overlay.attack.disabled)
	scene.battle_overlay.update_view(effects,table,true,"")
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("user://battle-overlay.png")
	scene.battle_overlay.update_view({"encounter":{"active":false}},table,true,"")
	assert(not scene.battle_overlay.visible)
	effects.encounter.turn_sequence=1
	scene.combat_state=effects
	scene._received("arena-pending",[{"request_id":"arena-attack-old","resolution_id":"old","breakdown":{"combat_turn":["old",1,"character","dorn7"]}}])
	assert(scene.pending_intent.is_empty())
	scene._received("arena-pending",[{"request_id":"arena-attack-current","resolution_id":"current","breakdown":{"combat_turn":["fixture-only",1,"character","dorn7"]}}])
	assert(scene.pending_intent.key=="arena-confirm")
	print("COMPANION3_BATTLE_OVERLAY_PASS");quit()
