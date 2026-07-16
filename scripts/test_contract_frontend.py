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
    hub = FRONTEND / "pages" / "ConclaveHub.tsx"
    quick = FRONTEND / "components" / "QuickContractPanel.tsx"
    scene = FRONTEND / "pages" / "ScenePanel.tsx"
    sheet = FRONTEND / "pages" / "PlayableCharacterSheet.tsx"
    chat = FRONTEND / "pages" / "ChatVault.tsx"
    api = FRONTEND / "api.ts"
    app = FRONTEND / "App.tsx"
    styles = FRONTEND / "styles.css"
    vite = FRONTEND_ROOT / "vite.config.ts"

    contains(
        api,
        "export type ContractRecord",
        "export type ReputationLedger",
        "newContractRequestId",
        "listContracts",
        "createContract",
        "acceptContract",
        "setContractObjectiveStatus",
        "linkContractScene",
        "createContractScene",
        "approveContractReward",
        "deliverContractReward",
        "revertReputation",
        '"/contracts"',
        "/reputation",
    )
    contains(
        hub,
        "Conclave dos Errantes",
        "Disponíveis",
        "Aceitos",
        "Em andamento",
        "Concluídos",
        "Falhos/abandonados",
        "Histórico",
        "Nenhum contrato publicado.",
        "Nenhum contrato disponível no momento.",
        "Recompensa ainda não revelada.",
        "private_briefing",
        "isGm && contract.private_briefing",
        "window.confirm",
        "deliverContractReward",
        "omnisvera-character-state",
        "onOpenScene(link.scene_id)",
        "mediaUrlFromVaultPath",
    )
    contains(
        quick,
        'role="dialog"',
        'aria-modal="true"',
        'event.key === "Escape"',
        "Objetivo principal",
        "Recompensa pública",
        "Abrir cena relacionada",
        "Abrir Conclave",
        "Nenhum contrato disponível no momento.",
    )
    contains(
        scene,
        "contract_links",
        "omnisvera-open-contract",
        "omnisvera_selected_scene",
        "Contratos vinculados",
    )
    contains(
        app,
        '"conclave"',
        "<ConclaveHub",
        "<QuickContractPanel",
        "openConclave",
        "openScenePanel",
        "omnisvera-open-contract",
        "omnisvera-open-scene",
        'page === "chat"',
        'page === "sheet"',
        'page === "scene"',
    )
    contains(
        styles,
        ".conclave-page",
        ".contract-board",
        ".contract-detail",
        ".quick-contract-panel",
        ".quick-contract-drawer",
        ".scene-contract-links",
        "@media (max-width: 640px)",
        "calc(100vw - 1.3rem)",
    )
    contains(vite, '"/contracts"', '"/reputation"', '"/scenes"', '"/characters"')
    contains(sheet, "PlayableCharacterSheet", "omnisvera-open-dice-tray")
    contains(chat, "chatVault", "initialQuestion")

    print("CONTRACT_FRONTEND_PASS")


if __name__ == "__main__":
    main()
