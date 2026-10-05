"""Explicit, idempotent conversion of the approved Dorn token to a PC sheet."""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from .character_creation import init_character_creation, seed_from_note
from .character_play import init_character_play
from .session_context import table_exists


def promote_dorn(database_path, *, token_id, note):
    init_character_creation(database_path)
    init_character_play(database_path)
    now = datetime.now(timezone.utc).isoformat()
    with closing(sqlite3.connect(database_path)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM character_sheets WHERE profile_id='dorn7'").fetchone():
            return {"id": "dorn7", "created": False}
        if table_exists(db, "combat_effect_clock"):
            clock = db.execute("SELECT encounter_json FROM combat_effect_clock LIMIT 1").fetchone()
            encounter = json.loads(clock[0] or "{}") if clock else {}
            if encounter.get("active") and any(p.get('target_id') in {token_id, 'dorn7'} for p in encounter.get('participants', [])):
                raise ValueError("Encerre o combate de Dorn antes de converter a ficha.")
        if table_exists(db, "combat_effects") and db.execute("SELECT 1 FROM combat_effects WHERE target_type='token' AND target_id=? AND active=1", (token_id,)).fetchone():
            raise ValueError("Resolva os efeitos ativos do pin antes de converter a ficha.")
        if table_exists(db, "combat_attack_resolutions") and db.execute("SELECT 1 FROM combat_attack_resolutions WHERE status='pending' AND expires_at>? AND (actor_character_id=? OR (target_type='token' AND target_id=?))", (now, token_id, token_id)).fetchone():
            raise ValueError("Resolva o ataque pendente de Dorn antes de converter a ficha.")
        token = db.execute("SELECT * FROM session_workspace_tokens WHERE id=?", (token_id,)).fetchone()
        if not token or ''.join(c for c in token['name'].lower() if c.isalnum()) not in {'dorn7', 'unidadedorn7'}:
            raise ValueError("Pin de Dorn 7 não encontrado.")
        sheet = json.loads(token['sheet_json'] or '{}')
        attacks = sheet.get('attacks') or []
        if not attacks:
            raise ValueError("Revise os ataques aprovados de Dorn antes de converter.")
        data = seed_from_note(note)
        data['character_class'].update(class_name='Constructo — adaptação de campanha', hit_points=token['maximum_hp'], saving_throw=sheet.get('saving_throw'))
        data['race'].update(race='Golem metálico', movement=sheet.get('movement'), racial_abilities='\n'.join(sheet.get('abilities') or []))
        data['armor']['armor_class'] = sheet.get('armor_class')
        data['attacks'] = {'attack_notes': sheet.get('notes', '')}
        overrides = {
            'level_pending': not bool((note.get('frontmatter') or {}).get('level')),
            'maximum_hp': token['maximum_hp'], 'armor_class': sheet.get('armor_class'),
            'initiative': sheet.get('initiative'), 'movement': sheet.get('movement'),
            'natural_attacks': [dict(id=f'natural:{i}', name=a['name'], damage=a['damage'], attack_bonus=int(a['bonus']),
                                     weapon_item_path=f'natural:dorn7:{i}', notes=a.get('notes')) for i, a in enumerate(attacks)],
            'approved_session_abilities': [dict(id=f'construct:{i}', name=a.split(':')[0], description=a,
                kind='ability', group='Habilidades', mechanics_status='partial', source='Ficha aprovada pelo Mestre',
                active=True, blocked=False) for i, a in enumerate(sheet.get('abilities') or [])],
        }
        state = dict(current_hp=token['current_hp'], maximum_hp=token['maximum_hp'], temporary_hp=0,
                     conditions=json.loads(token['conditions_json'] or '[]'), resources=[], coins=None,
                     location=None, session_notes=sheet.get('description', ''))
        db.execute("CREATE TABLE IF NOT EXISTS companion_conversion_backups (profile_id TEXT PRIMARY KEY, token_json TEXT NOT NULL, created_at TEXT NOT NULL)")
        db.execute("INSERT INTO companion_conversion_backups VALUES('dorn7',?,?)", (json.dumps(dict(token)), now))
        db.execute("INSERT INTO character_sheets(profile_id,character_path,character_title,data_json,status,updated_at) VALUES('dorn7',?,'Dorn 7',?,'draft',?)", (note['path'], json.dumps(data), now))
        db.execute("INSERT INTO character_definition_overrides VALUES('dorn7',?,?)", (json.dumps(overrides), now))
        db.execute("INSERT INTO character_states(profile_id,state_json,updated_at) VALUES('dorn7',?,?)", (json.dumps(state), now))
        db.execute("UPDATE session_workspace_tokens SET token_type='character',character_id='dorn7',current_hp=NULL,maximum_hp=NULL,conditions_json='[]',updated_at=? WHERE id=?", (now, token_id))
        return {"id": "dorn7", "created": True}
