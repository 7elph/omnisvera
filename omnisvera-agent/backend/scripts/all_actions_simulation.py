"""All-current-actions rehearsal: native HTTP, fixture tokens, TEMP database only.

Prepare/serve with cf01_probe.py first. Outputs private evidence beside the
temporary database, never operational state. Independent scenarios restore
resources/HP in the disposable fixture; they are not extra uses in one battle.
"""
from __future__ import annotations
if __name__ == '__main__':
    from memory_guard import join_owned_job_from_env
    join_owned_job_from_env()

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
import json
import hashlib
from pathlib import Path
import sqlite3
import uuid
import traceback
import time
import httpx
try:
    from .cf01_probe import checked_database, TOKENS
    from .sheet_rehearsal import build_report, render_report
    from .run_sheet_test import save_progress
except ImportError:  # direct CLI invocation
    from cf01_probe import checked_database, TOKENS
    from sheet_rehearsal import build_report, render_report
    from run_sheet_test import save_progress

ACTORS = ('vezemir', 'morthak', 'raziel', 'dorn7')


class Simulation:
    def __init__(self, database, port, actors=ACTORS, scenarios=None):
        if not actors or any(actor not in ACTORS for actor in actors):
            raise ValueError('Select existing scenario actors: ' + ', '.join(ACTORS))
        self.actors = tuple(dict.fromkeys(actors))
        self.port = port
        self.scenarios = set(scenarios or ())
        self.available_scenarios = set()
        self.database = checked_database(database)
        if not self.database.is_file(): raise ValueError('Prepare an existing disposable database first')
        self.prefix = 'simulation-' + uuid.uuid4().hex[:12]
        self.clients = {role: httpx.Client(base_url=f'http://127.0.0.1:{port}', headers={'X-Omnisvera-Token': token}, timeout=30, trust_env=False) for role, token in TOKENS.items()}
        assert self.get('/health')['access_mode'] == 'gm'
        # Prove HTTP and SQL point at the SAME disposable copy before resetting it.
        marker = self.post('/workspace/messages', {'text': self.prefix})
        with closing(sqlite3.connect(self.database)) as db:
            assert db.execute('SELECT count(*) FROM session_workspace_messages WHERE text=?', (self.prefix,)).fetchone()[0] == 1
        self.results, self.trace = [], []
        self.sheets = {actor: self.get('/characters/' + actor) for actor in ACTORS}
        self.baseline_states = {actor: deepcopy(sheet['state']) for actor, sheet in self.sheets.items()}
        self.baseline_inventory = {actor: deepcopy(sheet['inventory']) for actor, sheet in self.sheets.items()}
        maps = self.get('/workspace/maps')
        self.map_id = next((m['id'] for m in maps if 'arena' in m['title'].lower()), None) or self.get('/workspace')['map']['id']
        self.request('PATCH', '/gm/workspace/maps/active', {'map_id': self.map_id})
        catalog = self.get('/gm/workspace/monster-catalog?q=hobgoblin')
        self.monster = next(m for m in catalog['monsters'] if m['id'] == 'hobgoblin')
        self.catalog = catalog['catalog']
        self.enemy = self.create_monster('Hobgoblin do ensaio ' + self.prefix, self.monster['average_hp'])
        self.corpse = self.create_monster('Hobgoblin caído do ensaio ' + self.prefix, 0)
        for index, actor in enumerate(ACTORS):
            self.post('/gm/workspace/tokens', {'token_type':'character','character_id':actor,'map_id':self.map_id,'name':self.sheets[actor]['definition']['name'],'latitude':20+index*10,'longitude':30,'visible_to_players':True})

    def create_monster(self, name, hp):
        m = self.monster
        # SRD has no attribute scores: explicit TEST declarations, not canon.
        sheet = {k:m[k] for k in ('armor_class','saving_throw','hit_dice','movement','morale','treasure')}
        sheet.update(catalog_id=m['id'], attacks=m['attacks'], abilities=[a['name']+': '+a['description'] for a in m['abilities']], has_blood=True,
                     attributes={'strength':10,'constitution':10,'dexterity':10,'wisdom':10}, reanimation_allowed=hp == 0,
                     notes='Ensaio isolado: atributos 10 declarados só para exercitar JP/FOR; não são estatísticas publicadas da SRD.')
        return self.post('/gm/workspace/tokens', {'token_type':'monster','map_id':self.map_id,'name':name,'image_path':m['image_path'],'latitude':55,'longitude':55,
                                                'visible_to_players':True,'current_hp':hp,'maximum_hp':m['average_hp'],'sheet':sheet})

    def get(self, route, role='gm'):
        response = self.clients[role].get(route); response.raise_for_status(); return response.json()

    def request(self, method, route, payload, role='gm', accepted=(200,)):
        response = self.clients[role].request(method, route, json=payload)
        if hasattr(self, 'trace'):
            self.trace.append({'method':method,'route':route,'role':role,'request_id':payload.get('request_id'), 'status':response.status_code})
        if response.status_code not in accepted: raise AssertionError(f'{route}: {response.status_code}: {response.text[:700]}')
        return response.json() if response.content else None

    def post(self, route, payload, role='gm', accepted=(200,)):
        return self.request('POST', route, payload, role, accepted)

    def role(self, actor): return 'gm' if actor == 'dorn7' else actor

    def command(self, action, payload=None, replay=False):
        body = {'request_id':self.prefix+'-'+uuid.uuid4().hex,'expected_version':self.get('/combat/effects')['version'],'action':action,'payload':payload or {}}
        route = '/combat/next-turn' if action == 'next_turn' else '/gm/combat/effects'
        return self.repeated(route, body) if replay else self.post(route, body)

    def snapshot(self):
        chars = {}
        for actor in ACTORS:
            sheet = self.get('/characters/'+actor)
            chars[actor] = {'hp':sheet['state']['current_hp'],'max_hp':sheet['state']['maximum_hp'],
                'animal':sheet['state'].get('animal_form'),'resources':{r['key']:r['current'] for r in sheet['state']['resources']},
                'attributes':sheet['definition']['attributes'],'ac':sheet['definition']['defenses']['armor_class'],
                'attacks':[{k:a.get(k) for k in ('id','attack_bonus','damage','attack_count')} for a in sheet['definition']['attacks']],
                'items':[{k:i.get(k) for k in ('item_path','quantity','charges_current','equipped')} for i in sheet['inventory']]}
        battle = self.get('/combat/effects')
        tokens = self.get('/workspace')['tokens']
        return {'characters':chars,'effects':battle['effects'],'encounter':battle.get('encounter'),
                'tokens':[{k:t.get(k) for k in ('id','current_hp','maximum_hp','conditions','grid_position','sheet')} for t in tokens if t['id'] in (self.enemy['id'],self.corpse['id']) or t.get('sheet',{}).get('summon')]}

    def repeated(self, route, body, role='gm'):
        # Same request sent concurrently, then again after reconnect/retry.
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: self.post(route, body, role), range(2)))
        assert responses[0] == responses[1], 'Concurrent retries returned different results'
        state = self.persisted_fingerprint()
        replay = self.post(route, body, role)
        assert replay == responses[0], 'Retry did not recover original result'
        assert self.persisted_fingerprint() == state, 'Retry changed durable state or duplicated ledger rows'
        if hasattr(self, 'checks'):
            self.checks.add('retry concorrente e repetido: uma mutação e nenhum ledger duplicado')
            self.verify('idempotency')
        return responses[0]

    def verify(self, *checks):
        self.verified_checks = getattr(self, 'verified_checks', set()) | set(checks)

    def persisted_fingerprint(self):
        """Retry checks inspect durable state directly, not dozens of sheet polls.

        The case still performs native HTTP reads and GM/owner parity checks.
        Only existing transactionally updated tables are included; hashes never
        publish the private rows from the disposable campaign copy.
        """
        tables=('character_states','player_inventory','character_events','combat_effect_clock',
                'combat_effects','combat_attack_resolutions','session_workspace_tokens',
                'session_workspace_entity_positions','session_ledger')
        with closing(sqlite3.connect(self.database)) as db:
            db.execute('BEGIN')
            existing={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            rows=[(table, sorted(db.execute('SELECT * FROM "'+table+'"').fetchall(),key=repr)) for table in tables if table in existing]
        return hashlib.sha256(repr(rows).encode('utf-8')).hexdigest()

    def reset(self, actor, combat=True, physical=False):
        if self.get('/combat/effects').get('encounter',{}).get('active'): self.command('end')
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('UPDATE combat_effects SET active=0')
            for profile, base in self.baseline_states.items():
                state = deepcopy(base); state.pop('animal_form',None); state['current_hp']=max(1,state['maximum_hp']-5)
                for resource in state['resources']: resource['current']=resource['maximum']
                db.execute('UPDATE character_states SET state_json=?,version=version+1 WHERE profile_id=?',(json.dumps(state),profile))
                for item in self.baseline_inventory[profile]:
                    db.execute('UPDATE player_inventory SET quantity=?,equipped=?,charges_current=? WHERE profile_id=? AND item_path=?',
                               (item['quantity'],int(item['equipped']),item.get('charges_max') or item.get('charges_current'),profile,item['item_path']))
            db.execute("UPDATE session_workspace_tokens SET current_hp=0 WHERE json_extract(sheet_json,'$.summon.caster')='morthak'")
            for token in (self.enemy,self.corpse):
                db.execute('UPDATE session_workspace_tokens SET current_hp=?,sheet_json=? WHERE id=?',(token['current_hp'],json.dumps(token['sheet']),token['id']))
        self.request('PATCH','/gm/workspace/table-mode',{'table_mode':'physical' if physical else 'digital'})
        self.request('PATCH','/gm/workspace/maps/active',{'map_id':self.map_id})
        workspace=self.get('/workspace');grid=workspace['map'].get('grid')
        if grid:
            enemy=next(t for t in workspace['tokens'] if t['id']==self.enemy['id'])['grid_position']
            offsets=[(-1,0),(0,-1),(1,0),(0,1)]
            for profile,(dx,dy) in zip(ACTORS,offsets):
                token=next(t for t in workspace['tokens'] if t.get('character_id')==profile);pos=token['grid_position']
                destination=[min(grid['cols']-1,max(0,enemy['cell_x']+dx)),min(grid['rows']-1,max(0,enemy['cell_y']+dy))]
                self.post('/workspace/maps/'+self.map_id+'/move',{'request_id':self.prefix+'-'+uuid.uuid4().hex,'token_id':token['id'],'mode':'GM_REPOSITION',
                    'path':[[pos['cell_x'],pos['cell_y']],destination],'expected_position_version':pos['version'],'expected_grid_version':grid['version']})
        if combat:
            order = [actor]+[p for p in ACTORS if p != actor]
            self.command('start', {'title':'Simulação isolada de todas as ações','map_id':self.map_id,'battle_mode':True,
                'participants':[{'target_type':'character','target_id':p,'initiative':30-i,'name':self.sheets[p]['definition']['name']} for i,p in enumerate(order)]+
                              [{'target_type':'token','target_id':self.enemy['id'],'initiative':1,'name':self.enemy['name']}]})

    def case(self, label, actor, execute, *, combat=True, physical=False, blocked=False, covers=(), scenario_id=None):
        if actor not in self.actors:
            return
        scenario_id=scenario_id or actor+':'+label
        self.available_scenarios.add(scenario_id)
        if self.scenarios and scenario_id not in self.scenarios:
            return
        print('RUN',actor,label,flush=True)
        started = time.monotonic()
        if hasattr(self, 'database'):
            save_progress(self.database.parent, phase='api', current=scenario_id,
                          completed=len(self.results), total=None)
        record={'actor':actor,'action':label,'scenario_id':scenario_id,'combat':combat,'physical':physical,'covers':list(covers)}
        self.checks = set()
        self.verified_checks = set()
        trace_start = len(self.trace)
        try:
            self.reset(actor,combat,physical)
            before=self.snapshot(); last=max((e['id'] for e in self.get('/workspace/ledger?limit=1000')),default=0)
            self.checks.clear(); self.verified_checks.clear()
            original = self.persisted_fingerprint()
            execution_trace = len(self.trace)
            result=execute()
            after = self.snapshot()
            self.check_persisted(actor, after)
            if self.persisted_fingerprint() != original and any(
                c['method'] in {'POST', 'PATCH', 'DELETE'} and 200 <= c['status'] < 300
                for c in self.trace[execution_trace:]):
                self.verify('execution', 'persistence')
            record.update(status='EXPECTED_BLOCK' if blocked else 'PASS', result=result, before=before, after=after,
                          ledger=[{k:e.get(k) for k in ('id','character_id','event_kind','title','visibility','action_cards')} for e in self.get('/workspace/ledger?limit=1000') if e['id']>last])
            if blocked and isinstance(result,dict):record['availability_reason']=str(result.get('detail') or 'Pré-requisito indisponível')[:300]
        except Exception as error:
            record.update(status='FAIL',error=str(error) or type(error).__name__,error_type=type(error).__name__,traceback=traceback.format_exc())
        record.update(checks=sorted(self.checks), verified_checks=sorted(self.verified_checks), commands=self.trace[trace_start:],
                      duration_seconds=round(time.monotonic()-started, 3))
        self.results.append(record);print(record['status'],label,record.get('error',''),flush=True)
        if hasattr(self, 'database'):
            save_progress(self.database.parent, phase='api', current=scenario_id,
                          completed=len(self.results), total=None, elapsed_seconds=record['duration_seconds'])

    def check_persisted(self, actor, snapshot):
        """New HTTP client and SQLite read: no reliance on cached command response."""
        with httpx.Client(base_url=f'http://127.0.0.1:{self.port}', headers={'X-Omnisvera-Token': TOKENS[self.role(actor)]},
                          timeout=30, trust_env=False) as fresh:
            response = fresh.get('/characters/'+actor); response.raise_for_status(); owner = response.json()
        gm = self.get('/characters/'+actor)
        for key in ('level', 'attributes', 'attacks', 'defenses', 'session_abilities'):
            assert owner['definition'][key] == gm['definition'][key], 'GM/owner mismatch: ' + key
        assert owner['state'] == gm['state'] and owner['inventory'] == gm['inventory'], 'GM/owner state mismatch'
        with closing(sqlite3.connect(self.database)) as db:
            state = json.loads(db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (actor,)).fetchone()[0])
            assert state['current_hp'] == snapshot['characters'][actor]['hp'], 'PV not persisted'
            raw_resources = {r['key']: r['current'] for r in state['resources']}
            for key, value in snapshot['characters'][actor]['resources'].items():
                assert raw_resources.get(key) == value, 'Resource not persisted: ' + key
        self.checks.update(('PV e recursos persistidos no SQLite', 'nova leitura HTTP e paridade Mestre/proprietário'))

    def resource_keys(self, actor, ability):
        card = next((a for a in self.sheets[actor]['definition']['session_abilities'] if a['id']==ability), {})
        key = (card.get('uses') or {}).get('resource_key')
        state_keys={r['key'] for r in self.sheets[actor]['state']['resources']}
        if key and key not in state_keys and key.replace('-','_') in state_keys:
            key=key.replace('-','_')
        return ('resource:'+key,) if key else ()

    def item_keys(self, actor, title):
        return tuple('item:'+i['item_path'] for i in self.sheets[actor]['inventory'] if i['item_title']==title)

    def attack(self, actor, attack_id='melee', technique=None, **extra):
        before = self.snapshot()['characters'][actor]
        target_hp = next(t for t in self.get('/workspace')['tokens'] if t['id']==self.enemy['id'])['current_hp']
        body={'request_id':self.prefix+'-'+uuid.uuid4().hex,'target_type':'token','target_id':self.enemy['id'], 'roll_mode':'physical','d20':15,**extra}
        route=f'/characters/{actor}/techniques/{technique}' if technique else f'/characters/{actor}/attacks/resolve'
        if not technique: body['attack_id']=attack_id
        preview=self.repeated(route,body,self.role(actor))
        assert not preview.get('confirmed'), 'Preview changed HP before confirmation'
        assert self.snapshot()['characters'][actor]['resources'] == before['resources'], 'Preview consumed a resource'
        assert next(t for t in self.get('/workspace')['tokens'] if t['id']==self.enemy['id'])['current_hp'] == target_hp, 'Preview damaged target'
        self.checks.add('prévia não aplica dano nem custo')
        result=self.repeated('/combat/attacks/'+preview['resolution_id']+'/confirm',{},self.role(actor))
        assert result['hp_after'] == max(0, result['hp_before']-result['damage_total']), 'Damage inconsistent with HP'
        if body['d20'] == 1 or result.get('result') == 'miss':
            assert result['damage_total'] == 0 and result['hp_before'] == result['hp_after'], 'Miss damaged target'
        cost = result['breakdown'].get('resource_cost')
        after = self.snapshot()['characters'][actor]
        if cost:
            assert after['resources'][cost['key']] == before['resources'][cost['key']]-cost['amount'], 'Wrong attack cost'
            self.checks.add('custo do contrato descontado uma vez na confirmação')
            self.verify('cost')
        # Independent campaign approvals, not just agreement with the server's
        # returned damage/cost. These are TEST expectations, never runtime rules.
        approved = {'arma-de-sangue':('1d8',1), 'garras-predatorias':('1d6',1),
                    'investida-predatoria':('2d4',1), 'toque-sombrio':('1d4',1)}
        if technique in approved:
            formula, amount = approved[technique]
            assert result['damage_formula'].lower() == formula, 'Approved damage formula regressed'
            assert cost and cost['amount']==amount, 'Approved resource cost regressed'
            self.checks.add('dano e custo conferidos contra valores aprovados, não somente contra a resposta')
        if technique == 'lamina-de-sangue':
            amount = body['charges']
            assert result['damage_formula'].lower()==f'{amount}d4' and cost['amount']==amount, 'Blade count mismatch'
        if technique == 'mordida':
            level = int((self.sheets[actor]['definition'] or {}).get('level') or 1)
            expected_bite = '2d10' if level >= 16 else '2d6' if level >= 8 else '1d6' if level >= 5 else '1d4'
            assert result['damage_formula'].lower()==expected_bite and not cost, 'Bite formula/cost mismatch'
        drain = result['breakdown'].get('drain_result')
        if drain:
            expected_hp=min(before['max_hp'],before['hp']+drain['drained'])
            fumble=result['breakdown'].get('fumble_result')
            if fumble:
                assert fumble['hp_before']==expected_hp,'Self damage must follow the drain resolution'
                expected_hp=fumble['hp_after']
            assert after['hp'] == expected_hp, 'Life drain mismatch'
            self.checks.add('drenagem cura somente PV efetivamente retirados, limitada ao máximo')
        self.checks.add('dano confirmado corresponde à mudança de PV')
        return {k:result.get(k) for k in ('resolution_id','attack_id','d20','attack_bonus','damage_formula','damage_total','hp_before','hp_after','result','breakdown')}

    def technique(self, actor, technique, **payload):
        blood_before=self.snapshot()['characters'][actor]['resources'].get('reserva_de_sangue') if actor=='raziel' and technique in {'marca-rubra','regeneracao-vampirica'} else None
        body={'request_id':self.prefix+'-'+uuid.uuid4().hex,**payload}
        result=self.repeated(f'/characters/{actor}/techniques/{technique}',body,self.role(actor))
        if blood_before is not None:
            assert self.snapshot()['characters'][actor]['resources']['reserva_de_sangue']==blood_before-1,'Wrong blood cost'
            self.verify('cost')
        return result

    def hemomancy_use(self, weapon, skill=False):
        """Exercise the same native card command/receipt, not a test rules engine."""
        from urllib.parse import urlencode
        # Independent approved expectations; production still owns all calculations.
        approved={'arco':('1d8',1,1),'foice':('1d8',1,1),
                  'marreta':('1d10',1,1),'lanca':('1d8',1,1),'escudo':(None,1,0)}
        formula,invocation,extra=approved[weapon]
        identity='hemomancia-'+weapon+('-habilidade' if skill else '')
        before=self.snapshot()['characters']['raziel']['resources']['reserva_de_sangue']
        if weapon=='escudo':
            ca=self.get('/characters/raziel')['definition']['defenses']['armor_class']
            result=self.technique('raziel',identity)
            assert self.get('/characters/raziel')['definition']['defenses']['armor_class']==ca+2
            self.command('round')
            assert self.get('/characters/raziel')['definition']['defenses']['armor_class']==ca
        else:
            ring=self.get('/gm/grid/range?'+urlencode({'ref':'technique:raziel:'+identity,
                'map_id':self.map_id,'attacker_character_id':'raziel'}))
            assert ring.get('gridded') and any(t['id']==self.enemy['id'] and t['valid'] for t in ring['targets']),'Native range did not include adjacent target'
            self.verify('range')
            result=self.attack('raziel',technique=identity)
            assert result['breakdown']['hemomancy']['base_damage']==formula
            if weapon=='lanca' and skill:
                assert result['breakdown']['hemomancy']['skill_damage']=='1d4'
            self.command('end')
        after=self.snapshot()['characters']['raziel']['resources']['reserva_de_sangue']
        assert after==before-max(invocation,extra if skill else 0),'Wrong invocation/skill cost'
        assert not any(e.get('hemomancy_kind') for e in self.get('/combat/effects')['effects']),'Temporary hemomancy did not expire'
        self.verify('cost','expiration')
        return result

    def potion_case(self, actor):
        title='Poção de HP'
        label=title+' + ataque no mesmo turno'
        if any(i['item_title']==title and i.get('quantity',0)>0 for i in self.sheets[actor]['inventory']):
            self.case(label,actor,lambda:(self.item(actor,title),self.attack(actor,'ranged' if actor=='raziel' else 'melee')),
                physical=True,covers=self.item_keys(actor,title))
        else:
            self.case(title+' sem estoque: rejeição sem mutação',actor,
                lambda:self.missing_consumable(actor,title),physical=True,blocked=True,
                scenario_id=actor+':'+label)

    def missing_consumable(self, actor, title):
        # Read the existing exhausted stack; never fabricate/replenish an item
        # merely to make a copied real sheet pass its rehearsal.
        with closing(sqlite3.connect(self.database)) as db:
            row=db.execute('SELECT item_path FROM player_inventory WHERE profile_id=? AND item_title=? AND quantity<=0',
                (actor,title)).fetchone()
        assert row, 'Consumível ausente, sem registro esgotado para provar rejeição: '+title
        before=self.persisted_fingerprint()
        body={'request_id':self.prefix+'-'+uuid.uuid4().hex,'action':'use_item','payload':{'item_path':row[0]}}
        result=self.post('/characters/'+actor+'/actions',body,self.role(actor),accepted=(400,))
        self.post('/characters/'+actor+'/actions',body,self.role(actor),accepted=(400,))
        assert self.persisted_fingerprint()==before, 'Rejected empty consumable changed durable state'
        self.checks.add('estoque zero: rejeição nativa e retry sem repor, curar ou consumir ação')
        return {'detail':'Sem estoque na ficha copiada: '+title,'native_rejection':result}

    def item(self, actor, title):
        item=next(i for i in self.get('/characters/'+actor)['inventory'] if i['item_title']==title)
        hp = self.get('/characters/'+actor)['state']['current_hp']
        body={'request_id':self.prefix+'-'+uuid.uuid4().hex,'action':'use_item','payload':{'item_path':item['item_path']},'reason':'Ensaio: usar '+title}
        self.repeated('/characters/'+actor+'/actions',body,self.role(actor))
        after = self.get('/characters/'+actor)
        # Native inventory hides empty stacks. Consuming the last potion is
        # success, not a StopIteration failure in the rehearsal itself.
        saved = next((i for i in after['inventory'] if i['item_path']==item['item_path']), {'quantity':0})
        assert saved['quantity']<item['quantity'] or (saved.get('charges_current') is not None and
            saved['charges_current']<(item.get('charges_current') or 0)), 'Consumable did not spend quantity/charge'
        self.checks.add('item desconta quantidade ou carga sem duplicação')
        self.verify('cost')
        if title=='Poção de HP':
            assert hp <= after['state']['current_hp'] <= after['state']['maximum_hp'], 'Potion HP outside allowed bounds'
            self.checks.add('cura do consumível limitada aos PV máximos')
        return {'item':title}

    def ring(self):
        before=self.get('/characters/raziel')['state']
        self.item('raziel','Anel Runico')
        after=self.get('/characters/raziel')['state']
        assert after['current_hp']==min(before['maximum_hp'],before['current_hp']+4), 'Runic ring healing changed'
        ring=next(i for i in self.get('/characters/raziel')['inventory'] if i['item_title']=='Anel Runico')
        assert ring['charges_current']==0 and ring['quantity']==1, 'Ring was not retained with exhausted charge'
        body={'request_id':self.prefix+'-'+uuid.uuid4().hex,'action':'use_item','payload':{'item_path':ring['item_path']}}
        state=self.snapshot()
        rejected=self.post('/characters/raziel/actions',body,'raziel',accepted=(400,))
        assert 'cargas' in str(rejected).lower(), 'Second ring use was not rejected for exhausted charge'
        assert self.snapshot()==state, 'Rejected second use changed state'
        self.post('/characters/raziel/actions',{'request_id':self.prefix+'-'+uuid.uuid4().hex,
            'action':'change_charges','payload':{'item_path':ring['item_path'],'charges':1}},'raziel',accepted=(403,))
        assert self.snapshot()==state, 'Owner manual charge adjustment bypassed daily limit'
        self.repeated('/characters/raziel/actions',{'request_id':self.prefix+'-'+uuid.uuid4().hex,
            'action':'rest_in_coffin','payload':{}},'raziel')
        assert next(i for i in self.get('/characters/raziel')['inventory'] if i['item_path']==ring['item_path'])['charges_current']==0, 'Coffin recharged daily item'
        self.repeated('/characters/raziel/actions',{'request_id':self.prefix+'-'+uuid.uuid4().hex,
            'action':'rest_at_inn','payload':{}},'gm')
        assert next(i for i in self.get('/characters/raziel')['inventory'] if i['item_path']==ring['item_path'])['charges_current']==1
        self.item('raziel','Anel Runico')
        self.checks.add('Anel: cura 4, carga 1→0, segundo uso/recarga manual bloqueados, Caixão não recarrega, descanso do Mestre recarrega')
        return {'daily_charge_enforced':True,'master_rest_recharge':True,'coffin_does_not_recharge':True}

    def rejected_attack(self, actor, attack):
        result=self.post('/characters/'+actor+'/attacks/resolve',{'request_id':self.prefix+'-'+uuid.uuid4().hex,'attack_id':attack,'target_type':'token','target_id':self.enemy['id'],'roll_mode':'physical','d20':15},self.role(actor),accepted=(400,409))
        return result

    def summoned(self, technique):
        payload={'target_type':'token','target_id':self.corpse['id']} if technique=='animar-mortos' else {}
        summon=self.technique('morthak',technique,**payload); token=summon['token']
        denied=self.post('/characters/morthak/techniques/'+technique,{'request_id':self.prefix+'-'+uuid.uuid4().hex,**payload},'morthak',accepted=(400,409))
        self.command('next_turn')
        attack=self.repeated('/gm/combat/tokens/'+token['id']+'/attacks/resolve',{'request_id':self.prefix+'-'+uuid.uuid4().hex,'attack_id':'0','target_type':'token','target_id':self.enemy['id'],'roll_mode':'physical','d20':15},'morthak')
        self.repeated('/combat/attacks/'+attack['resolution_id']+'/confirm',{},'morthak')
        return {'summon':token,'duplicate_block':denied,'attack':attack}

    def night(self, animal='corvo'):
        count=self.get('/characters/raziel')['state']['resources']
        count=next(r['current'] for r in count if r['key']=='forma_da_noite')
        body={'request_id':self.prefix+'-'+uuid.uuid4().hex,'action':'consume_resource','payload':{'resource_key':'forma_da_noite','amount':1,'animal':animal},'reason':'Forma da Noite: '+animal}
        self.repeated('/characters/raziel/actions',body,'raziel')
        before=self.get('/characters/raziel','raziel')
        assert before['state']['current_hp']==1 and before['definition']['defenses']['armor_class']==14
        assert not before['definition']['attacks'], 'Animal retained normal attacks'
        assert next(r['current'] for r in before['state']['resources'] if r['key']=='forma_da_noite')==count-1
        returned=self.repeated('/characters/raziel/actions',{'request_id':self.prefix+'-'+uuid.uuid4().hex,'action':'end_night_form','payload':{},'reason':'Desativar Forma da Noite'},'raziel')
        assert before['state'].get('animal_form')==animal and not returned['state'].get('animal_form')
        self.verify('cost', 'expiration')
        return {'entered':animal,'returned':True,'animal_hp':1,'animal_ac':14,'normal_attacks_removed':True}

    def expiry(self, technique):
        resource=self.resource_keys('vezemir',technique)[0].split(':',1)[1]
        before=self.snapshot()['characters']['vezemir']['resources'][resource]
        activated=self.technique('vezemir',technique)
        assert self.snapshot()['characters']['vezemir']['resources'][resource]==before-1
        self.verify('cost')
        duration=activated['duration_rounds'];assert duration>=6
        for _ in range(duration): self.command('round')
        assert not any(e.get('source') in {'Força Arcana (Vezemir)','Velocidade (Vezemir)'} for e in self.get('/combat/effects')['effects'])
        self.checks.add('efeito removido ao expirar a duração retornada pelo backend')
        self.verify('expiration')
        return {'duration_rounds':duration,'expired':True}

    def vines(self):
        before=next(i for i in self.get('/characters/vezemir')['inventory'] if i['item_title']=='Pulseira de Vinhas')['charges_current']
        self.repeated('/characters/vezemir/vines',{'request_id':self.prefix+'-'+uuid.uuid4().hex,'target_type':'token','target_id':self.enemy['id']},'vezemir')
        assert next(i for i in self.get('/characters/vezemir')['inventory'] if i['item_title']=='Pulseira de Vinhas')['charges_current']==before-1
        for _ in range(20):
            if not any(e.get('reward')=='vines' for e in self.get('/combat/effects')['effects']):break
            self.command('next_turn',replay=True)
        assert not any(e.get('reward')=='vines' for e in self.get('/combat/effects')['effects'])
        self.verify('expiration', 'cost')
        return {'ended':True,'saving_throw':self.monster['saving_throw'],'maximum_target_turns':3}

    def move(self, actor):
        workspace=self.get('/workspace');grid=workspace['map'].get('grid')
        assert grid, 'No logical grid on chosen map'
        token=next(t for t in workspace['tokens'] if t.get('character_id')==actor);pos=token['grid_position'];x,y=pos['cell_x'],pos['cell_y']
        destination=[x+1 if x+1<grid['cols'] else x-1,y]
        body={'request_id':self.prefix+'-'+uuid.uuid4().hex,'token_id':token['id'],'mode':'COMBAT_MOVE','path':[[x,y],destination],
              'expected_position_version':pos['version'],'expected_grid_version':grid['version'],'expected_combat_version':self.get('/combat/effects')['version']}
        return self.repeated('/workspace/maps/'+self.map_id+'/move',body,self.role(actor))

    def targets(self, actor):
        from urllib.parse import urlencode
        first = next((a for a in self.sheets[actor]['definition']['attacks'] if a.get('damage')), None)
        assert first is not None, 'No damaging attack on sheet'
        attack_id, slot = first['id'], 'melee' if first['id'] == 'melee' else 'ranged'
        workspace=self.get('/workspace?map_id='+self.map_id)
        pin=next(t for t in workspace['tokens'] if t.get('character_id')==actor)
        query=urlencode({'slot':slot,'map_id':self.map_id,'attacker_token_id':pin['id']})
        listed = self.get(f'/characters/{actor}/attacks/{attack_id}/targets?{query}', self.role(actor))
        assert listed['slot'] == slot, listed
        assert listed['gridded'], 'No logical grid on chosen map/pin; manual fallback is not grid evidence'
        assert listed['targets'], 'Grid sem alvos listados'
        assert any(t['valid'] for t in listed['targets']), 'Nenhum alvo válido no alcance'
        self.checks.add('alvos válidos/inválidos listados pelo alcance do grid')
        self.verify('range')
        return {'valid': sum(1 for t in listed['targets'] if t['valid']),
                'invalid': sum(1 for t in listed['targets'] if not t['valid'])}

    def counterattack(self, actor):
        for _ in range(12):
            state = self.get('/combat/effects')
            encounter = state.get('encounter') or {}
            members = encounter.get('participants') or []
            if not members:
                break
            current = members[int(encounter.get('turn_index') or 0) % len(members)]
            if current.get('target_id') == self.enemy['id']:
                break
            self.command('next_turn')
        before = self.get('/characters/' + actor, self.role(actor))['state']['current_hp']
        attack = self.repeated('/gm/combat/tokens/' + self.enemy['id'] + '/attacks/resolve',
                               {'request_id': self.prefix + '-' + uuid.uuid4().hex, 'attack_id': '0',
                                'target_type': 'character', 'target_id': actor,
                                'roll_mode': 'physical', 'd20': 20}, 'gm')
        confirmed = self.repeated('/combat/attacks/' + attack['resolution_id'] + '/confirm', {}, 'gm')
        after = self.get('/characters/' + actor, self.role(actor))['state']['current_hp']
        if attack.get('result') == 'hit':
            assert after < before, 'Acerto sem dano em ' + actor
            self.checks.add('inimigo ataca de volta e aplica dano no PC')
        else:
            self.checks.add('inimigo ataca e o PC esquiva (erro legítimo)')
        return {'victim': actor, 'hp_before': before, 'hp_after': after,
                'result': attack.get('result')}

    def guard_expiry(self):
        ally = next(t for t in self.get('/workspace')['tokens'] if t.get('character_id')=='vezemir')
        payload = {}  # Approved party-wide guard; no chosen ally.
        self.command('dorn_guard',payload,replay=True)
        assert any(e.get('protocol')=='guard' for e in self.get('/combat/effects')['effects'])
        before = {actor:self.get('/characters/'+actor)['state']['current_hp'] for actor in ('vezemir','dorn7')}
        self.advance_to(self.enemy['id'])
        attack = self.repeated('/gm/combat/tokens/'+self.enemy['id']+'/attacks/resolve',
            {'request_id':self.prefix+'-'+uuid.uuid4().hex, 'attack_id':'0',
             'target_type':'character','target_id':'vezemir','roll_mode':'physical','d20':20})
        confirmed = self.repeated('/combat/attacks/'+attack['resolution_id']+'/confirm', {})
        assert attack['target_id'] == 'dorn7', 'Attack was not redirected to Dorn'
        assert self.get('/characters/vezemir')['state']['current_hp'] == before['vezemir'], 'Guarda did not protect the ally'
        assert self.get('/characters/dorn7')['state']['current_hp'] == confirmed['hp_after'], 'Redirected HP was not persisted'
        damage=confirmed['breakdown']['guard_damage']
        assert damage['after']==damage['before']//2,'Guard must halve redirected damage'
        assert any(e.get('area_guard') for e in self.get('/combat/effects')['effects']),'Area guard must survive the first interception'
        self.advance_to('dorn7')
        assert not any(e.get('protocol')=='guard' for e in self.get('/combat/effects')['effects'])
        self.verify('range','expiration')
        return {'redirected_to_dorn':True,'expired_at_next_dorn_turn':True}

    def advance_to(self, actor):
        for _ in range(20):
            state=self.command('next_turn',replay=True)
            encounter=state.get('encounter') or {};members=encounter.get('participants') or []
            if members and members[encounter.get('turn_index',0)]['target_id']==actor:return
        raise AssertionError('Turn cycle did not return to '+actor)

    def approved_dorn(self, spell):
        key='dorn_'+spell.replace('-','_')
        payload={'spell_id':spell,'targets':[{'type':'token','id':self.enemy['id']}]}
        if spell=='dissipar-magia':
            seeded=self.command('dorn_spell_cast',{'spell_id':'forca-arcana','targets':[{'type':'token','id':self.enemy['id']}]})
            payload['effect_id']=seeded['protocol_result']['results'][0]['effect']['id']
            self.advance_to('dorn7')
        before=self.snapshot()['characters']['dorn7']['resources'][key]
        result=self.command('dorn_spell_cast',payload,replay=True)['protocol_result']
        assert self.snapshot()['characters']['dorn7']['resources'][key]==before-1
        self.verify('cost', 'range')
        if spell=='dissipar-magia':
            saving=result['results'][0]
            active=any(e['id']==payload['effect_id'] for e in self.get('/combat/effects')['effects'])
            assert active is not saving['success'], 'Dispel result disagrees with persisted effect'
        else:
            effect=result['results'][0]['effect']
            assert any(e['id']==effect['id'] for e in self.get('/combat/effects')['effects'])
            if spell=='reflexos':assert 2 <= effect['images_remaining'] <= 5
            if spell=='forca-arcana':assert effect['modifiers']['strength_bonus']==2  # declared test enemy FOR 10
            if spell=='teia':
                occupants=[e for e in self.get('/combat/effects')['effects'] if e.get('web_parent_id')==effect['id']]
                assert any(e['target_id']==self.enemy['id'] and e['modifiers']['armor_class_bonus']==-2 for e in occupants)
                workspace = self.get('/workspace'); grid = workspace['map']['grid']
                mine = next(t for t in workspace['tokens'] if t.get('character_id')=='dorn7')
                enemy = next(t for t in workspace['tokens'] if t['id']==self.enemy['id'])
                start, end = mine['grid_position'], enemy['grid_position']
                moved = self.repeated('/workspace/maps/'+self.map_id+'/move', {
                    'request_id':self.prefix+'-'+uuid.uuid4().hex, 'token_id':mine['id'], 'mode':'COMBAT_MOVE',
                    'path':[[start['cell_x'],start['cell_y']],[end['cell_x'],end['cell_y']]],
                    'expected_position_version':start['version'], 'expected_grid_version':grid['version'],
                    'expected_combat_version':self.get('/combat/effects')['version']})
                assert moved['movement']['spent_m'] == 3*grid['cell_size_m'], 'Teia must charge triple movement in its area'
                self.checks.add('Teia: passo na área cobra três vezes a escala; retry não repete gasto')
            self.command('dorn_spell_time',{'seconds':effect['remaining_seconds']},replay=True)
            assert not any(e['id']==effect['id'] or e.get('web_parent_id')==effect['id'] for e in self.get('/combat/effects')['effects'])
            self.verify('expiration')
        self.checks.add('magia aprovada: custo único, efeito persistido e encerramento nativo')
        return result

    def frenzy(self):
        before=self.snapshot()['characters']['vezemir']['resources']['frenesi']
        result=self.technique('vezemir','frenesi')['protocol_result']
        effect=result['effect'];assert 2<=effect['rounds']<=5 and effect['modifiers']['strength_bonus']==2
        assert self.snapshot()['characters']['vezemir']['resources']['frenesi']==before-1
        for _ in range(effect['rounds']):self.command('round',replay=True)
        assert not any(e.get('skill')=='frenesi' for e in self.get('/combat/effects')['effects'])
        self.verify('cost','expiration')
        return result

    def provocation(self):
        before=self.snapshot()['characters']['vezemir']['resources']['provocacao']
        result=self.technique('vezemir','provocacao')['protocol_result']
        assert result['targets'] and any(e['target_id']==self.enemy['id'] for e in result['targets'])
        assert self.snapshot()['characters']['vezemir']['resources']['provocacao']==before-1
        self.command('end',replay=True)
        assert not any(e.get('skill')=='provocacao' for e in self.get('/combat/effects')['effects'])
        self.verify('cost','range','expiration')
        return result

    def high_spell(self, spell):
        key=spell.replace('-','_')
        before=self.snapshot()['characters']['morthak']
        if spell=='clonagem':
            fragments=[i for i in self.get('/characters/morthak')['inventory'] if i['item_title']=='Fragmento de Cristal Arcano' and i['quantity']>0]
            if not fragments:
                return self.post('/characters/morthak/techniques/clonagem',{'request_id':self.prefix+'-'+uuid.uuid4().hex},'morthak',accepted=(400,409))
            component_total=sum(i['quantity'] for i in fragments)
        else:
            # Only the declared test enemy and four party pins participate in
            # this isolated death-spell case; campaign NPC DV are not invented.
            with closing(sqlite3.connect(self.database)) as db, db:
                db.execute("UPDATE session_workspace_tokens SET visible_to_players=0 WHERE map_id=? AND id<>? AND COALESCE(character_id,'') NOT IN ('vezemir','morthak','raziel','dorn7')",(self.map_id,self.enemy['id']))
        result=self.technique('morthak',spell)['protocol_result']
        after=self.snapshot()['characters']['morthak']
        assert after['resources'][key]==before['resources'][key]-1
        if spell=='magia-da-morte':
            assert after['hp']==before['hp']//10, 'Death spell self-cost must leave floor(10% current HP)'
            assert result['results'], 'No victims/save rolls were resolved'
        else:
            remaining=sum(i['quantity'] for i in self.get('/characters/morthak')['inventory'] if i['item_title']=='Fragmento de Cristal Arcano')
            assert remaining==component_total-1
            self.advance_to('morthak')
            clones=[t for t in self.get('/workspace')['tokens'] if t.get('sheet',{}).get('summon',{}).get('technique')=='clonagem']
            assert len(clones)==2 and all(t.get('grid_position') and t['current_hp']==max(1,before['max_hp']//4) for t in clones)
            self.technique('morthak',spell,mode='end')
            assert not any(t.get('sheet',{}).get('summon',{}).get('technique')=='clonagem' for t in self.get('/workspace')['tokens'])
            self.verify('expiration')
        self.verify('cost','range')
        return result

    def repair(self, seeded=False):
        if seeded:
            # Test-only inventory, not a reward delivered to the real Dorn.
            from sys import path
            path.insert(0,str(Path(__file__).resolve().parents[1]))
            from app.player_inventory import upsert_inventory
            upsert_inventory(self.database,profile_id='dorn7',item_path='fixture:repair-kit',item_title='Kit de Reparo',quantity=1,equipped=False,notes='Somente fixture descartável')
        body={'request_id':self.prefix+'-'+uuid.uuid4().hex}
        if not seeded and not any(i['item_title']=='Kit de Reparo' and i['quantity']>0 for i in self.baseline_inventory['dorn7']):
            return self.post('/characters/dorn7/techniques/dorn-reparo',body,accepted=(400,409))
        repaired=self.repeated('/characters/dorn7/techniques/dorn-reparo',body)
        return {'test_only_kit':seeded,'repair':repaired,'attack':self.attack('dorn7')}

    def defensive_blood(self):
        before=self.get('/characters/raziel')['definition']['defenses']['armor_class']
        blood=self.snapshot()['characters']['raziel']['resources']['reserva_de_sangue']
        self.technique('raziel','sangue-defensivo')
        assert self.get('/characters/raziel')['definition']['defenses']['armor_class']==before+2
        assert self.snapshot()['characters']['raziel']['resources']['reserva_de_sangue']==blood-1
        self.command('round')
        assert self.get('/characters/raziel')['definition']['defenses']['armor_class']==before
        self.checks.add('Sangue Defensivo: custo 1, +2 CA e remoção após uma rodada')
        return {'armor_class_bonus':2,'expired':True,'approval':'Approved by the Master on 2026-10-12'}

    def coffin(self):
        route='/characters/raziel/actions';body={'action':'rest_in_coffin','payload':{},'request_id':self.prefix+'-'+uuid.uuid4().hex,'reason':'Ensaio de Caixão'}
        first=self.repeated(route,body,'raziel')
        assert first['state']['current_hp']==first['state']['maximum_hp']
        assert next(r['current'] for r in first['state']['resources'] if r['key']=='caixao')==0
        denied=self.post(route,{**body,'request_id':self.prefix+'-'+uuid.uuid4().hex},'raziel',accepted=(400,))
        self.repeated(route,{'action':'rest_at_inn','payload':{},'request_id':self.prefix+'-'+uuid.uuid4().hex,'reason':'Descanso concedido pelo Mestre na fixture'})
        assert next(r['current'] for r in self.get('/characters/raziel')['state']['resources'] if r['key']=='caixao')==1
        self.repeated(route,{**body,'request_id':self.prefix+'-'+uuid.uuid4().hex},'raziel')
        self.checks.add('Caixão restaura PV e só o descanso do Mestre recarrega seu uso')
        return {'owner_rest':True,'blocked_before_gm_rest':denied,'gm_recharge':True}

    def insufficient(self, actor, technique=None, attack_id=None, resource=None):
        with closing(sqlite3.connect(self.database)) as db, db:
            state = json.loads(db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (actor,)).fetchone()[0])
            for counter in state['resources']:
                if counter['key'] in resource:
                    counter['current'] = 0
            db.execute('UPDATE character_states SET state_json=?,version=version+1 WHERE profile_id=?', (json.dumps(state),actor))
        before = self.snapshot()
        route = f'/characters/{actor}/techniques/{technique}' if technique else f'/characters/{actor}/attacks/resolve'
        body = {'request_id':self.prefix+'-'+uuid.uuid4().hex,'target_type':'token','target_id':self.enemy['id'],
                'roll_mode':'physical','d20':15}
        if technique:
            body['position_confirmed']=True
        if attack_id: body['attack_id'] = attack_id
        self.post(route,body,self.role(actor),accepted=(400,409))
        assert before == self.snapshot(), 'Rejected command mutated state'
        self.checks.add('recurso insuficiente rejeitado sem dano, custo ou efeito')
        return {'rejected_without_mutation':True}

    def permission_and_turn(self, actor):
        # The other player cannot act for this sheet. Then prove the owner
        # cannot spend a second attack in the same turn against a still-live target.
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('UPDATE session_workspace_tokens SET current_hp=500,maximum_hp=500 WHERE id=?', (self.enemy['id'],))
        body={'request_id':self.prefix+'-'+uuid.uuid4().hex,'attack_id':'melee', 'target_type':'token',
              'target_id':self.enemy['id'],'roll_mode':'physical','d20':15}
        stranger='morthak' if actor=='raziel' else 'raziel'
        before = self.snapshot()
        self.post('/characters/'+actor+'/attacks/resolve',body,stranger,accepted=(403,404))
        assert before == self.snapshot(), 'Unauthorized command mutated state'
        self.checks.add('outro proprietário rejeitado sem mutação')
        self.attack(actor)
        before = self.snapshot()
        self.post('/characters/'+actor+'/attacks/resolve',{**body,'request_id':self.prefix+'-'+uuid.uuid4().hex},self.role(actor),accepted=(400,409))
        assert before == self.snapshot(), 'Exhausted turn mutated state'
        self.checks.add('segundo ataque no mesmo turno rejeitado sem mutação')
        return {'owner_only':True,'turn_budget_enforced':True}

    def run(self):
        for actor in ACTORS:
            for attack in self.sheets[actor]['definition']['attacks']:
                missing=not attack.get('damage')
                coverage=('attack:'+attack['id'],'ability:'+attack['id'])+self.resource_keys(actor,attack['id'])
                self.case('Ataque '+attack['id'],actor,lambda a=actor,i=attack['id'],m=missing:self.rejected_attack(a,i) if m else self.attack(a,i),physical=True,blocked=missing,covers=coverage)
                if not missing and attack['id'] not in {'misseis-magicos'}:
                    self.case('Erro crítico '+attack['id'],actor,lambda a=actor,i=attack['id']:self.attack(a,i,d20=1),physical=True,covers=coverage)
            self.case('Movimento por célula',actor,lambda a=actor:self.move(a))
            self.case('Contra-ataque do inimigo',actor,lambda a=actor:self.counterattack(a),
                      covers=('enemy:counterattack',))
            self.case('Alvos no alcance do grid',actor,lambda a=actor:self.targets(a),
                      covers=('attack:melee',))
        for technique in ('forca-arcana','velocidade'):
            self.case(technique+' e expiração','vezemir',lambda t=technique:self.expiry(t),covers=('ability:'+technique,)+self.resource_keys('vezemir',technique))
        self.case('Pulseira de Vinhas e JP/turnos','vezemir',self.vines,covers=self.item_keys('vezemir','Pulseira de Vinhas'))
        for actor in ('vezemir','morthak','raziel'):
            self.potion_case(actor)
        self.case('Anel Rúnico','raziel',self.ring,combat=False,covers=self.item_keys('raziel','Anel Runico'))
        for amount in (1,5):
            self.case(f'Lâmina de Sangue {amount}d4','raziel',lambda n=amount:self.attack('raziel',technique='lamina-de-sangue',charges=n,attack='ranged'),physical=True,covers=('ability:lamina-de-sangue','resource:reserva_de_sangue'))
        self.case('Mordida e cura','raziel',lambda:self.attack('raziel',technique='mordida'),physical=True,covers=('ability:mordida',)+self.resource_keys('raziel','mordida'))
        self.case('Regeneração Vampírica','raziel',lambda:self.technique('raziel','regeneracao-vampirica'),covers=('ability:regeneracao-vampirica','resource:reserva_de_sangue'))
        def mark():
            self.clients['gm'].patch('/gm/workspace/tokens/'+self.enemy['id'],json={'current_hp':self.monster['average_hp']-1}).raise_for_status()
            result=self.technique('raziel','marca-rubra',target_type='token',target_id=self.enemy['id'])
            self.command('end')
            assert not any(e.get('hemomancy_kind')=='mark' for e in self.get('/combat/effects')['effects'])
            self.verify('expiration')
            return result
        self.case('Marca Rubra','raziel',mark,covers=('ability:marca-rubra','resource:reserva_de_sangue'))
        for weapon in ('arco','foice','marreta','lanca','escudo'):
            for skill in ((False,) if weapon=='escudo' else (False,True)):
                identity='hemomancia-'+weapon+('-habilidade' if skill else '')
                self.case('Hemomancia: '+identity,'raziel',lambda w=weapon,s=skill:self.hemomancy_use(w,s),physical=weapon!='escudo',
                    covers=('ability:'+identity,'resource:reserva_de_sangue'))
        self.case('Forma da Noite ligar/desligar','raziel',self.night,combat=False,covers=('ability:forma-da-noite',)+self.resource_keys('raziel','forma-da-noite'))
        for animal in ('morcego','coruja'):
            self.case('Forma da Noite: '+animal,'raziel',lambda a=animal:self.night(a),combat=False,covers=('ability:forma-da-noite',)+self.resource_keys('raziel','forma-da-noite'))
        self.case('Caixão: descanso próprio, retry e recarga somente pelo Mestre','raziel',self.coffin,combat=False,covers=('ability:caixao',)+self.resource_keys('raziel','caixao'))
        self.case('Sangue Defensivo aprovado: CA/expiração','raziel',self.defensive_blood,covers=('ability:sangue-defensivo','resource:reserva_de_sangue'))
        for technique in ('garras-predatorias','investida-predatoria','arma-de-sangue'):
            if any(a['id']==technique and not a.get('blocked') for a in self.sheets['raziel']['definition']['session_abilities']):
                coverage=('ability:'+technique,'resource:reserva_de_sangue')
                self.case(technique+' aprovado: backend','raziel',lambda t=technique:self.attack('raziel',technique=t),physical=True,covers=coverage)
                self.case(technique+' erro crítico','raziel',lambda t=technique:self.attack('raziel',technique=t,d20=1),physical=True,covers=coverage)
                self.case(technique+' sem sangue','raziel',lambda t=technique:self.insufficient('raziel',technique=t,resource=('reserva_de_sangue',)),physical=True,covers=coverage)
        def wounded_claws():
            self.clients['gm'].patch('/gm/workspace/tokens/'+self.enemy['id'],json={'current_hp':self.monster['average_hp']-1}).raise_for_status()
            result=self.attack('raziel',technique='garras-predatorias')
            base=next(a for a in self.sheets['raziel']['definition']['attacks'] if a['id']=='melee')['attack_bonus']
            tactical=int((result.get('breakdown',{}).get('attack') or {}).get('tactical_bonus') or 0)
            assert result['attack_bonus']==base+1+tactical
            return result
        self.case('Faro: bônus existente contra alvo ferido','raziel',wounded_claws,physical=True,covers=('ability:faro-de-sangue',))
        for actor in ('morthak','dorn7'):
            self.case('Mísseis Mágicos nível 5',''+actor,lambda a=actor:self.attack(a,'misseis-magicos',roll_mode='digital',d20=None),covers=('ability:misseis-magicos',)+self.resource_keys(actor,'misseis-magicos'))
        for actor in ('raziel','morthak'):
            self.case('Permissão de proprietário e limite de ataque no turno',actor,lambda a=actor:self.permission_and_turn(a),physical=True,covers=('attack:melee',))
        self.case('Mísseis sem usos','morthak',lambda:self.insufficient('morthak',attack_id='misseis-magicos',resource=('misseis_magicos',)),covers=('ability:misseis-magicos',)+self.resource_keys('morthak','misseis-magicos'))
        for technique in ('levantar-esqueleto','animar-mortos'):
            ability='levantar-um-esqueleto' if technique=='levantar-esqueleto' else technique
            self.case(technique+' + ataque da invocação','morthak',lambda t=technique:self.summoned(t),physical=True,covers=('ability:'+ability,)+self.resource_keys('morthak',ability))
        coverage=('ability:toque-sombrio',)+self.resource_keys('morthak','toque-sombrio')
        self.case('Toque Sombrio + dano inicial','morthak',lambda:self.attack('morthak',technique='toque-sombrio',position_confirmed=True),physical=True,covers=coverage,scenario_id='morthak:Toque Sombrio + dano/FOR/JPC')
        self.case('Toque Sombrio erro crítico','morthak',lambda:self.attack('morthak',technique='toque-sombrio',position_confirmed=True,d20=1),physical=True,covers=coverage)
        self.case('Toque sem uso diário nem círculo','morthak',lambda:self.insufficient('morthak',technique='toque-sombrio',resource=('toque_sombrio','magias_de_1o_circulo')),covers=coverage)
        self.case('Aterrorizar + DV/JPS','morthak',lambda:self.technique('morthak','aterrorizar',position_confirmed=True,targets=[{'type':'token','id':self.enemy['id'],'distance_meters':3}]),covers=('ability:aterrorizar',)+self.resource_keys('morthak','aterrorizar'))
        for spell in ('levitacao','escuridao','relampago'):
            self.case('Tomo: '+spell,'dorn7',lambda s=spell:self.command('dorn_spell_cast',{'spell_id':s,'targets':[{'type':'token','id':self.enemy['id'],'contacts':1}], 'distance_meters':3,'weight_kg':40,'unwilling':True,'shape':'line','position_confirmed':True},replay=True),covers=('ability:'+spell,)+self.resource_keys('dorn7',spell))
        self.case('Guarda e expiração no turno de Dorn','dorn7',self.guard_expiry,covers=('ability:dorn_guard',))
        self.case('Vanguarda','dorn7',lambda:self.command('dorn_vanguard',{'enabled':True},replay=True),combat=False,covers=('ability:dorn_vanguard',))
        self.case('Diagnóstico','dorn7',lambda:self.command('dorn_diagnose',{'subject':'Arma do hobgoblin do ensaio','difficulty':14},replay=True),covers=('ability:dorn_diagnose',))
        kit_missing=not any(i['item_title']=='Kit de Reparo' and i['quantity']>0 for i in self.baseline_inventory['dorn7'])
        self.case('Reparo com inventário real','dorn7',self.repair,physical=True,blocked=kit_missing,covers=('ability:dorn-reparo',)+self.item_keys('dorn7','Kit de Reparo'))
        self.case('Reparo + ataque, kit apenas na fixture','dorn7',lambda:self.repair(seeded=True),physical=True)
        for spell in ('reflexos','teia','forca-arcana','dissipar-magia'):
            self.case('Pacote aprovado: '+spell,'dorn7',lambda s=spell:self.approved_dorn(s),covers=('ability:'+spell,)+self.resource_keys('dorn7',spell))
        self.case('Frenesi: uso manual e expiração','vezemir',self.frenzy,covers=('ability:frenesi','resource:frenesi'))
        self.case('Provocação: grid e fim de combate','vezemir',self.provocation,covers=('ability:provocacao','resource:provocacao'))
        for spell in ('clonagem','magia-da-morte'):
            missing=spell=='clonagem' and not any(i['item_title']=='Fragmento de Cristal Arcano' and i['quantity']>0 for i in self.baseline_inventory['morthak'])
            self.case('Necromante nível 5: '+spell,'morthak',lambda s=spell:self.high_spell(s),blocked=missing,covers=('ability:'+spell,)+self.resource_keys('morthak',spell))
        unknown=self.scenarios-self.available_scenarios
        if unknown:
            raise ValueError('Unknown scenarios for selected actors: '+', '.join(sorted(unknown)))
        # Leave a disposable physical encounter ready for browser/GM-owner parity.
        self.reset('morthak',physical=True)
        sheet_report=build_report(self.sheets,self.results,actors=self.actors)
        coverage={actor:data['entries'] for actor,data in sheet_report['characters'].items()}
        (self.database.parent/'sheet-test-report.json').write_text(json.dumps(sheet_report,ensure_ascii=False,indent=2),encoding='utf-8')
        (self.database.parent/'sheet-test-report.md').write_text(render_report(sheet_report),encoding='utf-8')
        report={'run_id':self.prefix,'database':str(self.database),'map_id':self.map_id,'enemy_id':self.enemy['id'],'enemy_name':self.enemy['name'],'monster':self.monster,'catalog':self.catalog,'coverage':coverage,
                'declarations':['Independent scenarios restore HP and counters ONLY in the temporary copy.', 'SRD monster attribute scores are absent: 10 is an explicit test-only declaration.', 'Entered physical d20=15; no claim that a human rolled physical dice.'],
                'catalogue':{p:self.sheets[p]['definition']['session_abilities'] for p in ACTORS},'baseline':{p:{'definition':{k:self.sheets[p]['definition'].get(k) for k in ('id','level','attributes','attacks','defenses','progression')},'state':{k:self.sheets[p]['state'].get(k) for k in ('current_hp','maximum_hp','resources')}} for p in ACTORS},
                'results':self.results,'trace':self.trace}
        output=self.database.parent/'all-actions-evidence.json';output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        lines=['# Ensaio isolado de combate', '', *report['declarations'], '', '| Personagem | Ação | Resultado | Consequências |','|---|---|---|---|']
        for record in self.results:
            before=record.get('before',{}).get('characters',{});after=record.get('after',{}).get('characters',{})
            changes=[]
            for actor in ACTORS:
                if actor not in before or actor not in after:continue
                if before[actor]['hp']!=after[actor]['hp']:changes.append(f"{actor} PV {before[actor]['hp']} → {after[actor]['hp']}")
                for key,value in before[actor]['resources'].items():
                    end=after[actor]['resources'].get(key)
                    if value!=end:changes.append(f'{actor} {key} {value} → {end}')
            changes.extend(e['title'] for e in record.get('ledger',[]) if e.get('title'))
            detail=record.get('error') or '; '.join(changes) or 'Ver resultado e snapshots no JSON'
            lines.append(f"| {record['actor']} | {record['action']} | {record['status']} | {detail.replace('|','/').replace(chr(10),' ')} |")
        lines.extend(['','## Catálogo completo: cobertura, não certificação de passivas',''])
        for actor,entries in coverage.items():
            lines.append(f"- {actor}: "+'; '.join(f"{a['key']} = {a['status']}" for a in entries))
        (self.database.parent/'all-actions-log.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        print('EVIDENCE='+str(output));print('COUNTS='+json.dumps({s:sum(r['status']==s for r in self.results) for s in ('PASS','FAIL','EXPECTED_BLOCK')}))
        return not any(r['status']=='FAIL' for r in self.results)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--database',type=Path,required=True);parser.add_argument('--port',type=int,default=8871)
    parser.add_argument('--actors',nargs='+',choices=ACTORS,default=list(ACTORS))
    parser.add_argument('--scenarios',nargs='+',help='Exact scenario_id values from an earlier report; omitted = all supported cases')
    args=parser.parse_args();simulation=Simulation(args.database,args.port,args.actors,args.scenarios)
    try: ok=simulation.run()
    finally:
        for client in simulation.clients.values():client.close()
    raise SystemExit(0 if ok else 1)

if __name__=='__main__':main()
