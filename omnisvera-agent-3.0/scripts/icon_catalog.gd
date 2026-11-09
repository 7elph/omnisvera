extends RefCounted
## Same item artwork fallback as Companion 2.0. No mechanics or new items.
static var _data: Dictionary = {}
static func slug(value: Variant) -> String:
	var text = str(value if value != null else "").to_lower()
	var accents = {"á":"a", "à":"a", "â":"a", "ã":"a", "ä":"a", "é":"e", "è":"e", "ê":"e", "ë":"e", "í":"i", "ì":"i", "î":"i", "ï":"i", "ó":"o", "ò":"o", "ô":"o", "õ":"o", "ö":"o", "ú":"u", "ù":"u", "û":"u", "ü":"u", "ç":"c"}
	for letter in accents:
		text = text.replace(letter, accents[letter])
	text = text.replace("'", "").replace("’", "")
	var regex = RegEx.new()
	regex.compile("[^a-z0-9]+")
	return regex.sub(text, "-", true).trim_prefix("-").trim_suffix("-")

static func resolve(data: Dictionary, value: Variant) -> String:
	var normalized = slug(value)
	if normalized.is_empty():
		return ""
	if normalized in data.ids:
		return normalized
	if data.aliases.has(normalized):
		return data.aliases[normalized]
	var best = ""
	for id in data.ids:
		if (normalized.contains(id) or str(id).contains(normalized)) and str(id).length() > best.length():
			best = id
	return best

static func item_art(item: Dictionary) -> Array:
	if _data.is_empty():
		_data = JSON.parse_string(FileAccess.get_file_as_string("res://assets/ui/item-icons.json"))
	var data = _data
	var id = resolve(data, item.get("item_title", item.get("name", "")))
	if id.is_empty() and slug(item.get("item_title", "")).begins_with("vara-"):
		id = "vara-de-3-m"
	if id.is_empty():
		id = resolve(data, item.get("item_type", item.get("type", "")))
	var candidates: Array = [item.get("thumbnail"), item.get("cover"), item.get("image_path")]
	if not id.is_empty():
		candidates.append("zz_media/ui/icons/items/" + id + "." + str(data.extensions.get(id, "png")))
	candidates.append("zz_media/ui/icons/items/inventario.jpg")
	return candidates
