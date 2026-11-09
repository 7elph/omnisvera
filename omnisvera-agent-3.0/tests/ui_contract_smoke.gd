extends SceneTree

const Presence = preload("res://scripts/hud_player.gd")
const Navigation = preload("res://scripts/navigation_panel.gd")
const Media = preload("res://scripts/media_cache.gd")
const Map = preload("res://scripts/map_viewer.gd")
const Commands = preload("res://scripts/game_commands.gd")
const Icons = preload("res://scripts/icon_catalog.gd")

func _initialize() -> void:
	call_deferred("check")

func check() -> void:
	var roster = Presence.new()
	root.add_child(roster)
	var characters = [{"id": "dorn7", "name": "Dorn"}, {"id": "raziel", "name": "Raziel"}]
	var presence = [{"character_id": "dorn7", "online": false},
		{"character_id": "raziel", "online": true},
		{"actor_id": "master", "actor_role": "gm", "actor_name": "Mestre", "online": true}]
	assert(Presence.online_characters(characters, presence).size() == 1)
	roster.update_roster(characters, presence)
	assert(roster.get_child_count() == 1)
	assert(roster.get_child(0).get_meta("identity") == "raziel")
	assert(roster.get_child(0).icon == null) # No replacement sprite masquerading as portrait.
	roster.update_roster(characters, [])
	assert(roster.get_child_count() == 0)
	roster.controlled_id = "dorn7"
	roster.update_roster(characters, [])
	assert(roster.get_child_count() == 0)
	var nav = Navigation.new()
	root.add_child(nav)
	assert(not nav.buttons.has("log"))
	assert(nav.buttons.has("sessions"))
	assert(nav.buttons.sheet is TextureButton) # Cannot draw a themed card background.
	assert(nav.buttons.sheet.custom_minimum_size.x >= 56)
	assert(nav.buttons.sheet.custom_minimum_size.y >= 54)
	nav.fit_height(390)
	assert(nav.column.columns == 2)
	assert(Commands.path_between(Vector2i(1,1), Vector2i(3,2)) == [[1,1],[2,2],[3,2]])
	var movement = Commands.move({"map": {"id": "fixture", "grid": {"version": 2}}, "tokens": [{"id": "pc", "character_id": "dorn7", "grid_position": {"cell_x": 1, "cell_y": 1, "version": 3}}]}, "dorn7", Vector2i(2,1), {})
	assert(movement.payload.mode == "EXPLORATION_MOVE")
	assert(movement.payload.expected_position_version == 3)
	assert(Media.media_path("zz_media/portrait.png") == "/media/zz_media/portrait.png?preview_size=128")
	assert(Media.media_path("https://outside.invalid/photo.png") == "")
	assert(Media.media_path("../private.png") == "")
	assert(Media.media_path("zz_media/%2e%2e/private.png") == "")
	assert(Media.media_path("zz_media/photo.png?token=secret") == "")
	assert(Media.media_path('"![[ui/icons/items/adaga.png|Adaga]]"') == "/media/zz_media/ui/icons/items/adaga.png?preview_size=128")
	assert(Media.media_path("/media/zz_media/Po%C3%A7%C3%A3o.png?preview_size=128", 768) == "/media/zz_media/Po%C3%A7%C3%A3o.png?preview_size=768")
	assert(Media.media_path("zz_media/%252e%252e/private.png") == "")
	assert("zz_media/ui/icons/items/armadura-de-couro.png" in Icons.item_art({"item_title": "Armadura de couro", "thumbnail": null}))
	assert("zz_media/ui/icons/items/bordao-cajado.png" in Icons.item_art({"item_title": "Cajado"}))
	var loader = Media.new()
	root.add_child(loader)
	loader.configure("http://127.0.0.1:1", "fixture-token")
	loader._busy = true # Hold transport to inspect scheduling without a network.
	var picture = TextureRect.new()
	root.add_child(picture)
	var pixel = Image.create(4, 4, false, Image.FORMAT_RGBA8)
	var thumbnail = ImageTexture.create_from_image(pixel)
	loader._cache[Media.media_path("zz_media/map.png", 128)] = thumbnail
	loader.bind("zz_media/gallery.png", picture)
	loader.bind("zz_media/map.png", picture, "texture", 768)
	assert(picture.texture == thumbnail)
	assert(loader._queue[0].ends_with("map.png?preview_size=768"))
	# An old thumbnail cannot overwrite a new full-size binding on the same object.
	var gallery = Media.media_path("zz_media/gallery.png")
	loader._deliver(gallery, ImageTexture.create_from_image(pixel))
	assert(picture.texture == thumbnail)
	var full = ImageTexture.create_from_image(pixel)
	loader._deliver(Media.media_path("zz_media/map.png", 768), full)
	assert(picture.texture == full)
	# A broken preferred artwork falls back to an existing catalog image.
	var fallback = Media.media_path("zz_media/adaga.png")
	loader._cache[fallback] = thumbnail
	loader.bind(["zz_media/missing.png", "zz_media/adaga.png"], picture)
	loader._deliver(Media.media_path("zz_media/missing.png"), null)
	assert(picture.texture == thumbnail)
	loader.configure("http://127.0.0.1:1", "another-fixture-token")
	assert(loader._cache.is_empty() and loader._queue.is_empty())
	var viewer = Map.new()
	root.add_child(viewer)
	assert(not viewer is PanelContainer) # The world must remain visible beside the image.
	viewer.size = Vector2(754, 362)
	await process_frame
	viewer.surface.texture = ImageTexture.create_from_image(Image.create(768, 509, false, Image.FORMAT_RGBA8))
	viewer.surface.update_geometry()
	assert(is_equal_approx(viewer.surface.bounds.size.y, 362))
	assert(is_equal_approx(viewer.surface.bounds.size.x / viewer.surface.bounds.size.y, 768.0 / 509.0))
	assert(viewer.surface._has_point(viewer.surface.bounds.get_center()))
	assert(not viewer.surface._has_point(Vector2(1, 180)))
	var original = viewer.surface.bounds
	viewer.surface.zoom_at(2.0, original.get_center())
	viewer.surface.update_geometry()
	assert(viewer.surface.bounds.get_center().is_equal_approx(original.get_center()))
	assert(viewer.surface.bounds.size.is_equal_approx(original.size * 2))
	print("COMPANION3_UI_CONTRACT_PASS")
	quit()
