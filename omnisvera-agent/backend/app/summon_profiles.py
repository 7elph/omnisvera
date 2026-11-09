"""Fill only absent fields of Morthak's two known undead summon profiles.

Existing campaign HP/AC/attacks remain authoritative. Movement, DV and JP use
the existing skeleton/zombie catalog; explicit overrides are never replaced.
"""
from copy import deepcopy

PROFILES={'levantar-esqueleto':'esqueleto','levantar-um-esqueleto':'esqueleto','animar-mortos':'zumbi'}


def complete_sheet(sheet):
    result=deepcopy(sheet)
    summon=result.get('summon') or {}
    identity=PROFILES.get(summon.get('technique')) if summon.get('caster')=='morthak' else None
    if not identity:return result
    from .monster_catalog import get_catalog_monster
    monster=get_catalog_monster(identity)
    if not monster:return result
    fields={}
    if result.get('movement') in (None,''):fields['movement']=monster.get('movement')
    if result.get('hit_dice') in (None,'') and result.get('dv') in (None,''):
        fields['hit_dice']=int(monster['hit_dice'])
    if result.get('saving_throw') in (None,''):fields['saving_throw']=monster.get('saving_throw')
    fields={key:value for key,value in fields.items() if value is not None}
    if fields:
        result.update(fields)
        result['summon']={**summon,'profile_source':monster.get('source_url'),
                          'profile_defaults':sorted(set(summon.get('profile_defaults') or [])|set(fields))}
    return result


def backfill_active(path):
    """Explicit activation maintenance, never a read/startup migration."""
    import json,sqlite3
    from contextlib import closing
    from .session_workspace import _now
    from .session_ledger import append_session_ledger_event
    changed=[];now=_now()
    with closing(sqlite3.connect(path,timeout=30)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        for identity,raw in db.execute("SELECT id,sheet_json FROM session_workspace_tokens WHERE current_hp>0 AND json_extract(sheet_json,'$.summon.caster')='morthak'").fetchall():
            before=json.loads(raw or '{}')
            if before.get('combat_retired') or (before.get('summon') or {}).get('dismissed'):continue
            after=complete_sheet(before)
            if after==before:continue
            db.execute('UPDATE session_workspace_tokens SET sheet_json=?,updated_at=? WHERE id=?',(json.dumps(after,ensure_ascii=False),now,identity))
            changed.append({'token_id':identity,'filled_fields':[key for key in ('movement','hit_dice','saving_throw') if before.get(key)!=after.get(key)]})
        if changed:
            db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
            append_session_ledger_event(db,source_type='summon_profile_repair',source_id='morthak-undead-v1:'+','.join(c['token_id'] for c in changed),
                event_kind='state',actor_id='master',actor_name='Mestre',actor_role='gm',character_id='morthak',
                title='Movimento e ficha básica das invocações completados',detail={'changes':changed},visibility='gm',created_at=now)
    return changed
