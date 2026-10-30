"""Lossless bestiary -> declarative rule records; no database writes or invented rules.

The raw record and clause offsets make every interpretation reviewable. A parsed
rule is NOT an installed combat handler. Existing attack execution remains native.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re

from .monster_actions import classify_ability, parse_attack_entry
from .monster_action_specs import monster_action_specs
from .monster_movement import movement_modes, movement_pending


_KINDS = (
    ("immunity", r"imun"), ("resistance", r"resist[eê]ncia|resistente"),
    ("vulnerability", r"vulner|dobro.*dano"), ("regeneration", r"regener"),
    ("saving_throw", r"\bJP\s*[DCS]\b"), ("damage", r"\bdano\b"),
    ("condition", r"paralis|petrific|envenen|sono|encant|amedront|apavor"),
    ("sense", r"infravis|vis[aã]o|detect|sentir"),
    ("spellcasting", r"conjura|magias?"), ("movement", r"voar|nadar|movimenta|deslocamento"),
)


def _clauses(text: str) -> list[dict]:
    # Keep separators and whitespace: joining clauses reconstructs EXACT source.
    result = []
    for match in re.finditer(r"[^.;\n]+(?:[.;\n]+|$)|[.;\n]+", text):
        fragment = match.group(0)
        kinds = [kind for kind, pattern in _KINDS if re.search(pattern, fragment, re.I)]
        result.append({"start": match.start(), "end": match.end(), "text": fragment,
                       "kind": kinds[0] if kinds else "other", "tags": kinds,
                       "execution_status": "unbound"})
    return result


def compile_monster_rules(monster: dict, catalog: dict, *, art_usage_count: int | None = None) -> dict:
    """Compile all supplied fields, attacks and abilities without losing text.

    Callers pass the existing catalog metadata, preserving rules and art licenses
    separately. No filesystem/network access, character state or hidden GM data.
    """
    record = deepcopy(monster)
    identity = str(monster.get("id") or "custom")
    source = {"catalog_id": catalog.get("id"), "edition": catalog.get("edition"),
              "url": monster.get("source_url") or catalog.get("source_url"),
              "license": catalog.get("license"), "license_url": catalog.get("license_url"),
              "attribution": catalog.get("attribution")}
    revision = hashlib.sha256(json.dumps(record, ensure_ascii=False, sort_keys=True,
                                        separators=(",", ":")).encode()).hexdigest()
    breaths = {s["ability_name"]: s for s in monster_action_specs({**record, "catalog": catalog})}
    from .monster_exposures import exposure_specs
    exposures={s['name']:s for s in exposure_specs(record)}
    breaths.update({name:s for name,s in exposures.items() if s['execution_status']=='native'})
    from .monster_runtime import breath_contract
    from .monster_passives import passive_specs
    passives=passive_specs(record)
    from .monster_riders import combat_rider_specs
    riders={spec['ability_index']:spec for spec in combat_rider_specs(record)['on_hit']}
    bound_indices={p['source_ability_index'] for family in ('damage_immunities','damage_resistances','damage_vulnerabilities') for p in passives.get(family,[])}
    from .damage_profiles import weapon_defense
    bound_indices.update(i for i,a in enumerate(record.get('abilities') or []) if weapon_defense({'abilities':[a]},{'kind':'weapon','magical':False})==0)
    if passives.get('regeneration'):bound_indices.add(passives['regeneration']['source_ability_index'])
    rules = []
    for index, attack in enumerate(monster.get("attacks") or []):
        parsed = parse_attack_entry(attack, index)
        gaps = ([parsed["reason"]] if parsed["status"] != "ready" else [])
        if parsed.get("riders") or parsed.get("notes"):
            gaps.append("Efeito adicional do ataque ainda exige resolução assistida.")
        text = str(attack.get("raw") or attack.get("notes") or attack.get("damage") or "")
        rules.append({"id": f"{identity}:attack:{index}", "name": parsed["name"],
                      "source_pointer": f"/attacks/{index}", "text": text,
                      "category": "attack", "clauses": _clauses(text), "parameters": parsed,
                      "execution": {"status": "native_attack" if not gaps else "assisted",
                                    "handler": "combat.resolve_attack" if parsed["status"] == "ready" else None,
                                    "gaps": gaps}})
    for index, ability in enumerate(monster.get("abilities") or []):
        name, text = str(ability.get("name") or ""), str(ability.get("description") or "")
        parameters = classify_ability(name, text)
        gaps = ["Texto preservado; regra completa ainda sem adaptador de execução validado."]
        if parameters.get("kind") == "spellcasting" and not (parameters.get("spellcasting") or {}).get("named_spells"):
            gaps.append("Repertório de magias não declarado; nível de conjurador não define magias conhecidas.")
        execution={"status":"assisted","handler":None,"gaps":gaps}
        if name in breaths:
            bound=breath_contract(record,name)
            if bound['execution_status']=='native':execution={'status':'native_exposure' if bound.get('requires_eye_contact') else 'native_breath','handler':'combat_effects.monster_breath','gaps':[]}
        elif index in riders:
            execution={'status':'native_on_hit','handler':'monster_conditions.apply_on_hit','gaps':[]}
        elif index in bound_indices:
            execution={'status':'partial','handler':'monster_runtime','gaps':['Componente de dano/regeneração automático; demais regras do texto continuam assistidas.']}
        rules.append({"id": f"{identity}:ability:{index}", "name": name,
                      "source_pointer": f"/abilities/{index}", "text": text,
                      "category": parameters["kind"], "clauses": _clauses(text),
                      "parameters": parameters, "action_spec": breaths.get(name),
                      "execution": execution})
    image = monster.get("image_path")
    attribution = monster.get("image_attribution") or ""
    origin = "missing" if not image else ("generated_registration" if attribution.startswith("Mesa Omnisvera") else "external_catalog")
    return {"schema_version": 1, "monster_id": identity, "name": monster.get("name"),
            "revision": revision, "source": source, "source_record": record,
            "movement": {"raw": monster.get("movement"), "modes": movement_modes(monster.get("movement")),
                         "pending": movement_pending(monster.get("movement"))},
            "art": {"path": image, "origin": origin, "attribution": attribution or None,
                    "catalog_reuse_count": art_usage_count,
                    "license": monster.get("image_license"), "license_url": monster.get("image_license_url"),
                    "source_url": monster.get("image_source_url"), "file_verified": False,
                    "user_upload_verified": False, "unique_portrait_verified": None},
            "rules": rules, "coverage": {"attacks": len(monster.get("attacks") or []),
                                         "abilities": len(monster.get("abilities") or []),
                                         "source_preserved": True,
                                         "fully_automated": False}}
