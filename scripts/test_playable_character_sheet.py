from __future__ import annotations

import tempfile
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))

from app.character_play import (  # noqa: E402
    apply_character_action,
    attribute_modifier,
    build_character_definition,
    compose_character_view,
    get_or_create_state,
    list_character_events,
    load_definition_overrides,
    revert_character_event,
    update_definition_overrides,
)
from app.player_inventory import list_inventory, upsert_inventory  # noqa: E402


def sample_sheet() -> dict:
    return {
        "profile_id": "vezemir",
        "character_path": "Characters/Individual/Vezemir.md",
        "character_title": "Vezemir",
        "steps": [
            {"key": "attributes", "fields": {"strength": 13, "dexterity": 10, "constitution": 16, "intelligence": 8, "wisdom": 10, "charisma": 4}, "guide": {}},
            {"key": "race", "fields": {"race": "Meio-Elfo", "movement": "9 m", "racial_abilities": "Visão na penumbra confirmada."}, "guide": {}},
            {"key": "character_class", "fields": {"class_name": "Guerreiro", "level": 1, "hit_points": 13, "saving_throw": "16", "base_attack": 2, "experience": 0, "class_abilities": "Combate marcial."}, "guide": {}},
            {"key": "attacks", "fields": {"melee_bonus": 2, "ranged_bonus": 1, "attack_notes": "Grisalma"}, "guide": {}},
            {"key": "equipment", "fields": {"equipment_list": "Grisalma", "starting_gold": 90}, "guide": {}},
            {"key": "armor", "fields": {"armor_class": 22}, "guide": {}},
            {"key": "magic", "fields": {"known_magic": "", "magic_notes": ""}, "guide": {}},
            {"key": "details", "fields": {"physical_description": "Alto e forte.", "personality": "Reservado.", "background": "Foi criado em Avenor.", "goals": "Busca o dragão."}, "guide": {}},
        ],
    }


def sample_note() -> dict:
    return {
        "path": "Characters/Individual/Vezemir.md",
        "title": "VEZEMIR — O BASTARDO DE FERRO",
        "updated_at": "2026-07-16T00:00:00+00:00",
        "frontmatter": {
            "race": "Meio-Elfo",
            "class": "Guerreiro",
            "level": 1,
            "visibility": "Público",
            "thumbnail": "zz_media/thumbnails/th_vezemir.png",
            "cover": "zz_media/characters/vezemir.png",
            "location": "[[Floresta de Avenor]]",
            "status": "Vivo",
            "canon_status": "Working Canon",
        },
        "content": """# Vezemir

## O que os jogadores sabem

Vezemir é um guerreiro meio-elfo.

## Relações

Elarion Vaelthor foi seu mentor.

## Segredos do Mestre

Isto não pode aparecer.
""",
    }


def main() -> None:
    assert attribute_modifier(13) == 1
    assert attribute_modifier(10) == 0
    assert attribute_modifier(4) == -3

    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "character.sqlite3"
        upsert_inventory(
            database,
            profile_id="vezemir",
            item_path="Items/Grisalma.md",
            item_title="Grisalma",
            quantity=1,
            equipped=True,
            notes=None,
        )
        inventory = list_inventory(database, "vezemir")
        definition = build_character_definition(
            profile_id="vezemir",
            note=sample_note(),
            sheet=sample_sheet(),
            inventory=inventory,
            access_level="gm",
        )
        assert definition["name"] == "Vezemir"
        assert definition["epithet"] == "O Bastardo de Ferro"
        assert definition["portrait"] == "zz_media/thumbnails/th_vezemir.png"
        assert definition["defenses"]["armor_class"] == 22
        assert definition["defenses"]["initiative"] is None
        assert definition["attacks"][0]["damage"] is None
        assert "Isto não pode aparecer" not in definition["public_description"]

        state = get_or_create_state(
            database,
            profile_id="vezemir",
            sheet=sample_sheet(),
            definition=definition,
        )
        assert state["current_hp"] == 13
        assert state["maximum_hp"] == 13

        gm_view = compose_character_view(
            definition={**definition, "gm_fields": {"notes": "Privado"}},
            state=state,
            inventory=inventory,
            access_level="gm",
        )
        assert gm_view["definition"]["gm_fields"]["notes"] == "Privado"
        public_definition = build_character_definition(
            profile_id="vezemir",
            note=sample_note(),
            sheet=sample_sheet(),
            inventory=inventory,
            access_level="public",
        )
        public_view = compose_character_view(
            definition=public_definition,
            state=None,
            inventory=inventory,
            access_level="public",
        )
        assert public_view["state"] is None
        assert public_view["inventory"] == []
        assert "gm_fields" not in public_view["definition"]
        assert "attributes" not in public_view["definition"]

        damage = apply_character_action(
            database,
            character_id="vezemir",
            actor_id="vezemir",
            actor_role="player",
            action="damage",
            payload={"amount": 5},
        )
        assert damage["after"] == 8
        damaged = get_or_create_state(database, profile_id="vezemir", sheet=sample_sheet(), definition=definition)
        assert damaged["current_hp"] == 8

        apply_character_action(
            database,
            character_id="vezemir",
            actor_id="master",
            actor_role="gm",
            action="heal",
            payload={"amount": 99},
        )
        healed = get_or_create_state(database, profile_id="vezemir", sheet=sample_sheet(), definition=definition)
        assert healed["current_hp"] == 13

        try:
            apply_character_action(
                database,
                character_id="varkh",
                actor_id="vezemir",
                actor_role="player",
                action="damage",
                payload={"amount": 1},
            )
        except PermissionError:
            pass
        else:
            raise AssertionError("Outro jogador não pode alterar uma ficha alheia")

        apply_character_action(
            database,
            character_id="vezemir",
            actor_id="vezemir",
            actor_role="player",
            action="add_condition",
            payload={"condition": "Caído"},
        )
        condition_event = list_character_events(database, "vezemir")[0]
        assert condition_event["event_type"] == "add_condition"
        reverted = revert_character_event(
            database,
            character_id="vezemir",
            event_id=condition_event["id"],
            actor_id="master",
        )
        assert reverted["reverted_at"]
        after_revert = get_or_create_state(database, profile_id="vezemir", sheet=sample_sheet(), definition=definition)
        assert "Caído" not in after_revert["conditions"]

        overrides = update_definition_overrides(
            database,
            character_id="vezemir",
            actor_id="master",
            fields={"initiative": 1, "gm_fields": {"notes": "Somente Mestre"}},
        )
        assert overrides["initiative"] == 1
        assert load_definition_overrides(database, "vezemir")["gm_fields"]["notes"] == "Somente Mestre"

        item_event = apply_character_action(
            database,
            character_id="vezemir",
            actor_id="vezemir",
            actor_role="player",
            action="unequip_item",
            payload={"item_path": "Items/Grisalma.md"},
        )
        assert item_event["after"]["equipped"] is False
        revert_character_event(database, character_id="vezemir", event_id=item_event["event_id"], actor_id="master")
        assert list_inventory(database, "vezemir")[0]["equipped"] is True

    frontend = (ROOT / "omnisvera-agent" / "frontend" / "src" / "pages" / "PlayableCharacterSheet.tsx").read_text(encoding="utf-8")
    quick = (ROOT / "omnisvera-agent" / "frontend" / "src" / "components" / "QuickCharacterSheet.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "omnisvera-agent" / "frontend" / "src" / "styles.css").read_text(encoding="utf-8")
    assert "onError={() => setFailed(true)}" in frontend
    assert "Ficha rápida" in quick
    assert "@media (max-width: 640px)" in styles
    assert "max-width: calc(100vw - 2rem)" in styles
    print("PLAYABLE_CHARACTER_SHEET_PASS")


if __name__ == "__main__":
    main()
