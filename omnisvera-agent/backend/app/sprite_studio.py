"""Independent sprite atlas library. Visual bindings never mutate native entities.

PNG bytes and versioned metadata live together in SQLite. Only an already-visible
native pin can expose an atlas to players. No image generation service is assumed.
"""
import base64
import binascii
import hashlib
import io
import json
import re
import sqlite3
import warnings
import zipfile
from contextlib import closing
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import Depends, HTTPException, Response
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationError, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Frame(StrictModel):
    x: StrictInt = Field(ge=0, le=4095)
    y: StrictInt = Field(ge=0, le=4095)
    w: StrictInt = Field(ge=1, le=4096)
    h: StrictInt = Field(ge=1, le=4096)
    offset_x: StrictInt = Field(default=0, ge=-1024, le=1024)
    offset_y: StrictInt = Field(default=0, ge=-1024, le=1024)
    scale: float = Field(default=1, ge=.1, le=4)


class Animation(StrictModel):
    frames: list[StrictInt] = Field(min_length=1, max_length=256)
    fps: float = Field(default=6, ge=1, le=30)
    loop: bool = True
    direction: str = Field(default='down', pattern=r'^[a-z_]{1,32}$')
    durations_ms: list[StrictInt] | None = Field(default=None, max_length=256)

    @model_validator(mode='after')
    def timings(self):
        if self.durations_ms is not None and (len(self.durations_ms) != len(self.frames) or
                any(n < 34 or n > 10000 for n in self.durations_ms)):
            raise ValueError('Durações devem corresponder aos quadros, entre 34 e 10000 ms')
        return self


class Metadata(StrictModel):
    schema_version: Literal[1] = 1
    canvas_width: StrictInt = Field(ge=1, le=1024)
    canvas_height: StrictInt = Field(ge=1, le=1024)
    pivot: tuple[float, float] = (.5, .5)
    scale: float = Field(default=1, ge=.25, le=4)
    frames: list[Frame] = Field(min_length=1, max_length=256)
    animations: dict[str, Animation] = Field(min_length=1, max_length=32)

    @model_validator(mode='after')
    def references(self):
        if any(not 0 <= n <= 1 for n in self.pivot):raise ValueError('Pivô fora do quadro')
        for state, animation in self.animations.items():
            if not re.fullmatch(r'[a-z][a-z0-9_]{0,39}', state):raise ValueError('Estado inválido')
            if any(n < 0 or n >= len(self.frames) for n in animation.frames):
                raise ValueError('Animação referencia quadro ausente')
        return self


def connect(path):
    db=sqlite3.connect(path, timeout=30);db.row_factory=sqlite3.Row
    return db


def initialize(path):
    with closing(connect(path)) as db, db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS sprite_assets(
          id TEXT PRIMARY KEY, name TEXT NOT NULL, metadata_json TEXT NOT NULL,
          png BLOB NOT NULL, image_hash TEXT NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL,
          version INTEGER NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sprite_bindings(
          entity_type TEXT NOT NULL CHECK(entity_type IN ('character','token')),
          entity_id TEXT NOT NULL, asset_id TEXT NOT NULL REFERENCES sprite_assets(id),
          PRIMARY KEY(entity_type,entity_id));
        CREATE TABLE IF NOT EXISTS sprite_commands(
          request_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, response_json TEXT NOT NULL);
        ''')


def _master(access):
    if access.mode != 'gm':raise PermissionError('Somente o Mestre edita sprites')


def _dto(row, public=False):
    result={key:row[key] for key in ('id','version','image_hash','width','height')}
    result['metadata']=json.loads(row['metadata_json'])
    if not public:result.update(name=row['name'],updated_at=row['updated_at'])
    return result


def _png(encoded):
    if len(encoded)>12_000_000:raise ValueError('PNG excede 8 MB')
    try:
        raw=base64.b64decode(encoded,validate=True)
        if len(raw)>8_000_000:raise ValueError('PNG excede 8 MB')
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if image.format!='PNG' or getattr(image,'n_frames',1)!=1:raise ValueError('Importe PNG estático ou sprite sheet PNG')
                if max(image.size)>4096 or image.width*image.height>8_000_000:raise ValueError('Imagem excede 4096 px ou 8 megapixels')
                image.load();rgba=image.convert('RGBA');target=io.BytesIO();rgba.save(target,format='PNG')
                return target.getvalue(),image.width,image.height
    except (binascii.Error,UnidentifiedImageError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning) as exc:
        raise ValueError('PNG inválido ou grande demais') from exc


def _fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()


def _replay(db,request_id,fingerprint):
    if not re.fullmatch(r'[a-zA-Z0-9_-]{8,120}',request_id):raise ValueError('Identidade de comando inválida')
    row=db.execute('SELECT * FROM sprite_commands WHERE request_id=?',(request_id,)).fetchone()
    if row:
        if row['fingerprint']!=fingerprint:raise ValueError('Comando reutilizado com outro conteúdo')
        return json.loads(row['response_json'])


def _finish(db,request_id,fingerprint,response,title,detail):
    from .session_ledger import append_session_ledger_event
    append_session_ledger_event(db,source_type='sprite_studio',source_id=request_id,event_kind='state',
        actor_id='master',actor_name='Mestre',actor_role='gm',character_id=None,title=title,
        detail=detail,visibility='gm',created_at=datetime.now(timezone.utc).isoformat())
    db.execute('INSERT INTO sprite_commands VALUES(?,?,?)',(request_id,fingerprint,json.dumps(response)))
    return response


def save_asset(path,access,*,request_id,name,metadata,png_base64=None,asset_id=None,expected_version=0):
    _master(access)
    if not name.strip() or len(name)>100:raise ValueError('Informe nome de até 100 caracteres')
    try:meta=Metadata.model_validate(metadata).model_dump(mode='json',exclude_none=True)
    except ValidationError as exc:raise ValueError(str(exc)) from exc
    image=_png(png_base64) if png_base64 is not None else None
    fp=_fingerprint([name,meta,hashlib.sha256(image[0]).hexdigest() if image else None,asset_id,expected_version])
    with closing(connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        replay=_replay(db,request_id,fp)
        if replay:return replay
        old=db.execute('SELECT * FROM sprite_assets WHERE id=?',(asset_id,)).fetchone() if asset_id else None
        if asset_id and (not old or old['version']!=expected_version):raise ValueError('Asset mudou; recarregue antes de salvar')
        if not asset_id and expected_version!=0:raise ValueError('Versão inicial inválida')
        if not image:
            if not old:raise ValueError('Importe um PNG')
            image=(old['png'],old['width'],old['height'])
        content,width,height=image
        for frame in meta['frames']:
            if frame['x']+frame['w']>width or frame['y']+frame['h']>height:raise ValueError('Recorte fora da imagem')
        identity=asset_id or uuid4().hex
        db.execute('''INSERT INTO sprite_assets VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
          name=excluded.name,metadata_json=excluded.metadata_json,png=excluded.png,image_hash=excluded.image_hash,
          width=excluded.width,height=excluded.height,version=excluded.version,updated_at=excluded.updated_at''',
          (identity,name.strip(),json.dumps(meta),content,hashlib.sha256(content).hexdigest(),width,height,
           (old['version'] if old else 0)+1,datetime.now(timezone.utc).isoformat()))
        result=_dto(db.execute('SELECT * FROM sprite_assets WHERE id=?',(identity,)).fetchone())
        return _finish(db,request_id,fp,result,'Sprite salvo',{'asset_id':identity,'version':result['version'],'image_hash':result['image_hash']})


def library(path,access):
    _master(access)
    with closing(connect(path)) as db:
        return [_dto(row) for row in db.execute('SELECT id,name,metadata_json,image_hash,width,height,version,updated_at FROM sprite_assets ORDER BY name')]


def bind_asset(path,access,*,request_id,entity_type,entity_id,asset_id):
    _master(access)
    if entity_type not in ('character','token'):raise ValueError('Tipo de vínculo inválido')
    fp=_fingerprint([entity_type,entity_id,asset_id])
    with closing(connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        replay=_replay(db,request_id,fp)
        if replay:return replay
        if entity_type=='token':
            exists=db.execute('SELECT 1 FROM session_workspace_tokens WHERE id=?',(entity_id,)).fetchone()
        else:
            exists=db.execute('SELECT 1 FROM session_workspace_tokens WHERE character_id=?',(entity_id,)).fetchone()
            if not exists and db.execute("SELECT 1 FROM sqlite_master WHERE name='character_states'").fetchone():
                exists=db.execute('SELECT 1 FROM character_states WHERE profile_id=?',(entity_id,)).fetchone()
        if not exists:raise ValueError('Entidade existente não encontrada')
        if asset_id:
            if not db.execute('SELECT 1 FROM sprite_assets WHERE id=?',(asset_id,)).fetchone():raise ValueError('Sprite inexistente')
            db.execute('INSERT INTO sprite_bindings VALUES(?,?,?) ON CONFLICT(entity_type,entity_id) DO UPDATE SET asset_id=excluded.asset_id',(entity_type,entity_id,asset_id))
        else:db.execute('DELETE FROM sprite_bindings WHERE entity_type=? AND entity_id=?',(entity_type,entity_id))
        result={'entity_type':entity_type,'entity_id':entity_id,'asset_id':asset_id}
        return _finish(db,request_id,fp,result,'Visual do pin atualizado',result)


def enrich_tokens(path,tokens):
    """Read-only, one batched metadata query AFTER native visibility filtering."""
    with closing(connect(path)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='sprite_bindings'").fetchone():return tokens
        bindings={(r['entity_type'],r['entity_id']):r for r in db.execute('''SELECT b.entity_type,b.entity_id,
          a.id,a.version,a.metadata_json,a.image_hash,a.width,a.height FROM sprite_bindings b JOIN sprite_assets a ON a.id=b.asset_id''')}
        for token in tokens:
            row=bindings.get(('token',token['id'])) or bindings.get(('character',token.get('character_id')))
            if row and not (token.get('sheet') or {}).get('corpse'):token['sprite']=_dto(row,public=True)
    return tokens


def image_bytes(path,asset_id,image_hash,access):
    if access.mode!='gm':
        from .session_workspace import get_workspace_snapshot
        visible=get_workspace_snapshot(path,is_gm=False)['tokens']
        if not any(t.get('sprite',{}).get('id')==asset_id for t in visible):raise PermissionError('Sprite não está em um pin visível')
    with closing(connect(path)) as db:
        row=db.execute('SELECT png FROM sprite_assets WHERE id=? AND image_hash=?',(asset_id,image_hash)).fetchone()
        if not row:raise ValueError('Imagem indisponível; atualize o asset')
        return bytes(row['png'])


class SaveRequest(StrictModel):
    request_id: str = Field(min_length=8,max_length=120)
    asset_id: str | None = None
    expected_version: StrictInt = Field(default=0,ge=0)
    name: str = Field(min_length=1,max_length=100)
    metadata: Metadata
    png_base64: str | None = Field(default=None,max_length=12_000_000)


class BindingRequest(StrictModel):
    request_id: str = Field(min_length=8,max_length=120)
    entity_type: Literal['character','token']
    entity_id: str = Field(min_length=1,max_length=160)
    asset_id: str | None = None


def register(app,get_path,require_any):
    def execute(fn,*args,**kwargs):
        try:return fn(get_path(),*args,**kwargs)
        except PermissionError as exc:raise HTTPException(403,str(exc)) from exc
        except ValueError as exc:raise HTTPException(409,str(exc)) from exc

    @app.get('/gm/sprites')
    def listing(access=Depends(require_any)):return execute(library,access)

    @app.post('/gm/sprites')
    def save(request:SaveRequest,access=Depends(require_any)):
        return execute(save_asset,access,**request.model_dump(mode='json',exclude_none=True))

    @app.post('/gm/sprites/binding')
    def binding(request:BindingRequest,access=Depends(require_any)):
        return execute(bind_asset,access,**request.model_dump())

    @app.get('/workspace/sprites/{asset_id}/{image_hash}.png')
    def image(asset_id:str,image_hash:str,access=Depends(require_any)):
        content=execute(image_bytes,asset_id,image_hash,access)
        # Revalidate authorization on every fetch; browser must not retain hidden assets.
        return Response(content,media_type='image/png',headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

    @app.get('/gm/sprites/{asset_id}/export')
    def export(asset_id:str,access=Depends(require_any)):
        items=execute(library,access);asset=next((a for a in items if a['id']==asset_id),None)
        if not asset:raise HTTPException(404,'Sprite inexistente')
        content=execute(image_bytes,asset_id,asset['image_hash'],access)
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr('sheet.png',content)
            bundle.writestr('sprite.json',json.dumps({'name':asset['name'],'image':'sheet.png',**asset['metadata']},ensure_ascii=False,indent=2))
        return Response(output.getvalue(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="sprite.zip"','Cache-Control':'no-store'})

    @app.on_event('startup')
    def startup():initialize(get_path())
