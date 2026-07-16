from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "omnisvera-agent" / "frontend" / "src"
FRONTEND_ROOT = ROOT / "omnisvera-agent" / "frontend"


def contains(path: Path, *needles: str) -> None:
    content = path.read_text(encoding="utf-8")
    for needle in needles:
        assert needle in content, f"{needle!r} ausente em {path.name}"


def main() -> None:
    full = FRONTEND / "pages" / "ScenePanel.tsx"
    quick = FRONTEND / "components" / "QuickScenePanel.tsx"
    character = FRONTEND / "components" / "QuickCharacterSheet.tsx"
    api = FRONTEND / "api.ts"
    app = FRONTEND / "App.tsx"
    styles = FRONTEND / "styles.css"
    vite = FRONTEND_ROOT / "vite.config.ts"

    contains(
        full,
        "getActiveScene",
        "createScene",
        "addSceneParticipant",
        "declareSceneAction",
        "requestSceneActionRoll",
        "resolveSceneAction",
        "rejectSceneAction",
        "applySceneConsequence",
        'consequence("remove_condition"',
        "Remover condição",
        "revealSceneElement",
        "omnisvera-open-character",
        "scene.events",
        "Nenhuma cena ativa",
        "O mestre ainda não iniciou uma cena.",
    )
    contains(
        quick,
        'role="dialog"',
        'aria-modal="true"',
        'event.key === "Escape"',
        "declareSceneAction",
        "omnisvera-open-character",
        "setInterval",
        "O mestre ainda não iniciou uma cena.",
    )
    contains(character, "omnisvera-open-character", "setSelectedId(characterId)", "setOpen(true)")
    contains(
        api,
        "export type GameScene",
        "getActiveScene",
        "declareSceneAction",
        "requestSceneActionRoll",
        "applySceneConsequence",
        "scene_id",
        "action_id",
    )
    contains(app, 'type Page = "chat"', 'page === "scene"', "<ScenePanel", "<QuickScenePanel")
    contains(vite, '"/gm"', '"/characters"', '"/rolls"', '"/scenes"', '"/media"')
    contains(
        styles,
        ".scene-page",
        ".scene-participant-grid",
        ".scene-action-composer",
        ".scene-history",
        ".quick-scene-panel",
        ".quick-scene-drawer",
        "@media (max-width: 640px)",
        "calc(100vw - 1.3rem)",
        "overflow-wrap: anywhere",
    )

    print("SCENE_FRONTEND_PASS")


if __name__ == "__main__":
    main()
