extends Node
## GM-side proximity watch. Proposes (or, in automatic mode, starts) a battle when a
## hostile creature pin gets close to a hero on the exploration grid. Starting uses the
## existing /gm/combat/effects "start" command; the server stages the arena.
signal proposal(monsters: Array, heroes: Array)
signal start_requested(payload: Dictionary)
const CONFIG = "user://companion_v3.cfg"
var auto_mode: bool = true   # monsters on the map start the battle when the group gets close
var radius: int = 4
var arena_map_id: String = ""
var ignored: Dictionary = {}       # token id -> true (GM marked "não hostil")
var rows: Dictionary = {}          # character id -> "front" | "back"
var snoozed: Dictionary = {}       # token id -> msec until
var pending: bool = false
var initiative_mode: String = "d20"  # d20 (rolled by the server) | manual | fixed
const DEFAULT_BACK = ["morthak", "raziel"]

func _ready() -> void:
	var file = ConfigFile.new()
	if file.load(CONFIG) == OK:
		auto_mode = bool(file.get_value("encounters", "auto", true))
		radius = int(file.get_value("encounters", "radius", 4))
		arena_map_id = str(file.get_value("encounters", "arena", ""))
		ignored = file.get_value("encounters", "ignored", {})
		rows = file.get_value("encounters", "rows", {})
		initiative_mode = str(file.get_value("encounters", "initiative", "d20"))

func save() -> void:
	var file = ConfigFile.new()
	file.load(CONFIG)
	file.set_value("encounters", "auto", auto_mode)
	file.set_value("encounters", "radius", radius)
	file.set_value("encounters", "arena", arena_map_id)
	file.set_value("encounters", "ignored", ignored)
	file.set_value("encounters", "rows", rows)
	file.set_value("encounters", "initiative", initiative_mode)
	file.save(CONFIG)

func row_of(character_id: String) -> String:
	return str(rows.get(character_id, "back" if character_id in DEFAULT_BACK else "front"))

static func hostile(token: Dictionary) -> bool:
	if token.get("token_type") != "monster" or not token.get("visible_to_players", true): return false
	var sheet: Dictionary = token.get("sheet", {}) if token.get("sheet") is Dictionary else {}
	if sheet.get("combat_retired", false) or sheet.get("summon") or sheet.get("embedded_in_location"): return false
	# Explicit GM marker wins; without it, fall back to "has attacks".
	var disposition = str(sheet.get("disposition", ""))
	if disposition in ["neutral", "ally"] or sheet.get("hostile") == false: return false
	if disposition == "hostile": return token.get("current_hp") == null or int(token.current_hp) > 0
	if token.get("current_hp") != null and int(token.current_hp) <= 0: return false
	return not (sheet.get("attacks", []) as Array).is_empty()

static func cell(token: Dictionary) -> Vector2i:
	var p: Dictionary = token.get("grid_position", {}) if token.get("grid_position") is Dictionary else {}
	if p.is_empty(): return Vector2i(-9999, -9999)
	return Vector2i(int(p.cell_x), int(p.cell_y))

static func distance(a: Dictionary, b: Dictionary) -> int:
	var d = cell(a) - cell(b)
	return maxi(absi(d.x), absi(d.y))

## Pure check over an exploration snapshot. Returns {} or {monsters, heroes}.
func scan(workspace: Dictionary, now_msec: int) -> Dictionary:
	var tokens: Array = workspace.get("tokens", [])
	var heroes = tokens.filter(func(t): return t.get("token_type") == "character" and t.get("character_id") and t.get("grid_position") is Dictionary)
	var monsters = tokens.filter(func(t): return hostile(t) and t.get("grid_position") is Dictionary and not ignored.has(str(t.id)) and int(snoozed.get(str(t.id), 0)) < now_msec)
	var spotted: Array = []
	for monster in monsters:
		for hero in heroes:
			if distance(monster, hero) <= radius:
				spotted.append(monster)
				break
	if spotted.is_empty(): return {}
	# Creatures near the spotted ones join; the whole party on this map joins.
	var group: Array = spotted.duplicate()
	for monster in monsters:
		if monster in group: continue
		for other in spotted:
			if distance(monster, other) <= radius:
				group.append(monster)
				break
	return {"monsters": group, "heroes": heroes}

func snooze(monsters: Array, seconds: float = 90) -> void:
	for monster in monsters: snoozed[str(monster.id)] = Time.get_ticks_msec() + int(seconds * 1000)

## Arena grid + formation: heroes on the left, creatures on the right, front lines adjacent.
func build_payload(monsters: Array, heroes: Array, arena: Dictionary) -> Dictionary:
	var grid: Dictionary = arena.get("map", {}).get("grid", {})
	var cols = int(grid.get("cols", 12))
	var rows_count = int(grid.get("rows", 8))
	var middle = cols / 2
	var center = rows_count / 2
	var participants: Array = []
	var formation: Array = []
	var lanes = [0, -1, 1, -2, 2, -3, 3, -4, 4]
	var slots = {"hero-front": 0, "hero-back": 0, "monster-front": 0, "monster-back": 0}
	for hero in heroes:
		var line = "hero-" + row_of(str(hero.character_id))
		var x = middle - 1 if line == "hero-front" else middle - 3
		var y = clampi(center + lanes[slots[line] % lanes.size()], 0, rows_count - 1)
		slots[line] += 1
		participants.append({"target_type": "character", "target_id": str(hero.character_id), "name": str(hero.get("name", hero.character_id)), "initiative": 0})
		formation.append({"target_type": "character", "target_id": str(hero.character_id), "cell": [clampi(x, 0, cols - 1), y]})
	for index in range(monsters.size()):
		var monster: Dictionary = monsters[index]
		var line = "monster-front" if index < maxi(1, heroes.size()) else "monster-back"
		var x = middle if line == "monster-front" else middle + 2
		var y = clampi(center + lanes[slots[line] % lanes.size()], 0, rows_count - 1)
		slots[line] += 1
		participants.append({"target_type": "token", "target_id": str(monster.id), "name": str(monster.get("name", "Criatura")), "initiative": 0})
		formation.append({"target_type": "token", "target_id": str(monster.id), "cell": [clampi(x, 0, cols - 1), y]})
	var names = monsters.map(func(m): return str(m.get("name", "Criatura")))
	return {"map_id": str(arena.get("map", {}).get("id", arena_map_id)), "battle_mode": true, "participants": participants,
		"formation": formation, "title": "Batalha · " + ", ".join(names).substr(0, 80)}
