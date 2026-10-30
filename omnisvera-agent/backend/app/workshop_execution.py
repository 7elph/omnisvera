"""Explicitly configured execution; outputs remain private drafts, never commands."""
import json
import os
import time
import copy
import hashlib
import urllib.request
import re
import unicodedata
from collections import Counter
from pathlib import Path
from .ai_workshop_adapters import ImageAssetAdapter,WorkshopAdapterError


def configuration():
    defaults={'code_provider':'opencode','enabled':False,'text':True,'image':False,'code':False,'min_free_ram_mb':1024,
              'daily_limits':{'text':12,'image':2,'code':6},'idle_seconds':30}
    configured=os.environ.get('AI_WORKSHOP_CONFIG_FILE')
    if not configured:return defaults
    path=Path(configured)
    if not path.is_file():return defaults
    raw=json.loads(path.read_text(encoding='utf-8'))
    for key in ('enabled','text','image','code'):
        if key in raw:
            if type(raw[key]) is not bool:raise ValueError('Invalid automation flag')
            defaults[key]=raw[key]
    defaults['min_free_ram_mb']=max(1024,min(262144,int(raw.get('min_free_ram_mb',1024))))
    defaults['idle_seconds']=max(5,min(3600,int(raw.get('idle_seconds',30))))
    provider=raw.get('code_provider','opencode')
    if provider not in {'opencode','ollama-cloud'}:raise ValueError('Invalid code analysis provider')
    defaults['code_provider']=provider
    limits=raw.get('daily_limits') or {}
    for queue in ('text','image','code'):
        value=limits.get(queue,defaults['daily_limits'][queue])
        if type(value) is not int or not 0<=value<=1000:raise ValueError('Invalid configured daily budget')
        defaults['daily_limits'][queue]=value
    return defaults


def generate_draft(settings,identity,mode):
    # The caller already owns the native workload slot. Reuse the asset pipeline.
    from .asset_api import _generate_job
    return _generate_job(settings,identity,mode)


def authorized_roster():
    """Local read only; do not forward an auth header through proxies/redirects."""
    from .ai_preparation_context import party_context
    root=Path(__file__).resolve().parents[2]
    token=os.environ.get('OMNISVERA_MASTER_TOKEN')
    if not token:
        token=json.loads((root/'backend/data/access_tokens.json').read_text(encoding='utf-8-sig'))['master_token']
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    request=urllib.request.Request('http://127.0.0.1:8787/characters',headers={'X-Omnisvera-Token':token})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(request,timeout=10) as response:roster=json.loads(response.read(256001))
    return party_context(roster)


class ContextTextAdapter:
    uses_external_budget=True
    def __init__(self,adapter,context_loader=authorized_roster):self.adapter=adapter;self.context_loader=context_loader
    def __call__(self,job):
        try:context=self.context_loader()
        except Exception:raise WorkshopAdapterError('config',message_code='current_party_context_unavailable') from None
        current=copy.deepcopy(job);payload=current.setdefault('payload_json',{})
        payload['facts']=[r for r in payload.get('facts',[]) if not(isinstance(r,dict) and r.get('kind')=='current_party_snapshot')]+[context]
        result=self.adapter(current)
        result['output']['party_context_sha256']=hashlib.sha256(json.dumps(context,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        notes=quality_notes(result['output'].get('draft',''),context)
        if notes:
            result['status']='needs_review';result['output']['quality_notes']=notes
        return result


def quality_notes(text,context=None):
    """Conservative structural check, never a claim that other prose is factual."""
    def norm(value):return ''.join(c for c in unicodedata.normalize('NFKD',value).casefold() if not unicodedata.combining(c))
    notes=[]
    if len(text)>50000:notes.append('oversized_block')
    fragments=[re.sub(r'\s+',' ',part).strip().casefold() for part in re.split(r'[.!?]\s+|\n+',text)]
    counts=Counter(part for part in fragments if len(part)>=24)
    repeated=sum(len(part)*count for part,count in counts.items() if count>=3)
    if repeated>=240 and repeated>=len(text)*.4:notes.append('repeated_content')
    split=(re.search(r'(?im)^#{1,4}[^\n]*(?:perguntas|dúvidas|duvidas|questões|questoes)[^\n]*',text)
           or re.search(r'(?im)^\s*\*{0,2}(?:dúvidas|duvidas|perguntas|questões|questoes)\b',text))
    if split:
        body=norm(text[:split.start()]);questions=text[split.start():]
        known={norm(m.get('name','')) for m in (context or {}).get('members',[])}
        uncertain=set()
        for line in questions.splitlines():
            if not any(word in norm(line) for word in ('quem','significa','incert','asr','erro de','nao criar')):continue
            for value in re.findall(r'[“«"]([^”»"\n]{1,60})[”»"]',line):
                key=norm(value.strip())
                if key and key not in known and len(key.split())<=3:uncertain.add(key)
        if any(name in body for name in uncertain):notes.append('uncertain_names_used_as_lore')
    return notes


class ImageGenerationAdapter:
    uses_external_budget=True
    def __init__(self,settings):self.settings=settings
    def __call__(self,job):
        from .asset_generation import get_job
        queued=ImageAssetAdapter(self.settings.database_path)(job)
        identity=int(queued['external_ref'].split(':')[-1])
        asset=get_job(identity,database_path=self.settings.database_path)
        if asset['status']=='generating':
            raise WorkshopAdapterError('timeout_ambiguous',message_code='image_generation_in_progress',ambiguous=True)
        started=time.perf_counter();generated=False
        if asset['status'] not in {'awaiting_approval','ready','approved'}:
            try:asset=generate_draft(self.settings,identity,'official');generated=True
            except Exception as error:
                cause=error.__cause__ or error
                reason=getattr(cause,'reason','unknown')
                if reason in {'daily_quota','quota'}:
                    raise WorkshopAdapterError('quota',retry_after_seconds=3600,message_code='image_provider_quota') from None
                if reason=='auth':raise WorkshopAdapterError('auth_permanent',message_code='image_provider_auth') from None
                if isinstance(cause,TimeoutError) or 'timeout' in reason:
                    raise WorkshopAdapterError('timeout_ambiguous',message_code='image_timeout',ambiguous=True) from None
                raise WorkshopAdapterError('provider_error',retry_after_seconds=300,message_code='image_provider_unavailable') from None
        if not asset.get('image_path') or not asset['image_path'].startswith(('draft:','zz_media/')):
            raise WorkshopAdapterError('provider_error',message_code='image_result_missing')
        output={**queued['output'],'provider':'asset_generation','model':'flux-2-klein-9b',
                'asset_job_id':identity,'image_path':asset['image_path'],
                'draft':'Imagem gerada para revisão privada. A imagem atual foi preservada.',
                'generated':generated}
        return {'status':'awaiting_approval','external_ref':queued['external_ref'],'output':output,
                'metrics':{'provider':'asset_generation','model':'flux-2-klein-9b',
                           'duration_ms':int((time.perf_counter()-started)*1000),'samples':1}}


class CodeOllamaAdapter:
    """Explicit cloud text analysis fallback. It has no file/command/tool executor."""
    uses_external_budget=True
    def __init__(self,adapter):self.adapter=adapter
    def __call__(self,job):
        try:result=self.adapter(job)
        except WorkshopAdapterError as error:
            error.provider='ollama-code'
            raise
        result['output']['executed_suggestions']=False
        result['output']['execution_route']='ollama_cloud_code_analysis'
        return result
