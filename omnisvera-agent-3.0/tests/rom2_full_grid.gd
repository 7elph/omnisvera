extends SceneTree
func _initialize() -> void:
	call_deferred("check")
func check() -> void:
	var terrain = load("res://scripts/rom2_terrain.gd").new()
	root.add_child(terrain)
	var failures = 0
	for y in range(80):
		for x in range(80):
			var cell = Vector2i(x,y)
			if terrain.world_to_cell(terrain.cell_to_world(cell)) != cell:
				failures += 1
				print(cell, " -> ", terrain.world_to_cell(terrain.cell_to_world(cell)))
	print("ROM2_FULL_GRID_ROUNDTRIP_FAILURES=",failures)
	quit(1 if failures else 0)
