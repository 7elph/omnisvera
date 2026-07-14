from __future__ import annotations

from typing import Any


def validate_persona(persona: dict[str, Any]) -> list[str]:
    required = {"id","name","role","voice","vocabulary","tone","knowledge_policy","access_profile","forbidden_behaviors","response_length"}
    errors = [f"campo ausente: {key}" for key in sorted(required - set(persona))]
    if persona.get("knowledge_policy") != "rag_only": errors.append("knowledge_policy precisa ser rag_only")
    if persona.get("role") not in {"npc","narrator","archive"}: errors.append("role inválido")
    if persona.get("access_profile") not in {"player","gm"}: errors.append("access_profile inválido")
    for key in ("voice","vocabulary","tone","forbidden_behaviors"):
        if key in persona and not isinstance(persona[key], list): errors.append(f"{key} precisa ser lista")
    bounds = persona.get("response_length") or {}
    if not isinstance(bounds.get("min"), int) or not isinstance(bounds.get("max"), int) or bounds.get("min",0) > bounds.get("max",0):
        errors.append("response_length inválido")
    return errors


def persona_style_prompt(persona: dict[str, Any]) -> str:
    errors = validate_persona(persona)
    if errors: raise ValueError("; ".join(errors))
    return (
        f"Voz: {', '.join(persona['voice'])}. Tom: {', '.join(persona['tone'])}. "
        f"Vocabulário preferido: {', '.join(persona['vocabulary'])}. "
        f"Entre {persona['response_length']['min']} e {persona['response_length']['max']} palavras. "
        "A persona altera somente o estilo. Use exclusivamente os fatos do contexto autorizado."
    )
