# Omnisvera Companion 3.0 — rules for coding agents

- Godot 4.7, GDScript 2.0. Indent with TABS. Static typing where the surrounding code uses it.
- The client is a thin view: the FastAPI backend is authoritative. Never compute rules, damage or rolls in the client; send intents.
- Only edit the files named in your task. Do not rename public functions other files call.
- UI text is Brazilian Portuguese. Keep strings short.
- Use `host` (the main scene, scripts/main.gd) for shared state: host.api.request_json(key, path, method, body), host._notice(text), host._show_detail(dict), host.media.bind(path, node, property), host.master, host.selected_id, host.sheet.
- Controllers live in scripts/controllers/*.gd and implement setup(main), handles(key), received(key, payload), failed(key, message, code).
- Do not add new autoloads, plugins or dependencies. No network calls except through host.api.
- When done, write a short summary of what you changed to build/opencode/<task>.md.
