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
    page = SRC / "pages" / "NpcDirectory.tsx"
    quick = SRC / "components" / "QuickNpcPanel.tsx"
    api = SRC / "api.ts"
    app = SRC / "App.tsx"
    scene = SRC / "pages" / "ScenePanel.tsx"
    contract = SRC / "pages" / "ConclaveHub.tsx"
    sheet = SRC / "pages" / "PlayableCharacterSheet.tsx"
    chat = SRC / "pages" / "ChatVault.tsx"
    styles = SRC / "styles.css"
    vite = FRONTEND / "vite.config.ts"

    checks += contains(api, "export type NpcRecord", "export type NpcMemory", "export type NpcRelationship", "listNpcs", "getNpc", "createNpcMemory", "recordNpcEncounter", "linkNpcContract")
    checks += contains(page, "Diretório de NPCs", "Nenhum NPC registrado", "Filtrar por facção", "Relações", "Memórias e crenças", "Promessas e dívidas", "Crença falsa", "Contradizer", "Registrar encontro", "Vincular contrato", "Histórico auditável")
    checks += contains(quick, 'role="dialog"', 'aria-modal="true"', "Abrir perfil completo", "Copiar resumo autorizado", "Prioridades do Mestre")
    checks += contains(scene, "Adicionar NPC existente", "recordNpcEncounter", "omnisvera-open-npc", "npc_source: `npc:${npc.id}`")
    checks += contains(contract, "NPCs relacionados", "linkNpcContract", "omnisvera-open-npc")
    checks += contains(sheet, "NPCs conhecidos", "listNpcs({ character_id: selectedId })", "omnisvera-open-npc")
    checks += contains(chat, "npcForMessage", "Abrir perfil jogável", "listNpcs")
    checks += contains(app, '"npcs"', "<NpcDirectory", "<QuickNpcPanel")
    checks += contains(styles, ".npc-layout", ".npc-profile", ".quick-npc-drawer", "@media (max-width: 640px)", "max-height: 88vh")
    checks += contains(vite, '"/npcs"')

    assert checks >= 29, checks
    print(f"NPC_MEMORY_FRONTEND_PASS {checks}/29")


if __name__ == "__main__":
    main()
