extends RefCounted
## Command construction only. The server validates ownership, path and turns.
static func path_between(start: Vector2i, finish: Vector2i) -> Array:
	var path: Array = [[start.x, start.y]]
	var cell = start
	while cell != finish and path.size() < 401:
		cell += Vector2i(signi(finish.x - cell.x), signi(finish.y - cell.y))
		path.append([cell.x, cell.y])
	return path

## Shortest 8-way path that walks around blocked cells (trees, buildings). [] when there is no way.
static func path_around(start: Vector2i, finish: Vector2i, blocked: Dictionary, cols: int, rows: int, limit: int = 400) -> Array:
	if blocked.is_empty() or start == finish: return path_between(start, finish)
	if blocked.has(finish): return []
	var came: Dictionary = {start: start}
	var queue: Array = [start]
	var head = 0
	while head < queue.size() and queue.size() < 6000:
		var cell: Vector2i = queue[head]
		head += 1
		if cell == finish: break
		for dx in [-1, 0, 1]:
			for dy in [-1, 0, 1]:
				var next = cell + Vector2i(dx, dy)
				if (dx == 0 and dy == 0) or came.has(next) or blocked.has(next): continue
				if next.x < 0 or next.y < 0 or next.x >= cols or next.y >= rows: continue
				if dx != 0 and dy != 0 and (blocked.has(cell + Vector2i(dx, 0)) or blocked.has(cell + Vector2i(0, dy))): continue  # no corner cutting
				came[next] = cell
				queue.append(next)
	if not came.has(finish): return []
	var path: Array = []
	var step = finish
	while step != start:
		path.push_front([step.x, step.y])
		step = came[step]
	path.push_front([start.x, start.y])
	return path if path.size() <= limit + 1 else []

static func move(snapshot: Dictionary, profile: String, destination: Vector2i, combat: Dictionary, blocked: Dictionary = {}) -> Dictionary:
	var map: Dictionary = snapshot.get("map") if snapshot.get("map") is Dictionary else {}
	var geometry: Dictionary = map.get("grid", {})
	for token in snapshot.get("tokens", []):
		if token.get("character_id") != profile or not token.get("grid_position") is Dictionary:
			continue
		var pos: Dictionary = token.grid_position
		var active = combat.get("encounter", {}).get("active", false)
		return {"path": "/workspace/maps/" + str(map.id).uri_encode() + "/move", "payload": {
			"request_id": "godot-move-" + Crypto.new().generate_random_bytes(12).hex_encode(),
			"token_id": token.id, "mode": "COMBAT_MOVE" if active else "EXPLORATION_MOVE",
			"path": path_around(Vector2i(int(pos.cell_x), int(pos.cell_y)), destination, blocked, int(geometry.get("cols", 96)), int(geometry.get("rows", 96))),
			"expected_position_version": int(pos.version), "expected_grid_version": int(geometry.get("version", 0)),
			"expected_combat_version": int(combat.get("version", 0))}}
	return {}

static func attack(spell_id: String, actor_id: String, target_ids: Array, revision: int = 0) -> Dictionary:
	var targets: Array = []
	for id in target_ids:
		targets.append({"type": "token", "id": id})
	return {
		"path": "/gm/combat/attack",
		"payload": {
			"request_id": "godot-attack-" + Crypto.new().generate_random_bytes(12).hex_encode(),
			"spell_id": spell_id,
			"actor_id": actor_id,
			"targets": targets,
			"expected_revision": revision
		}}