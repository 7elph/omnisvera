"""Idempotent Session 5 content installation. Rehearsal by default; --apply uses local GM API.

No gameplay transitions, rewards, character writes or existing record updates.
Credentials never enter reports. Runtime evidence/backups are private and ignored.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT.parent
DOCS = VAULT / "CAMPANHA/Sessoes/Sessao_05"
DB = ROOT / "backend/data/omnisvera_companion.sqlite3"
PREFIX = "sage-session05-20260925"
SECRET = "S05_PRIVATE_PREPARATION_ONLY"


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


def snapshot(db):
    """Capture existing domain rows; audit/index activity intentionally excluded."""
    result = {}
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as conn:
        names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for name in names:
            if (name.startswith(("character", "player_", "game_sessions", "session_custom", "session_workspace", "npcs", "scenes", "contracts"))
                    and name not in {"session_workspace_presence"}):
                query = 'SELECT * FROM "' + name + '"'
                if name == "scenes":
                    query += " WHERE request_id NOT LIKE '" + PREFIX + "-%'"
                result[name] = {digest(row) for row in conn.execute(query)}
    return result


def post(client, path, key, **body):
    response = client.post(path, json={"request_id": PREFIX + "-" + key, **body})
    if response.status_code >= 400:
        raise RuntimeError(f"{path}: HTTP {response.status_code}: {response.text[:600]}")
    return response.json()


def install(client, db):
    sessions = client.get("/gm/sessions").json()
    conflicts = [s for s in sessions if s.get("session_number") == 5 and s.get("request_id") != PREFIX + "-session"]
    if conflicts:
        raise RuntimeError("Existing Session 5 requires reconciliation, not overwrite")
    master = (DOCS / "SESSION_05_MASTER.md").read_text(encoding="utf-8")
    session = post(client, "/gm/sessions", "session", title="Sessão 5 — Ecos sob a Montanha", session_number=5,
                   private_notes=SECRET + "\nPreparação não jogada. Roteiro completo no Vault: CAMPANHA/Sessoes/Sessao_05/SESSION_05_MASTER.md. Morthak nas costas de Vezemir; Dorn acompanha; Varkh NPC, posição pendente. Não conceder recompensas nem ativar cenas em lote.")
    assert session["status"] == "planned", "Do not modify an already started Session 5"
    map_record = post(client, "/gm/world/maps", "map", title="Sessão 5 — estrada das encostas (esquema)",
                      image_path="zz_media/maps/session05_route_schematic.svg", map_type="schematic", width=1200, height=800,
                      visibility="gm", public_description="Esquema de conexões, sem escala e sem fronteiras oficiais.",
                      private_description=SECRET + ": revelar somente quando útil; não altera mapa ativo.")
    # The spatial atlas and the table have separate map registries. Reuse the existing
    # domain operation to register this asset without activating it or touching old maps.
    sys.path.insert(0, str(ROOT / "backend"))
    from app.session_workspace import list_workspace_maps, set_workspace_map
    image_path = "zz_media/maps/session05_route_schematic.svg"
    matching = [m for m in list_workspace_maps(db) if m["image_path"] == image_path]
    table_map = matching[0] if matching else set_workspace_map(db, title="Sessão 5 — esquema das encostas", image_path=image_path, visible_to_players=False)
    places = [("Retirada das montanhas", 63, 26), ("Estrada da carga", 74, 44), ("Entrada da capital anã", 51, 64), ("Oficinas do Canal", 36, 78), ("Sede anã do Conclave", 54, 85)]
    locations = []
    for i, (name, x, y) in enumerate(places):
        locations.append(post(client, "/gm/world/locations", f"place-{i}", map_id=map_record["id"], name=name,
            location_type="custom", x=x, y=y, visibility="gm", discovered_by_default=False,
            canon_status="preparação; posição esquemática", public_description="Ponto de referência da Sessão 5; posição sem escala.", private_description=SECRET))
    npc_specs = [
        ("Tessa Viga-Clara", "Anã", "Trabalhadora", "Quer salvar pessoas e ferramentas. Fala enquanto trabalha.", "Ajuda na estrada pode render abrigo, não bônus automático."),
        ("Orda Sel", "Anã", "Comerciante", "Mantém entregas e salários; pesa promessas.", "Não identifica espécie dracônica; não comprar a escama sem decisão da mesa."),
        ("Brunna Calha", "Anã", "Capitã / aventureira B", "Veterana responsável por patrulhas; pergunta por saídas.", "Não recebe tarefa de matar dragões pelos PCs."),
        ("Edda Ruun", "Anã", "Delegada civil", "Separa visto, ouvido e inferido.", "Não concede prêmio antigo sem conferir contrato; não é rainha."),
        ("Dagna Fio", "Anã", "Estudiosa / artífice", "Examina material com consentimento.", "A escama não comprova dono nem espécie; abrasão não prova duelo."),
        ("Ivo", "Humano", "Aventureiro C iniciante", "Escolta carga e quer carta de referência.", "Parceiro de Neri; aprende com a própria missão, sem virar servo da party."),
        ("Neri", "Humana", "Aventureira C iniciante", "Escolta carga; avalia custo de cumprir promessas.", "Parceira de Ivo; pode resolver problema por outra abordagem."),
        ("Seris Tal", "Elfa", "Aventureira A / perita", "Investiga cisterna e contratos de conservação.", "Comparável ao grupo, sem conhecer destino de Elarion ou origem de Dorn."),
        ("Maera Voss", "Antropa — traços de coruja", "Veterana A", "Prepara escolta de pesquisadores em galeria instável.", "Muito mais experiente em combate; agenda própria, não resolve dragões pela party."),
        ("Liora Tamel", "Antropa — traços cervídeos", "Escrivã de Nimalia", "Confere nomes e recibos antes de títulos.", "Entrega convocação na cena 6; não possui autoridade de comando sobre Dorn."),
    ]
    npcs = []
    for i, (name, race, role, public, private) in enumerate(npc_specs):
        npcs.append(post(client, "/gm/npcs", f"npc-{i}", name=name, race=race, class_or_role=role,
            public_description=public, private_description=SECRET + ": " + private,
            visible_to_players=False, canonical_status="PREPARAÇÃO DO MESTRE — ainda não encontrado", current_location="Preparação da Sessão 5"))
    scenes = []
    scene_data = [
        ("O recuo", 0, "A trilha desce. Pequenos animais atravessam o caminho rumo ao vale.", "Escolher retirada e proteger o grupo.", "Cena 1 —"),
        ("A carga que não pode esperar", 1, "Uma carroça bloqueia a drenagem. Trabalhadores e escoltas procuram uma saída.", "Decidir como lidar com a carga e os animais.", "Cena 2 —"),
        ("Uma cidade em vários turnos", 2, "Oficinas, cargas e aventureiros seguem agendas diferentes.", "Conhecer pessoas e prioridades da capital anã.", "Cena 3 —"),
        ("O que uma escama não conta", 3, "O ferreiro pede autorização para examinar a peça e ouvir sua origem.", "Distinguir evidência de hipótese.", "Cena 4 —"),
        ("O relatório e as prioridades", 4, "A delegada separa três folhas: visto, ouvido e concluído.", "Relatar reconhecimento e escolher próximos passos.", "Cena 5 —"),
        ("Os primeiros nomes", 4, "Uma mensageira pede falar com os participantes da primeira incursão.", "Ouvir o pedido e decidir como responder.", "Cena 6 —"),
    ]
    for i, (title, place, public, objective, marker) in enumerate(scene_data):
        section = master.split("## " + marker, 1)[1].split("\n## ", 1)[0]
        notes = SECRET + "\n" + section[:1650] + "\nContinuação: SESSION_05_MASTER.md; nunca publicar notas privadas."
        scenes.append(post(client, "/gm/scenes", f"scene-{i}", session_id=session["id"], title=title,
            location_name=places[place][0], public_description=public, objective=objective,
            private_notes=notes, visibility="gm", checklist={"opening": True, "private_notes": True}))
        scene = scenes[-1]
        post(client, f"/gm/world/scenes/{scene['id']}/location", f"scene-location-{i}", location_id=locations[place]["id"])
        detail = client.get(f"/scenes/{scene['id']}").json()
        npc_indices = [[], [0, 5, 6], [1, 2, 7, 8], [4], [3, 1], [9]][i]
        people = [("npc", f"npc:{npcs[n]['id']}", npcs[n]["name"], None) for n in npc_indices]
        people += [("player_character", None, label, name) for name, label in [("vezemir", "Vezemir"), ("raziel", "Raziel"), ("morthak", "Morthak — transportado por Vezemir")]]
        people.append(("npc", "npc:4", "Dorn 7 — controle do Mestre", None))
        for kind, source, label, character in people:
            if any(p.get("public_label") == label for p in detail.get("participants", [])):
                continue
            response = client.post(f"/gm/scenes/{scene['id']}/participants", json={"participant_type": kind, "npc_source": source,
                "npc_name": label if not character else None, "character_id": character, "public_label": label,
                "visible_to_players": False, "private_status": "Preparado; confirmar presença na abertura. Nenhum recurso alterado."})
            response.raise_for_status()
        post(client, f"/gm/scenes/{scene['id']}/elements", f"clue-{i}", element_type="clue", title=["Animais descendo", "Carga e drenagem", "Agendas independentes", "Escama: evidência e limites", "Visto, ouvido, inferido", "Convocação e desenho"][i],
             public_description=public, private_description=notes[:1900], status="hidden", visibility="gm")
        # Only finish untouched records from this installer; do not overwrite subsequent user edits.
        if not detail.get("map_id") and detail.get("version") == 1:
            fields = {"map_id": table_map["id"], "image_path": image_path, "visibility": "table",
                      "checklist": {key: True for key in ["identity", "map", "opening", "public_image", "characters", "npcs", "creatures", "scenery", "pins", "fog", "clues", "treasure", "interactive_items", "initial_states", "private_notes", "transitions", "player_preview"]}}
            response = client.patch(f"/gm/scenes/{scene['id']}", json={"expected_version": 1, "fields": fields})
            response.raise_for_status()
        elif detail.get("map_id") != table_map["id"]:
            raise RuntimeError("Prepared scene changed externally; refusing overwrite")
    contracts = []
    for i, (title, issuer, brief, objective) in enumerate([
        ("Sessão 5 — consolidar o reconhecimento", "Conclave — sede anã", "Organizar observações sobre as montanhas e riscos da estrada.", "Separar o que foi visto, ouvido e inferido; conferir o contrato anterior antes de pagamento."),
        ("Sessão 5 — convocação de Nimalia", "Ofício de Nimalia", "Reunir testemunhos da primeira incursão à estrutura sob a estrada.", "Convocar Vezemir, Raziel e Varkh; acolher Morthak como testemunha posterior; responder com data possível."),
    ]):
        contract = post(client, "/gm/contracts", f"contract-{i}", session_id=session["id"], title=title, issuer_name=issuer,
            contract_type="investigação", public_summary=brief, public_briefing=brief,
            private_briefing=SECRET + ": " + objective, visibility="gm", risk_label="Preparação; sem pagamento automático")
        contracts.append(contract)
        post(client, f"/gm/contracts/{contract['id']}/objectives", f"objective-{i}", title="Preparar relato e decisão", public_description=brief,
             private_description=objective, status="hidden", revealed_to_players=False)
        post(client, f"/gm/contracts/{contract['id']}/scene-links", f"link-{i}", scene_id=scenes[4 + i]["id"], link_type="preparation")
    post(client, f"/gm/contracts/{contracts[0]['id']}/rewards", "reward", reward_type="favor", label="Abrigo por uma noite — proposta",
         description="Somente se o grupo ajudar Tessa e aceitar a oferta em mesa. Não é pagamento retroativo da missão de dragões.", visibility="gm")
    # Enemies live as private scene elements, not tokens on the currently active production map.
    for i in range(2):
        post(client, f"/gm/scenes/{scenes[1]['id']}/elements", f"wolf-{i}", element_type="threat", title=f"Lobo {i + 1} — encontro opcional",
             public_description="Um lobo fareja perto da carga.", visibility="gm", status="ready",
             private_description="OD2 SRD lobo: PV12 CA14 JP5 Moral6 DV2+2 movimento12m; mordida +2, 1d6; sem tesouro; XP referência175. Dois animais; alimentação/fuga evitam combate. Não aplicar XP automaticamente.")
    # Hidden map tokens; name + map identity prevents duplication on retry.
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as conn:
        token_names = {r[0] for r in conn.execute("SELECT name FROM session_workspace_tokens WHERE map_id=?", (table_map["id"],))}
    for i in range(2):
        name = f"S5 — Lobo {i + 1}"
        if name not in token_names:
            response = client.post("/gm/workspace/tokens", json={"token_type": "monster", "name": name, "map_id": table_map["id"],
                "latitude": 44 + i * 3, "longitude": 74 + i * 3, "visible_to_players": False,
                "maximum_hp": 12, "current_hp": 12, "sheet": {"armor_class": 14, "saving_throw": 5, "morale": 6, "movement": "12 m",
                "attacks": [{"name": "Mordida", "bonus": "+2", "damage": "1d6", "notes": "OD2 SRD; encontro opcional"}],
                "notes": "DV2+2; sem tesouro; XP referência175, não concedido. Foge/cede diante de risco; alimentação pode evitar combate."}})
            response.raise_for_status()
    return {"session": session["id"], "scenes": [x["id"] for x in scenes], "npcs": [x["id"] for x in npcs], "map": map_record["id"], "table_map": table_map["id"], "locations": [x["id"] for x in locations], "contracts": [x["id"] for x in contracts]}


def audit(client, player, ids):
    checked = []
    for kind, path in [("session", "/sessions/"), ("scenes", "/scenes/"), ("npcs", "/npcs/"), ("map", "/world/maps/"), ("locations", "/world/locations/"), ("contracts", "/contracts/")]:
        values = ids[kind] if isinstance(ids[kind], list) else [ids[kind]]
        for value in values:
            gm = client.get(path + str(value))
            assert gm.status_code == 200, (path, value, gm.status_code)
            public = player.get(path + str(value))
            assert public.status_code in (403, 404), ("Private prepared content exposed", path, value, public.status_code)
            assert SECRET not in public.text
            checked.append(path + str(value))
    return {"gm_read": len(checked), "player_denied": len(checked), "secret_not_exposed": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run = ROOT / ".autonomy/runtime" / ("session05-" + ("apply-" if args.apply else "rehearsal-") + stamp)
    run.mkdir(parents=True, exist_ok=False)
    backup = run / "before.sqlite3"
    with closing(sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True)) as source, closing(sqlite3.connect(backup)) as target:
        source.backup(target)
    # Preserve all campaign markdown as it currently exists, without runtime/secrets.
    shutil.copytree(VAULT / "CAMPANHA", run / "campaign-notes")
    credentials = json.loads((ROOT / "backend/data/access_tokens.json").read_text(encoding="utf-8-sig"))
    gm_headers = {"X-Omnisvera-Token": credentials["master_token"]}
    player_headers = {"X-Omnisvera-Token": credentials["player_profiles"]["raziel"]["token"]}
    target_db = DB if args.apply else run / "rehearsal.sqlite3"
    if not args.apply:
        shutil.copy2(backup, target_db)
    before = snapshot(target_db)
    if args.apply:
        import httpx
        client = httpx.Client(base_url="http://127.0.0.1:8788", headers=gm_headers, timeout=90, trust_env=False)
        player = httpx.Client(base_url="http://127.0.0.1:8788", headers=player_headers, timeout=90, trust_env=False)
    else:
        profiles = {k: v for k, v in credentials["player_profiles"].items() if not v.get("gm_controlled")}
        os.environ.update(OMNISVERA_DB_PATH=str(target_db), OMNISVERA_VAULT_PATH=str(VAULT),
            OMNISVERA_MASTER_TOKEN=credentials["master_token"], OMNISVERA_ACCESS_TOKEN=credentials["master_token"],
            OMNISVERA_PLAYER_PROFILES_JSON=json.dumps(profiles), OMNISVERA_REBUILD_ON_STARTUP="false", OMNISVERA_TRAINING_CAPTURE_MODE="off")
        sys.path.insert(0, str(ROOT / "backend"))
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app, headers=gm_headers)
        player = TestClient(app, headers=player_headers)
    try:
        ids = install(client, target_db)
        (run / "ids.json").write_text(json.dumps(ids, indent=2), encoding="utf-8")
        results = audit(client, player, ids)
        again = install(client, target_db)
        assert again == ids, "Repetition changed identity"
        after = snapshot(target_db)
        changed = [table for table, rows in before.items() if not rows.issubset(after.get(table, set()))]
        assert not changed, f"Existing domain rows changed: {changed}"
        report = {"mode": "apply" if args.apply else "rehearsal", "ids": ids, "privacy": results,
                  "idempotency": "PASS", "existing_domain_rows_preserved": True, "backup": str(backup),
                  "content_hashes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in DOCS.glob("*.md")}}
        media = client.get("/media/zz_media/maps/session05_route_schematic.svg")
        assert media.status_code == 200 and "<svg" in media.text
        report["map_asset_served"] = True
        if not args.apply:
            response = client.post(f"/gm/sessions/{ids['session']}/status", json={"status": "active"})
            response.raise_for_status()
            response = client.post(f"/gm/scenes/{ids['scenes'][0]}/open-on-table", json={"request_id": PREFIX + "-rehearsal-open"})
            response.raise_for_status()
            public = player.get(f"/scenes/{ids['scenes'][0]}")
            assert public.status_code == 200 and SECRET not in public.text and "private_notes" not in public.json()
            report["isolated_start_and_public_opening"] = "PASS"
        (run / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        client.close()
        player.close()


if __name__ == "__main__":
    main()
