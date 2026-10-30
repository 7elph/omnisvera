"""Optional declared NPC spell uses, on the existing monster usage/rest state."""
import json


def require_use(db,token_id,spell_id):
    row=db.execute('SELECT sheet_json,current_hp FROM session_workspace_tokens WHERE id=?',(token_id,)).fetchone()
    sheet=json.loads(row[0] or '{}') if row else {}
    repertoire=sheet.get('spell_repertoire')
    if repertoire is None:return None
    if not isinstance(repertoire,list):raise ValueError('Repertório do NPC inválido')
    entry=next((s for s in repertoire if isinstance(s,dict) and s.get('spell_id')==spell_id),None)
    if not entry:raise ValueError('Magia fora do repertório configurado deste NPC')
    limit=entry.get('daily_uses')
    if type(limit) is not int or not 1<=limit<=99:raise ValueError('Usos da magia do NPC inválidos')
    if row[1] is None or row[1]<=0:raise ValueError('NPC derrotado não pode conjurar')
    used=(sheet.get('monster_runtime') or {}).get('usage',{}).get('spell:'+spell_id,0)
    if type(used) is not int or used<0:raise ValueError('Contador de magias do NPC inválido')
    if used>=limit:raise ValueError('Usos da magia esgotados; aguarde o descanso geral do Mestre')
    return {'spell_id':spell_id,'limit':limit,'used_before':used,'used_after':used+1,'remaining':limit-used-1}


def consume(db,token_id,budget,now):
    if budget is None:return
    row=db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(token_id,)).fetchone()
    sheet=json.loads(row[0] or '{}')
    sheet.setdefault('monster_runtime',{}).setdefault('usage',{})['spell:'+budget['spell_id']]=budget['used_after']
    db.execute('UPDATE session_workspace_tokens SET sheet_json=?,updated_at=? WHERE id=?',(json.dumps(sheet,ensure_ascii=False),now,token_id))
