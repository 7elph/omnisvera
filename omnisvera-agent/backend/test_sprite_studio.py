"""Visual assets only: disposable DB, no real sheets or combat changes."""
import base64
import copy
import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from PIL import Image
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.access import AccessContext
from app import sprite_studio as studio
from app.session_workspace import init_session_workspace, save_workspace_token, get_workspace_snapshot


def png(size=(64, 32)):
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    image.putpixel((min(8,size[0]-1),min(8,size[1]-1)), (40, 180, 255, 255))
    result = io.BytesIO(); image.save(result, format='PNG')
    return base64.b64encode(result.getvalue()).decode()


def metadata():
    return dict(schema_version=1, canvas_width=32, canvas_height=32, pivot=[.5, .5], scale=1,
        frames=[dict(x=0, y=0, w=32, h=32, offset_x=0, offset_y=0, scale=1),
                dict(x=32, y=0, w=32, h=32, offset_x=0, offset_y=0, scale=1)],
        animations={'idle':dict(frames=[0], fps=4, loop=True, direction='down'),
                    'walk_down':dict(frames=[0, 1], fps=8, loop=True, direction='down')})


class SpriteStudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'fixture.sqlite3'
        from app.character_play import init_character_play
        from app.character_creation import init_character_creation
        from app.dice_rolls import init_dice_rolls
        from app.session_ledger import init_session_ledger
        init_character_play(self.path);init_character_creation(self.path);init_dice_rolls(self.path)
        init_session_workspace(self.path)
        init_session_ledger(self.path)
        studio.initialize(self.path)
        self.gm = AccessContext(mode='gm')
        self.player = AccessContext(mode='player', profile_id='raziel')
        self.token = save_workspace_token(self.path, token_type='character', character_id='dorn7',
            name='Dorn', latitude=40, longitude=40, visible_to_players=True)

    def save(self, **updates):
        args=dict(request_id='sprite-create-001', asset_id=None, expected_version=0,
                  name='Dorn teste', metadata=metadata(), png_base64=png())
        args.update(updates)
        return studio.save_asset(self.path, self.gm, **args)

    def bind(self, asset):
        return studio.bind_asset(self.path, self.gm, request_id='sprite-binding-001',
            entity_type='character', entity_id='dorn7', asset_id=asset['id'])

    def test_import_rgba_metadata_retry_and_reopen(self):
        first=self.save(); self.assertEqual(self.save(), first)
        self.assertEqual(first['width'],64)
        content=studio.image_bytes(self.path, first['id'], first['image_hash'], self.gm)
        self.assertEqual(Image.open(io.BytesIO(content)).getpixel((0,0))[3],0)
        studio.initialize(self.path)
        self.assertEqual(studio.library(self.path,self.gm)[0]['metadata'],metadata())
        with self.assertRaises(ValueError): self.save(name='different')

    def test_validation_rejects_bad_images_frames_missing_refs_and_numeric_extremes(self):
        for content in ['broken',base64.b64encode(b'<svg/>').decode()]:
            with self.assertRaises(ValueError): self.save(png_base64=content)
        for field,value in [('schema_version',2),('scale',float('nan')),('pivot',[2,0]),('frames',[])]:
            meta=metadata();meta[field]=value
            with self.assertRaises(ValueError):self.save(metadata=meta)
        meta=metadata();meta['frames'][1]['x']=63
        with self.assertRaises(ValueError):self.save(metadata=meta)
        meta=metadata();meta['animations']['idle']['frames']=[10]
        with self.assertRaises(ValueError):self.save(metadata=meta)
        with self.assertRaises(ValueError):self.save(png_base64=png((4097,1)))

    def test_replacement_preserves_identity_bindings_and_rejects_stale_editor(self):
        first=self.save();self.bind(first)
        edited=metadata();edited['animations']['idle']['fps']=6
        changed=self.save(request_id='sprite-edit-001',asset_id=first['id'],expected_version=1,metadata=edited,png_base64=None)
        self.assertEqual(changed['id'],first['id']);self.assertEqual(changed['version'],2)
        with self.assertRaises(ValueError):self.save(request_id='sprite-stale-001',asset_id=first['id'],expected_version=1)
        snapshot=studio.enrich_tokens(self.path,[self.token])
        self.assertEqual(snapshot[0]['sprite']['version'],2)
        self.assertEqual(snapshot[0]['sprite']['metadata']['animations']['idle']['fps'],6)

    def test_binding_is_visual_only_and_unbind_restores_static(self):
        first=self.save()
        with closing(sqlite3.connect(self.path)) as db:before=db.execute('SELECT * FROM session_workspace_tokens').fetchall()
        self.bind(first)
        with closing(sqlite3.connect(self.path)) as db:after=db.execute('SELECT * FROM session_workspace_tokens').fetchall()
        self.assertEqual(before,after)
        self.assertIn('sprite',get_workspace_snapshot(self.path,is_gm=True)['tokens'][0])
        studio.bind_asset(self.path,self.gm,request_id='sprite-unbind-001',entity_type='character',entity_id='dorn7',asset_id=None)
        self.assertNotIn('sprite',studio.enrich_tokens(self.path,[self.token])[0])
        with self.assertRaises(ValueError):studio.bind_asset(self.path,self.gm,request_id='sprite-invalid-001',entity_type='token',entity_id='missing',asset_id=first['id'])

    def test_private_library_and_media_not_disclosed_before_visible_binding(self):
        first=self.save()
        with self.assertRaises(PermissionError):studio.library(self.path,self.player)
        with self.assertRaises(PermissionError):studio.save_asset(self.path,self.player,request_id='sprite-hack-001',name='x',metadata=metadata(),png_base64=png(),asset_id=None,expected_version=0)
        with self.assertRaises(PermissionError):studio.image_bytes(self.path,first['id'],first['image_hash'],self.player)
        self.bind(first)
        self.assertTrue(studio.image_bytes(self.path,first['id'],first['image_hash'],self.player))
        with closing(sqlite3.connect(self.path)) as db,db:db.execute('UPDATE session_workspace_tokens SET visible_to_players=0')
        with self.assertRaises(PermissionError):studio.image_bytes(self.path,first['id'],first['image_hash'],self.player)

    def test_token_binding_and_ledger_once(self):
        first=self.save()
        args=dict(request_id='sprite-token-bind',entity_type='token',entity_id=self.token['id'],asset_id=first['id'])
        for _ in range(2):studio.bind_asset(self.path,self.gm,**args)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM session_ledger WHERE source_type='sprite_studio'").fetchone()[0],2)
        with self.assertRaises(ValueError):studio.bind_asset(self.path,self.gm,**{**args,'asset_id':None})

    def test_routes_auth_export_and_invalid_content(self):
        app=FastAPI();active=[self.gm]
        studio.register(app,lambda:self.path,lambda:active[0])
        with TestClient(app) as client:
            asset=client.post('/gm/sprites',json=dict(request_id='sprite-http-001',name='Sheet',metadata=metadata(),png_base64=png())).json()
            self.assertIn('id',asset)
            response=client.get('/gm/sprites/'+asset['id']+'/export')
            self.assertEqual(response.status_code,200);self.assertEqual(response.headers['content-type'],'application/zip')
            active[0]=self.player
            self.assertEqual(client.get('/gm/sprites').status_code,403)
            self.assertEqual(client.get('/workspace/sprites/'+asset['id']+'/'+asset['image_hash']+'.png').status_code,403)
            self.assertEqual(client.post('/gm/sprites',json={}).status_code,422)


if __name__=='__main__':unittest.main()
