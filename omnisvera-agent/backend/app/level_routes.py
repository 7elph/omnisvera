from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from . import level_advancement


class LevelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hp_roll: StrictInt | None = Field(default=None, ge=1, le=10)
    target_level: StrictInt | None = Field(default=None, ge=2, le=20)
    hp_policy: str = Field(default='preserve_wounds', pattern='^(preserve_current|preserve_wounds)$')


class LevelConfirmation(LevelRequest):
    fingerprint: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


class ManualHpAcknowledgement(BaseModel):
    model_config=ConfigDict(extra='forbid')
    level: StrictInt=Field(ge=2,le=20)
    reason: str=Field(min_length=1,max_length=500)


def register(app, require_master, character_loader, database_path):
    @app.post('/gm/characters/{profile_id}/level/manual-hp')
    def manual_hp(profile_id: str, request: ManualHpAcknowledgement, access=Depends(require_master)):
        from contextlib import closing
        from .character_play import _connect
        from .level_recalculation import acknowledge_manual_hp
        character_loader(profile_id,access)
        try:
            with closing(_connect(database_path())) as db,db:
                db.execute('BEGIN IMMEDIATE')
                return acknowledge_manual_hp(db,profile_id,request.level,actor_id='master',actor_role='gm',reason=request.reason)
        except ValueError as error:raise HTTPException(409,str(error)) from error
    @app.post("/gm/characters/{profile_id}/level/preview")
    def preview(profile_id: str, request: LevelRequest, access=Depends(require_master)):
        try:
            result = level_advancement.preview(database_path(), character_loader(profile_id, access), request.hp_roll, request.target_level, request.hp_policy)
            return {k: v for k, v in result.items() if not k.startswith("_")}
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/gm/characters/{profile_id}/level/confirm")
    def confirm(profile_id: str, request: LevelConfirmation, access=Depends(require_master)):
        try:
            applied = level_advancement.apply(database_path(), character_loader(profile_id, access), request.fingerprint, request.hp_roll, request.target_level, request.hp_policy)
            return {"applied": applied, "character": character_loader(profile_id, access)}
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
