"""Provision the ROM2 scenario through existing authenticated map contracts.
No character-sheet mutation. Existing scenarios are not resized or overwritten.
"""
import base64

def prepare(client, preview):
    effects=client.get('/combat/effects');effects.raise_for_status()
    if effects.json().get('encounter',{}).get('active'):
        raise RuntimeError('Combat active: refusing to change the shared scenario')
    maps=client.get('/workspace/maps');maps.raise_for_status()
    matches=[m for m in maps.json() if m.get('title')=='Arredores de Nimalis']
    if len(matches)>1: raise RuntimeError('Ambiguous scenario; no changes applied')
    if matches: scenario=matches[0]
    else:
        response=client.post('/gm/workspace/map',json={
            'title':'Arredores de Nimalis','filename':'arredores-nimalis.webp',
            'content_type':'image/webp','visible_to_players':True,
            'data_base64':base64.b64encode(preview.read_bytes()).decode()})
        response.raise_for_status();scenario=response.json()
    snapshot=client.get('/workspace',params={'map_id':scenario['id']});snapshot.raise_for_status()
    grid=snapshot.json().get('map',{}).get('grid') or {}
    if grid.get('cols')!=80 or grid.get('rows')!=80 or grid.get('cell_size_m')!=1:
        response=client.post('/workspace/maps/'+scenario['id']+'/grid',json={
            'request_id':'rom2-full-grid-'+scenario['id']+'-'+str(grid.get('version',0)),
            'expected_version':grid.get('version',0),'cols':80,'rows':80,'cell_size_m':1,
            'origin_x':0,'origin_y':0,'distance_rule':'chebyshev'})
        response.raise_for_status()
    existing={t.get('character_id') for t in snapshot.json().get('tokens',[])}
    for character,x,y in [('dorn7',6,6),('morthak',8,6),('vezemir',6,8),('raziel',8,8)]:
        if character in existing: continue
        response=client.post('/gm/workspace/tokens',json={
            'token_type':'character','character_id':character,'name':character,
            'map_id':scenario['id'],'visible_to_players':True,
            'longitude':100*(x+.5)/80,'latitude':100*(y+.5)/80})
        response.raise_for_status()
    response=client.patch('/gm/workspace/maps/active',json={'map_id':scenario['id']})
    response.raise_for_status()
    return scenario['id']
