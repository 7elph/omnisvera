from __future__ import annotations

from .asset_generation import STYLE_PRESETS

def build_prompt(asset_type: str, style_version: str, source_data: dict) -> str:
    style = STYLE_PRESETS.get(style_version, "")
    # Never invent canonical facts, only use provided source_data
    parts: list[str] = [style]
    if asset_type == "scene_cover":
        if source_data.get("title"):
            parts.append(f"Scene title: {source_data['title']}")
        if source_data.get("location_name"):
            parts.append(f"Location: {source_data['location_name']}")
        if source_data.get("public_description"):
            parts.append(f"Description: {source_data['public_description']}")
        if source_data.get("objective"):
            parts.append(f"Objective: {source_data['objective']}")
        parts.append("widescreen environment, cinematic composition")
    elif asset_type == "session_cover":
        if source_data.get("title"):
            parts.append(f"Session: {source_data['title']}")
        if source_data.get("public_summary"):
            parts.append(f"Summary: {source_data['public_summary']}")
        parts.append("widescreen environment, cinematic composition")
    elif asset_type == "item_art":
        if source_data.get("name"):
            parts.append(f"Item: {source_data['name']}")
        if source_data.get("item_type"):
            parts.append(f"Type: {source_data['item_type']}")
        if source_data.get("description"):
            parts.append(f"Description: {source_data['description']}")
        parts.append("single object centered, detailed fantasy item illustration")
    elif asset_type in ("potion_hp", "potion_mp"):
        if asset_type == "potion_hp":
            parts.append("healing potion, ruby/crimson liquid, clearly identifiable healing potion, readable silhouette")
        else:
            parts.append("mana potion, deep blue/cyan arcane liquid, clearly identifiable mana potion, readable silhouette")
        parts.append("single potion bottle centered, detailed")
    # Filter empty
    prompt = ", ".join(p for p in parts if p)
    return prompt
