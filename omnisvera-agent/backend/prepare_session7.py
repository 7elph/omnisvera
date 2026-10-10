"""Create-only preparation using native Companion tables/APIs; never starts a live table.

Run from repository root: python backend/prepare_session7.py --install
--encounter is an explicit GM command, used only after activating this session/scene.
"""
from __future__ import annotations
import argparse
from contextlib import closing
from html import escape
import json
from pathlib import Path
import sqlite3

from app.session7_content import BRIEFING, ENEMIES, HANDOUTS, MAPS, NPCS, PLAYERS, SCENES, SUMMARY, TITLE
from app.scene_play import create_session, create_scene, create_element, add_participant, list_sessions, list_scenes, SCENE_CHECKLIST_KEYS
from app.session_workspace import set_workspace_map, list_workspace_maps, save_workspace_token, list_workspace_tokens, update_workspace_fog, save_session_item, list_session_items
from app.loot import init_loot
from app.npc_memory import init_npc_memory, create_npc

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT.parent
DATABASE = ROOT / "backend/data/omnisvera_companion.sqlite3"


def map_svg(title, rooms):
    # Code-generated schematic, not AI artwork. No secret clues printed on player maps.
    cells = ''.join(f'<path d="M{x*40} 0V960"/>' for x in range(33))
    cells += ''.join(f'<path d="M0 {y*40}H1280"/>' for y in range(25))
    shapes = ''.join(f'<rect x="{x*40}" y="{y*40}" width="{w*40}" height="{h*40}" rx="5" fill="#3c4145" stroke="#aaaba3" stroke-width="4"/><text x="{(x+w/2)*40}" y="{(y+h/2)*40}" text-anchor="middle" fill="#fff" font-size="22">{escape(label)}</text>' for x,y,w,h,label in rooms)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="960" viewBox="0 0 1280 960"><rect width="1280" height="960" fill="#22282c"/><g stroke="#778080" opacity=".25">{cells}</g>{shapes}<text x="20" y="28" fill="#ead9b7" font-size="22">{escape(title)} · célula 1,5 m · coberturas, não paredes contínuas</text></svg>'


def _token(db, map_id, name, **values):
    existing = next((t for t in list_workspace_tokens(db,map_id) if t['name']==name), None)
    return existing or save_workspace_token(db,map_id=map_id,name=name,**values)


def _sheet(name, spec):
    attacks = [dict(name=spec['weapon'],bonus=spec['bonus'],damage=spec['damage'])]
    if name == 'Caçador de Captura':
        attacks.append(dict(name='Virote sedativo · JP após acerto',bonus=2,damage='1d4'))
    description=spec.get('description',spec.get('special','')).split('Sabe:')[0]
    return dict(name=name,armor_class=spec['ac'],hit_points=spec['hp'],saving_throw=spec['jp'],
                movement=str(spec.get('moves',9)),attacks=attacks,treasure='Q',
                special=spec.get('special',description),description=description,
                action_budget=1,alignment='Neutro',session7=True,marker='session7')


def install(db: Path, vault: Path) -> dict:
    """Idempotent create-only: no character state, inventory, existing scenes or clock changes."""
    sessions = list_sessions(db)
    conflict = next((s for s in sessions if s.get('session_number')==7 and s.get('request_id')!='session7-portoes-fechados-v1'),None)
    if conflict:
        raise ValueError('Já existe outra Sessão 7; preservar e revisar manualmente antes de instalar')
    session, created = create_session(db,request_id='session7-portoes-fechados-v1',campaign_id='omnisvera',title=TITLE,session_number=7,created_by='master',private_notes=BRIEFING)
    init_npc_memory(db)
    npc_records={}
    for index,(name,spec) in enumerate(NPCS.items()):
        npc_records[name]=create_npc(db,request_id=f'session7-npc-profile-{index}',campaign_id='omnisvera',actor_id='master',fields=dict(name=name,portrait_path=spec['image'],race='Humano',class_or_role=name,current_location='Nimalis',public_description=spec['description'].split('Sabe:')[0],private_description=spec['description'],canonical_status='Proposto para Sessão 7; não jogado',visible_to_players=False))[0]
    npc_records['Serren Kaal']=create_npc(db,request_id='session7-npc-serren',campaign_id='omnisvera',actor_id='master',fields=dict(name='Serren Kaal',portrait_path='zz_media/class/cacador.png',race='Humano',class_or_role='Comandante de captura',current_location='Âncora Partida',public_description='Profissional de poucas palavras com arpão portátil, atento às saídas.',private_description=ENEMIES['Serren Kaal']['special'],canonical_status='Proposto para Sessão 7; não jogado',visible_to_players=False))[0]
    narrative = {'participants':[{'character_id':p,'name':p.capitalize()} for p in PLAYERS],
        'open_threads':[{'title':'Dragões e captura','description':'O responsável pela captura continua desconhecido.'},
                        {'title':'Tecnologia antiga reutilizada','description':'A função completa dos componentes não foi estabelecida.'}],
        'tags':['preparação proposta','não jogada']}
    with closing(sqlite3.connect(db)) as con, con:
        if created:
            con.execute('UPDATE game_sessions SET public_summary=?,gm_summary=?,narrative_json=? WHERE id=?',
                (SUMMARY,BRIEFING,json.dumps(narrative,ensure_ascii=False),session['id']))
        else:
            # Repair only our first, unplayed preparation's invalid collection shape.
            raw = con.execute('SELECT narrative_json,status FROM game_sessions WHERE id=?',(session['id'],)).fetchone()
            legacy = {'participants':['Vezemir','Morthak','Raziel'],'open_threads':['Dragões e captura','Tecnologia antiga reutilizada'],'tags':['preparação proposta','não jogada']}
            if raw[1]=='planned' and json.loads(raw[0] or '{}')==legacy:
                con.execute('UPDATE game_sessions SET narrative_json=? WHERE id=?',(json.dumps(narrative,ensure_ascii=False),session['id']))
    map_records = {}
    asset_dir = vault / 'zz_media/session7'
    asset_dir.mkdir(parents=True,exist_ok=True)
    for key,(title,rooms) in MAPS.items():
        relative = f'zz_media/session7/{key}.svg'
        target = vault / relative
        if not target.exists():
            target.write_text(map_svg(title,rooms),encoding='utf-8')
        m = next((m for m in list_workspace_maps(db) if m['title']==title),None)
        if not m:
            m = set_workspace_map(db,title=title,image_path=relative,visible_to_players=False)
            # Ready to reveal immediately; enemies remain individually hidden.
            for layer in ('exploration','battle'):
                update_workspace_fog(db,map_id=m['id'],layer=layer,enabled=False,revealed_cells=[])
        map_records[key]=m
        for index,character in enumerate(PLAYERS):
            _token(db,m['id'],character.capitalize(),token_type='character',character_id=character,
                latitude=86,longitude=42+index*7,image_path=f'zz_media/characters/{character}.{"jpg" if character=="morthak" else "png"}',visible_to_players=True)
        # Reuse actual Dorn identity; no detached duplicate sheet or stat recreation.
        _token(db,m['id'],'Dorn',token_type='character',character_id='dorn7',latitude=90,longitude=40,visible_to_players=True)
    scenes=[]
    for index,(title,key,opening,notes,npcs) in enumerate(SCENES):
        visual = {'port':'zz_media/locations/mare_baixa.png','conclave':'zz_media/faction/conclave_dos_errantes.png','gate':'zz_media/maps/mapa_de_nimalis.png'}.get(key,map_records[key]['image_path'])
        scene,new = create_scene(db,request_id=f'session7-scene-{index+1:02}',campaign_id='omnisvera',session_id=session['id'],
            title=title,location_name=map_records[key]['title'],created_by='master',public_description=opening,
            objective='Investigar, conversar ou agir conforme as escolhas do grupo; nenhuma solução obrigatória.',private_notes=notes,
            image_path=visual,map_id=map_records[key]['id'],visibility='table',checklist={k:True for k in SCENE_CHECKLIST_KEYS})
        scenes.append(scene)
        if new:
            for character in PLAYERS:
                add_participant(db,scene['id'],participant_type='player_character',character_id=character,public_label=character.capitalize())
            add_participant(db,scene['id'],participant_type='npc',character_id='dorn7',npc_name='Dorn',public_label='Dorn',private_status='Aliado; não decide pelos jogadores.')
            for name in npcs:
                add_participant(db,scene['id'],participant_type='npc',npc_name=name,npc_source=f'npc:{npc_records[name]["id"]}',public_label=name,visible_to_players=False,private_status='Ficha, motivações e informações no elemento privado deste NPC.')
        for name in npcs:
            spec=NPCS[name]
            create_element(db,scene['id'],request_id=f'session7-npc-{index}-{list(NPCS).index(name)}',element_type='object',title=f'NPC · {name}',status='prepared',visibility='gm',created_by='master',private_description=spec['description'],public_description=spec['description'].split('Sabe:')[0])
            _token(db,map_records[key]['id'],name,token_type='monster',latitude=35,longitude=50,image_path=spec['image'],
                current_hp=spec['hp'],maximum_hp=spec['hp'],visible_to_players=False,sheet=_sheet(name,spec))
    for scene_index,title,public,private in HANDOUTS:
        create_element(db,scenes[scene_index]['id'],request_id=f'session7-handout-{HANDOUTS.index((scene_index,title,public,private))+1}',
            element_type='clue',title=title,status='prepared',visibility='gm',created_by='master',public_description=public,private_description=private)
    # Physical clues stored separately from handouts; GM can reveal independently.
    clues=[('Sangue e rastros','Sangue seco em cabo e marcas de arrasto sob as caixas.','Raziel SAB 12: não humano, compatível com evidência anterior, idade aproximada. Vezemir INT/FOR 12: ancoragem de captura profissional.'),
           ('Ressonância residual','O encaixe apresenta uma vibração fraca perto de fontes de mana.','Morthak INT 12: resíduo mágico; só reage se aproximar cristal/grimório por decisão própria. Dorn diagnóstico 14: contenção biológica, arquivo indisponível.'),
           ('Rotas alternativas','Uma passagem de cargas comunica com o cais; documentos têm cópia no porto.','Falha não bloqueia: seguir equipe -> 07; investigar cidade -> 08; terceira opção válida.')]
    for i,(title,public,private) in enumerate(clues):
        create_element(db,scenes[5]['id'],request_id=f'session7-clue-{i}',element_type='clue',title=title,status='prepared',visibility='gm',created_by='master',public_description=public,private_description=private)
    for i,title in enumerate(('Preservar documentos','Impedir fuga de carga','Interceptar mensageiro','Capturar testemunha viva','Recuperar encaixe antigo')):
        create_element(db,scenes[5]['id'],request_id=f'session7-objective-{i}',element_type='objective',title=title,status='available',visibility='gm',created_by='master',public_description=title,private_description='Objetivo opcional. Exige ações/posição plausível; consequências e prazos nas notas da cena. Não é condição obrigatória de avanço.')
    enemy_tokens=[]
    for name,lat,lon in [('Caçador de Captura',30,24),('Operador de Corrente',60,35),('Artífice de Campo',62,58),('Serren Kaal',30,75),('Caçador de Captura · reserva',25,90)]:
        spec=ENEMIES[name.split(' · ')[0]]
        enemy_tokens.append(_token(db,map_records['inside']['id'],name,token_type='monster',latitude=lat,longitude=lon,
            current_hp=spec['hp'],maximum_hp=spec['hp'],visible_to_players=False,image_path='zz_media/class/cacador.png',sheet=_sheet(name.split(' · ')[0],spec)))
    from app.scene_play import scene_view
    participants=scene_view(db,scenes[5]['id'],access_mode='gm',profile_id=None)['participants']
    for token in enemy_tokens:
        if not any(p['public_label']==token['name'] for p in participants):
            source=f'npc:{npc_records["Serren Kaal"]["id"]}' if token['name']=='Serren Kaal' else f'map-token:{token["id"]}'
            add_participant(db,scenes[5]['id'],participant_type='npc' if token['name']=='Serren Kaal' else 'creature',npc_name=token['name'],npc_source=source,public_label=token['name'],visible_to_players=False,private_status='Reserva: não participa inicialmente.' if 'reserva' in token['name'] else 'Preparado; confronto não obrigatório.')
    for i,(name,lat,lon) in enumerate([('Mesa de documentos',25,67),('Carroça cinza',25,82),('Encaixe de contenção',65,25),('Saída para o cais',88,90)]):
        _token(db,map_records['inside']['id'],name,token_type='location',latitude=lat,longitude=lon,visible_to_players=False)
    # Existing native item catalog, no automatic grant or loot on preparation.
    item_specs=[('Fragmento de liga de contenção','Material','Encaixe incompleto e instável; não concede bônus. Só pode ser entregue após recuperado.'),
                ('Virotes de campo','Munição','Munição comum recuperável: até 6 intactos, a critério da cena; nenhum sedativo adicional mágico.'),
                ('Recibo de frete MB-17','Documento','Cópia do código de remessas; informação, não prova da identidade do mandante.')]
    existing_items=list_session_items(db)
    for name,kind,description in item_specs:
        if not any(i['name']==name for i in existing_items):
            save_session_item(db,name=name,item_type=kind,description=description,effects=['Sem bônus mecânico.'],usable=False)
    # Native draft loot is ready for GM reveal/distribution even after peaceful recovery.
    init_loot(db)
    rewards=[dict(id='s7-coins',name='Peças de ouro',kind='currency',quantity=20),
             dict(id='s7-bolts',name='Virotes de campo',kind='Munição',quantity=6),
             dict(id='s7-alloy',name='Fragmento de liga de contenção',kind='Material',quantity=1,description='Encaixe incompleto; sem bônus.'),
             dict(id='s7-receipt',name='Recibo de frete MB-17',kind='Documento',quantity=1,description='Código de remessa, não identidade do mandante.')]
    with closing(sqlite3.connect(db)) as con, con:
        con.execute("INSERT OR IGNORE INTO loot_resolutions(resolution_id,request_id,source_key,source_type,source_id,source_name,treasure_code,treasure_scope,roll_mode,rewards_json,rolls_json,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,'draft',datetime('now'))",
            ('loot:session7-cache','session7-loot-cache-v1','lair:session7-anchor','lair','session7-anchor','Âncora Partida · caixa recuperável','Preparado S7','lair','quick',json.dumps(rewards,ensure_ascii=False),'[]'))
    create_element(db,scenes[6]['id'],request_id='session7-loot-cache',element_type='object',title='Espólio recuperável — não automático',status='prepared',visibility='gm',created_by='master',public_description='Caixa de pagamentos, munição intacta, recibos e peças de oficina.',private_description='20 PO no máximo, 6 virotes comuns, um encaixe e recibos se preservados. Sem item mágico forte. Usar loot nativo após derrota ou grant de itens após negociação/recuperação; não exigir matar. Tesouro Q nos inimigos é alternativa, não somar caixa e rolagens para inflacionar recompensa. Contato/reputação só conforme ações reais.')
    return dict(session_id=session['id'],title=TITLE,scenes=[s['id'] for s in scenes],maps={k:v['id'] for k,v in map_records.items()},enemy_tokens=[t['id'] for t in enemy_tokens],players=list(PLAYERS),allies=['dorn7'])


def start_encounter(db: Path, *, include_dorn=False):
    """Native encounter action, guarded against old sessions/battles; no separate presets table."""
    from app.combat_effects import effect_command,readeffects
    from app.session_workspace import update_workspace_token
    session=next(s for s in list_sessions(db) if s.get('request_id')=='session7-portoes-fechados-v1')
    scene=next(s for s in list_scenes(db) if s['request_id']=='session7-scene-06')
    if session['status']!='active' or scene['status']!='active':
        raise ValueError('Inicie Sessão 7 e abra cena 06 na mesa antes do encontro')
    snapshot=readeffects(db)
    if snapshot.get('encounter',{}).get('active'):
        raise ValueError('Existe combate ativo; não será substituído')
    tokens=[t for t in list_workspace_tokens(db,scene['map_id']) if t['token_type']=='monster' and 'reserva' not in t['name']]
    participants=[dict(target_type='character',target_id=p,name=p.capitalize(),initiative=20-i) for i,p in enumerate(PLAYERS)]
    if include_dorn:
        participants.append(dict(target_type='character',target_id='dorn7',name='Dorn',initiative=15))
    participants += [dict(target_type='token',target_id=t['id'],name=t['name'],initiative=12-i) for i,t in enumerate(tokens)]
    result=effect_command(db,actor_id='master',actor_role='gm',request_id='session7-warehouse-start-v1',expected_version=snapshot['version'],action='start',payload=dict(title='Âncora Partida · provas e captura',map_id=scene['map_id'],participants=participants,battle_mode=True,game_session_id=session['id'],scene_id=scene['id']))
    for t in tokens:
        update_workspace_token(db,token_id=t['id'],visible_to_players=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=DATABASE)
    parser.add_argument('--vault',type=Path,default=VAULT)
    parser.add_argument('--install',action='store_true')
    parser.add_argument('--encounter',action='store_true')
    parser.add_argument('--include-dorn',action='store_true')
    args=parser.parse_args()
    if not args.install and not args.encounter:
        parser.error('Escolha --install ou --encounter; nada foi modificado')
    if args.install:
        print(json.dumps(install(args.db,args.vault),ensure_ascii=False,indent=2))
    if args.encounter:
        print(json.dumps(start_encounter(args.db,include_dorn=args.include_dorn),ensure_ascii=False,indent=2))
