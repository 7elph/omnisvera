from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "omnisvera-agent" / "frontend"
SRC = FRONTEND / "src"


def contains(path: Path, *needles: str) -> int:
    content = path.read_text(encoding="utf-8")
    for needle in needles:
        assert needle in content, f"{needle!r} ausente em {path.name}"
    return len(needles)


def main() -> None:
    checks = 0
    page = SRC / "pages" / "WorldMapPage.tsx"
    quick = SRC / "components" / "QuickAccessMenu.tsx"
    app = SRC / "App.tsx"
    api = SRC / "api.ts"
    styles = SRC / "styles.css"
    character = SRC / "pages" / "PlayableCharacterSheet.tsx"
    scene = SRC / "pages" / "ScenePanel.tsx"
    contract = SRC / "pages" / "ConclaveHub.tsx"
    npc = SRC / "pages" / "NpcDirectory.tsx"
    dice = SRC / "components" / "DiceTray.tsx"

    checks += contains(app, 'lazy(() => import("./pages/WorldMapPage"))', "<Suspense", 'page === "map"', "<QuickAccessMenu", "triggerHidden")
    checks += contains(api, "export type WorldMapRecord", "export type WorldLocationRecord", "export type JourneyRecord", "listWorldMaps", "listWorldLocations", "createTravelRoute", "createJourney", "advanceJourney", "transitionJourney")
    checks += contains(page, "Mapa, locais e viagens", "Lista acessível", 'role="list"', "Nenhum mapa registrado", "Posicionar no mapa", "Revelar rumor", "Revelar local", "Nova rota unidirecional", "Planejar viagem", "Confirmar chegada", "Viagem planejada. Ninguém foi movido ainda.")
    checks += contains(page, "filteredLocations", "knowledge_level", "world-route-layer", "mediaUrlFromVaultPath", "activeJourney", "progress_current", "onOpenScene", "onOpenContract")
    checks += contains(quick, "Acesso rápido", "Ficha rápida", "Cena rápida", "Contrato", "Dados", "Mapa e viagem", "omnisvera-open-dice-tray", "omnisvera-open-quick-scene", "omnisvera-open-quick-contract")
    checks += contains(dice, "triggerHidden", "omnisvera-open-dice-tray")
    checks += contains(character, "Abrir no mapa", "omnisvera-open-map")
    checks += contains(scene, "Abrir mapa e viagens", "omnisvera-open-map")
    checks += contains(contract, "Abrir local e planejar viagem", "omnisvera-open-map")
    checks += contains(npc, "Abrir mapa", "omnisvera-open-map")
    checks += contains(styles, ".quick-access-drawer", ".world-map-canvas", ".world-location-list", ".journey-card", "@media (max-width: 760px)", "overflow-x: auto", "grid-template-columns: minmax(0,1fr)")
    assert "react-leaflet" not in (FRONTEND / "package.json").read_text(encoding="utf-8")
    checks += 1
    assert checks >= 55, checks
    print(f"WORLD_TRAVEL_FRONTEND_PASS {checks}/55")


if __name__ == "__main__":
    main()
