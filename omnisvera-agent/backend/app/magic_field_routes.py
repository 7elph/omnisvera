from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, JsonValue

from . import magic_field_items as items


class Interaction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    item_path: str = Field(min_length=1, max_length=300)
    operation: str = Field(min_length=1, max_length=30)
    fields: dict[str, JsonValue] = Field(default_factory=dict, max_length=6)
    request_id: str = Field(min_length=8, max_length=120)


def register(app, get_path, require_any):
    def call(fn, *args):
        try:
            return fn(get_path(), *args)
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get('/characters/{owner}/inventory/field-item')
    def get_item(owner: str, item_path: str, access=Depends(require_any)):
        return call(items.inspect, access, owner, item_path)

    @app.post('/characters/{owner}/inventory/field-item')
    def use_item(owner: str, payload: Interaction, access=Depends(require_any)):
        return call(items.execute, access, owner, payload.item_path, payload.operation, payload.fields, payload.request_id)

    @app.get('/gm/maps/{map_id}/physical-tracks')
    def physical_tracks(map_id: str, access=Depends(require_any)):
        return call(items.tracks, access, map_id)
