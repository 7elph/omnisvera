"""Source-backed breath specifications; parsing never grants execution authority."""
from __future__ import annotations
import re
from .monster_actions import explicit_damage_dice


def _geometry(text: str) -> dict:
    shape = next((s for s in ("cone", "linha", "nuvem") if re.search(r"\b" + s + r"\b", text, re.I)), None)
    result = {"shape": {"linha": "line", "nuvem": "cloud"}.get(shape, shape),
              "width_m": None, "depth_m": None, "radius_m": None, "height_m": None}
    for field, word in (("width_m", "largura"), ("depth_m", "dist[aâ]ncia"), ("height_m", "altura")):
        match = re.search(r"(\d+)\s*metros?\s*de\s*" + word, text, re.I)
        if match:
            result[field] = int(match[1])
    radius = re.search(r"raio\s+de\s+(\d+)\s*metros?", text, re.I)
    if radius:
        result.update(shape="radius", radius_m=int(radius[1]))
    if shape == "linha":
        match = re.search(r"linha\s+de\s+at[ée]\s+(\d+)\s*metros?", text, re.I)
        if match:
            result["depth_m"] = int(match[1])
    result["declared"] = bool(result["radius_m"] or result["depth_m"])
    return result


def _uses(text: str) -> dict:
    match = re.search(r"(\d+|uma)\s+vez(?:es)?\s+(ao dia|por dia|por combate)", text, re.I)
    if match:
        maximum = 1 if match[1].lower() == "uma" else int(match[1])
        return {"maximum": maximum, "recharge": "combat" if match[2].lower() == "por combate" else "day"}
    match = re.search(r"uma\s+vez\s+a\s+cada\s+(\d+)\s+ataques", text, re.I)
    if match:
        return {"maximum": 1, "recharge": "every_n_attacks", "every_n_attacks": int(match[1])}
    if re.search(r"[àa]\s+vontade|n[ãa]o\s+tem\s+limita[çc][õo]es", text, re.I):
        return {"maximum": None, "recharge": "at_will"}
    return {"maximum": None, "recharge": None}


def monster_action_specs(monster: dict) -> list[dict]:
    catalog = monster.get("catalog") or {}
    results = []
    for index, ability in enumerate(monster.get("abilities") or []):
        name, text = str(ability.get("name") or ""), str(ability.get("description") or "")
        if not re.search(r"\b(baforada|sopro)\b", name + " " + text, re.I):
            continue
        formula = explicit_damage_dice(text)
        hd = re.fullmatch(r"([1-9]\d*)(?:[+-]\d+)?", str(monster.get("hit_dice") or ""))
        scaled = re.search(r"n[úu]mero de seus dados de vida em d(\d+)", text, re.I)
        if not formula and hd and scaled:
            formula = f"{hd[1]}d{scaled[1]}"
        multiplier = re.search(r"\d+d\d+\s*[x×]\s*(\d+)\s+pontos?\s+de\s+dano", text, re.I)
        if multiplier:
            formula = re.search(r"\d+d\d+", multiplier[0], re.I)[0].lower()
        save = re.search(r"\bJP\s*([DCS])\b", text, re.I)
        save_effect = "halves" if re.search(r"reduzir.*metade|reduz.*metade", text, re.I) else (
            "negates" if re.search(r"evita|nega", text, re.I) else None)
        geometry, uses = _geometry(text), _uses(text)
        reasons = []
        if not formula:
            reasons.append("dano_sem_formula_explicita")
        if not geometry["declared"]:
            reasons.append("geometria_incompleta")
        if not save or not save_effect:
            reasons.append("jp_ou_resultado_nao_declarado")
        if not uses["recharge"]:
            reasons.append("frequencia_nao_declarada")
        if re.search(r"chance|cego|petrific|Ghoul|concentrando|extra|regressivo", text, re.I):
            reasons.append("condicoes_ou_efeitos_adicionais")
        results.append({"id": f"{monster.get('id')}:breath:{index}", "name": name, "ability_name": name,
            "family": "breath", "description_full": text,
            "source": {"monster_id": monster.get("id"), "edition": catalog.get("edition") or "OD2",
                       "url": monster.get("source_url") or catalog.get("source_url"),
                       "license": catalog.get("license") or "CC BY-SA 4.0"},
            "damage_formula": formula, "damage_multiplier": int(multiplier[1]) if multiplier else 1,
            "save": f"JP{save[1].upper()}" if save else None, "save_effect": save_effect,
            "geometry": geometry, "uses": uses, "reasons": reasons,
            "automation_status": "assisted" if reasons else "specification_complete",
            "execution_status": "not_bound"})
    return results
