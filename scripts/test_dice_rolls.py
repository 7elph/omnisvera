from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "omnisvera-agent" / "backend"))

from app.dice_rolls import (  # noqa: E402
    MAX_DICE,
    MAX_SIDES,
    RollSpec,
    can_view_roll,
    complete_roll_request,
    create_roll,
    create_roll_request,
    get_roll,
    init_dice_rolls,
    list_roll_requests,
    list_rolls,
    parse_formula,
    resolve_character_roll,
    roll_formula,
    void_roll,
)


class SequenceRng:
    def __init__(self, values: list[int]):
        self.values = iter(values)

    def __call__(self, minimum: int, maximum: int) -> int:
        value = next(self.values)
        assert minimum <= value <= maximum
        return value


class FailRng:
    def __call__(self, minimum: int, maximum: int) -> int:
        raise AssertionError("Uma repetição idempotente não deve gerar novos números")


def expect_error(callback, message: str = "") -> None:
    try:
        callback()
    except (PermissionError, ValueError) as error:
        if message:
            assert message.casefold() in str(error).casefold(), str(error)
    else:
        raise AssertionError("Era esperado um erro")


def sample_definition() -> dict:
    return {
        "name": "Vezemir",
        "attributes": {"strength": 16},
        "attribute_modifiers": {"strength": 3, "dexterity": 0},
        "defenses": {"saving_throw": "16"},
        "attacks": [
            {"id": "melee", "name": "Corpo a corpo", "attack_bonus": 4},
            {"id": "ranged", "name": "À distância", "attack_bonus": None},
        ],
        "abilities": {"class": "Sem fórmula estruturada."},
    }


def sample_inventory() -> list[dict]:
    return [
        {
            "id": 1,
            "item_path": "Items/Grisalma.md",
            "item_title": "Grisalma",
            "equipped": True,
            "damage_formula": "2d6",
        }
    ]


def main() -> None:
    assert parse_formula("1d20").formula == "1d20"
    assert parse_formula("1d20+2").modifier == 2
    assert parse_formula("1d20-1").modifier == -1
    assert parse_formula("2d6").count == 2
    for formula in ("1d20*2", "eval(1)", "1d20;import os", "(1d20)", "2d6/2", "texto"):
        expect_error(lambda formula=formula: parse_formula(formula))
    expect_error(lambda: parse_formula(f"{MAX_DICE + 1}d6"), "quantidade")
    expect_error(lambda: parse_formula(f"1d{MAX_SIDES + 1}"), "lados")
    expect_error(lambda: parse_formula("1d20+1001"), "modificador")

    deterministic = roll_formula("2d6+3", SequenceRng([2, 5]))
    assert deterministic["individual_results"] == [2, 5]
    assert deterministic["subtotal"] == 7
    assert deterministic["total"] == 10

    attribute = resolve_character_roll(sample_definition(), sample_inventory(), "attribute", "strength")
    assert attribute.formula == "1d20+3"
    protection = resolve_character_roll(sample_definition(), sample_inventory(), "saving_throw", None)
    assert protection.formula == "1d20" and protection.target_value == 16
    attack = resolve_character_roll(sample_definition(), sample_inventory(), "attack", "melee")
    assert attack.formula == "1d20+4"
    damage = resolve_character_roll(sample_definition(), sample_inventory(), "damage", "Items/Grisalma.md")
    assert damage.formula == "2d6"
    expect_error(lambda: resolve_character_roll(sample_definition(), sample_inventory(), "attack", "ranged"), "não está configurado")
    expect_error(lambda: resolve_character_roll(sample_definition(), sample_inventory(), "ability", "Frenesi"), "não possui fórmula")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        database = Path(directory) / "dice.sqlite3"
        init_dice_rolls(database)
        event, created = create_roll(
            database,
            request_id="roll-test-0001",
            campaign_id="omnisvera",
            character_id="vezemir",
            actor_id="vezemir",
            actor_role="player",
            roll_type="attribute",
            label="Teste de Força",
            formula=attribute.formula,
            visibility="table",
            target_value=12,
            source=attribute.source,
            source_id=attribute.source_id,
            rng=SequenceRng([10]),
        )
        assert created and event["total"] == 13 and event["outcome"] == "success"
        same, created_again = create_roll(
            database,
            request_id="roll-test-0001",
            campaign_id="omnisvera",
            character_id="vezemir",
            actor_id="vezemir",
            actor_role="player",
            roll_type="attribute",
            label="Teste de Força",
            formula=attribute.formula,
            visibility="table",
            rng=FailRng(),
        )
        assert not created_again and same["id"] == event["id"] and same["total"] == 13
        expect_error(
            lambda: create_roll(
                database,
                request_id="roll-test-0001",
                campaign_id="omnisvera",
                actor_id="outro",
                actor_role="player",
                roll_type="free",
                label="Colisão",
                formula="1d6",
                visibility="table",
            ),
            "já utilizado",
        )

        private, _ = create_roll(
            database,
            request_id="roll-private-01",
            campaign_id="omnisvera",
            actor_id="vezemir",
            actor_role="player",
            character_id="vezemir",
            roll_type="free",
            label="Privada",
            formula="1d6",
            visibility="private",
            rng=SequenceRng([4]),
        )
        secret, _ = create_roll(
            database,
            request_id="roll-secret-001",
            campaign_id="omnisvera",
            actor_id="master",
            actor_role="gm",
            roll_type="free",
            label="Segredo",
            formula="1d20",
            visibility="gm",
            target_value=15,
            target_hidden=True,
            rng=SequenceRng([18]),
        )
        assert can_view_roll(event, access_mode="player", profile_id="varkh", actor_id="varkh")
        assert can_view_roll(private, access_mode="player", profile_id="vezemir", actor_id="vezemir")
        assert not can_view_roll(private, access_mode="player", profile_id="varkh", actor_id="varkh")
        assert not can_view_roll(secret, access_mode="player", profile_id="vezemir", actor_id="vezemir")
        assert can_view_roll(secret, access_mode="gm", profile_id=None, actor_id="master")
        assert len(list_rolls(database)) == 3

        voided = void_roll(database, roll_id=event["id"], actor_id="master", reason="Clique duplicado na mesa")
        assert voided["voided"] and voided["total"] == event["total"]
        expect_error(lambda: void_roll(database, roll_id=event["id"], actor_id="master", reason="Outra vez"), "já anulada")

        roll_request, request_created = create_roll_request(
            database,
            request_id="request-roll-01",
            campaign_id="omnisvera",
            character_id="vezemir",
            requested_by="master",
            spec=RollSpec("attribute", "Vezemir — Teste de Força", "1d20+3", "character_attribute", "strength"),
            visibility="owner",
            target_value=13,
            target_hidden=True,
        )
        assert request_created and list_roll_requests(database, character_id="vezemir")[0]["id"] == roll_request["id"]
        expect_error(
            lambda: complete_roll_request(
                database,
                request_id=roll_request["id"],
                completion_request_id="complete-wrong-1",
                actor_id="varkh",
                actor_role="player",
            ),
            "outro personagem",
        )
        completed, completion_created = complete_roll_request(
            database,
            request_id=roll_request["id"],
            completion_request_id="complete-roll-01",
            actor_id="vezemir",
            actor_role="player",
            rng=SequenceRng([11]),
        )
        assert completion_created and completed["total"] == 14 and completed["outcome"] == "success"
        repeated, repeated_created = complete_roll_request(
            database,
            request_id=roll_request["id"],
            completion_request_id="complete-roll-01",
            actor_id="vezemir",
            actor_role="player",
        )
        assert not repeated_created and repeated["id"] == completed["id"]
        expect_error(
            lambda: complete_roll_request(
                database,
                request_id=roll_request["id"],
                completion_request_id="complete-roll-02",
                actor_id="vezemir",
                actor_role="player",
            ),
            "já foi concluída",
        )

        gm_only_request, _ = create_roll_request(
            database,
            request_id="request-gm-only",
            campaign_id="omnisvera",
            character_id="vezemir",
            requested_by="master",
            spec=RollSpec("attribute", "Teste secreto", "1d20+3", "character_attribute", "strength"),
            visibility="gm",
        )
        expect_error(
            lambda: complete_roll_request(
                database,
                request_id=gm_only_request["id"],
                completion_request_id="complete-gm-only",
                actor_id="vezemir",
                actor_role="player",
            ),
            "reservada ao Mestre",
        )
        assert get_roll(database, completed["id"])["individual_results"] == [11]

    print("DICE_ROLL_ENGINE_PASS")


if __name__ == "__main__":
    main()
