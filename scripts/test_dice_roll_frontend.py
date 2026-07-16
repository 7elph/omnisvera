from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "omnisvera-agent" / "frontend" / "src"


def contains(path: Path, *needles: str) -> None:
    content = path.read_text(encoding="utf-8")
    for needle in needles:
        assert needle in content, f"{needle!r} ausente em {path.name}"


def main() -> None:
    tray = FRONTEND / "components" / "DiceTray.tsx"
    quick = FRONTEND / "components" / "QuickCharacterSheet.tsx"
    full = FRONTEND / "pages" / "PlayableCharacterSheet.tsx"
    api = FRONTEND / "api.ts"
    app = FRONTEND / "App.tsx"
    styles = FRONTEND / "styles.css"

    contains(
        tray,
        'role="dialog"',
        'aria-modal="true"',
        'aria-live="assertive"',
        "COMMON_DICE",
        "createFreeRoll",
        "individual_results.join",
        "listRollHistory",
        "listPendingRollRequests",
        "disabled={busy}",
        "visibility === \"gm\"",
        "voidDiceRoll",
        'event.key === "Escape"',
    )
    contains(
        full,
        "rollCharacterAction",
        'aria-live="assertive"',
        "omnisvera-open-dice-tray",
        'onRoll("attribute"',
        'onRoll("attack"',
        'onRoll("damage"',
    )
    contains(
        quick,
        "rollCharacterAction",
        "Rolar FOR",
        "Rolar proteção",
        "Rolar ataque",
        "disabled={rolling",
        "omnisvera-open-dice-tray",
    )
    contains(
        api,
        "createFreeRoll",
        "rollCharacterAction",
        "listRollHistory",
        "completeRollRequest",
        "voidDiceRoll",
        "request_id",
    )
    contains(app, "<DiceTray", "<QuickCharacterSheet")
    contains(
        styles,
        ".dice-tray-trigger",
        ".dice-tray-backdrop",
        ".dice-roll-card",
        ".quick-roll-actions",
        "@media (max-width: 640px)",
        "max-height: 92vh",
        "overflow-x: hidden",
    )

    print("DICE_ROLL_FRONTEND_PASS")


if __name__ == "__main__":
    main()
