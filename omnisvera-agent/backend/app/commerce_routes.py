from typing import Literal
from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from . import map_commerce as commerce


class Command(BaseModel):
    model_config=ConfigDict(extra='forbid')
    request_id: str = Field(min_length=8,max_length=120)


class QuoteRequest(Command):
    character_id: str = Field(min_length=1,max_length=80)
    kind: Literal['buy','sell','service']
    target_id: str = Field(min_length=1,max_length=300)
    quantity: StrictInt = Field(default=1,ge=1,le=999)
    negotiate: bool = False
    inventory_id: StrictInt | None = Field(default=None,gt=0)


class MerchantBinding(BaseModel):
    model_config=ConfigDict(extra='forbid')
    token_id: str
    npc_id: int | None = None
    location_id: int | None = None
    enabled: bool = True
    buy_pct: StrictInt = Field(default=50,ge=0,le=100)
    policy: dict[str,list[str]]|None=None


class ServiceCreate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    name: str = Field(min_length=1,max_length=120)
    kind: Literal['delivery','lodging','appraisal','spell','repair']
    price_copper: StrictInt = Field(ge=0,le=100000000)
    compendium_item_id: str | None = None
    amount: StrictInt = Field(default=1,ge=1,le=999)
    stock_id: str | None = None
    spell_id: str | None = None


class IndividualAppraisal(Command):
    character_id: str = Field(min_length=1,max_length=80)
    item_path: str = Field(min_length=1,max_length=300)
    unit_copper: StrictInt = Field(ge=0,le=100000000)


class TradeProfile(Command):
    item_path: str = Field(min_length=1,max_length=300)
    price_copper: StrictInt = Field(ge=0,le=100000000)
    trade_group: str


def register(app,get_path,require_any):
    def execute(fn,*args,**kwargs):
        try: return fn(get_path(),*args,**kwargs)
        except PermissionError as error: raise HTTPException(403,str(error)) from error
        except ValueError as error: raise HTTPException(409,str(error)) from error

    @app.get('/workspace/tokens/{token_id}/commerce')
    def offers(token_id:str,character_id:str|None=None,access=Depends(require_any)):
        return execute(commerce.for_pin,token_id,access,character_id)

    @app.get('/gm/items/audit')
    def items_audit(access=Depends(require_any)):
        if access.mode!='gm':raise HTTPException(403,'Somente o Mestre consulta a auditoria')
        from .item_registry import audit_items
        from .workshop_execution import configuration
        report=audit_items(get_path());report['workshop_configuration']=configuration()
        return report

    @app.post('/gm/items/generation-plan')
    def plan_items(request:Command,access=Depends(require_any)):
        from .item_registry import enqueue_gaps
        from .ai_workshop_routes import workshop_database_path
        return execute(enqueue_gaps,workshop_database_path(),access,request_id=request.request_id)

    @app.get('/gm/items/trade-catalog')
    def trade_catalog(access=Depends(require_any)):
        if access.mode!='gm':raise HTTPException(403,'Somente o Mestre configura catálogos')
        import sqlite3
        from contextlib import closing
        from .item_registry import registry,catalog_item
        with closing(sqlite3.connect(get_path())) as db:
            db.row_factory=sqlite3.Row
            items=[catalog_item(i) for i in registry(db)['entries'].values()]
        return {'catalog':{},'count':len(items),'total':len(items),'items':items}

    @app.put('/gm/items/trade-profile')
    def trade_profile(request:TradeProfile,access=Depends(require_any)):
        from .item_registry import set_trade_profile
        return execute(set_trade_profile,access,**request.model_dump())

    @app.get('/commerce/characters/{character_id}/history')
    def history(character_id:str,access=Depends(require_any)):
        return execute(commerce.history,access,character_id)

    @app.put('/gm/merchants/{merchant_id}/binding')
    def bind(merchant_id:str,request:MerchantBinding,access=Depends(require_any)):
        return execute(commerce.configure,merchant_id,access,**request.model_dump())

    @app.post('/gm/merchants/{merchant_id}/services')
    def service(merchant_id:str,request:ServiceCreate,access=Depends(require_any)):
        return execute(commerce.add_service,merchant_id,access,**request.model_dump())

    @app.post('/gm/merchants/{merchant_id}/individual-appraisals')
    def individual_appraisal(merchant_id:str,request:IndividualAppraisal,access=Depends(require_any)):
        return execute(commerce.appraise_item,merchant_id,access,**request.model_dump())

    @app.get('/gm/merchants/magic-services/catalog')
    def magic_catalog(access=Depends(require_any)):
        if access.mode!='gm':raise HTTPException(403,'Somente o Mestre configura atendimento mágico')
        from .merchant_magic import catalogue
        return catalogue()

    @app.post('/gm/merchants/{merchant_id}/magic-services/defaults')
    def magic_defaults(merchant_id:str,request:Command,access=Depends(require_any)):
        from .merchant_magic import configure_defaults
        return execute(configure_defaults,merchant_id,access)

    @app.get('/gm/npcs/{npc_id}/campaign-combat-profile')
    def npc_profile(npc_id:int,access=Depends(require_any)):
        if access.mode!='gm':raise HTTPException(403,'Somente o Mestre consulta a configuração de combate')
        from .npc_campaign_profile import proposal
        return proposal()

    @app.post('/gm/npcs/{npc_id}/campaign-combat-profile')
    def npc_apply_profile(npc_id:int,request:Command,access=Depends(require_any)):
        from .npc_campaign_profile import apply
        return execute(apply,npc_id,access,request_id=request.request_id)

    @app.post('/commerce/{merchant_id}/quotes')
    def quote(merchant_id:str,request:QuoteRequest,access=Depends(require_any)):
        return execute(commerce.quote,merchant_id,access,**request.model_dump())

    @app.delete('/gm/merchants/{merchant_id}/services/{service_id}')
    def remove_service(merchant_id:str,service_id:str,access=Depends(require_any)):
        return execute(commerce.remove_service,merchant_id,service_id,access)

    @app.post('/commerce/quotes/{quote_id}/confirm')
    def confirm(quote_id:str,request:Command,access=Depends(require_any)):
        return execute(commerce.confirm,quote_id,access,request_id=request.request_id)

    @app.on_event('startup')
    def initialize(): commerce.initialize(get_path())
