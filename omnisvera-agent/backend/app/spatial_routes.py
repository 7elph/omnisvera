"""Commands on existing workspace maps; authentication supplied by the host app."""
from typing import Literal
from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from . import spatial_grid as spatial


class GridCommand(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: str = Field(min_length=8, max_length=120)
    expected_version: int = 0
    cols: StrictInt = Field(ge=1, le=200)
    rows: StrictInt = Field(ge=1, le=200)
    cell_size_m: float = Field(gt=0)
    origin_x: float = Field(default=0, ge=0, lt=100)
    origin_y: float = Field(default=0, ge=0, lt=100)
    distance_rule: Literal['chebyshev','manhattan'] = 'chebyshev'


class MoveCommand(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: str = Field(min_length=8, max_length=120)
    token_id: str
    mode: Literal['COMBAT_MOVE','GM_REPOSITION']
    path: list[tuple[StrictInt, StrictInt]] = Field(min_length=1,max_length=401)
    expected_position_version: int
    expected_grid_version: int
    expected_combat_version: int | None = None


def register_spatial_routes(app, get_path, require_any, load_movement):
    def execute(function, **args):
        try:
            return function(get_path(), **args)
        except PermissionError as error:
            raise HTTPException(403, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error

    @app.post('/workspace/maps/{map_id}/grid')
    def configure(map_id: str, request: GridCommand, access=Depends(require_any)):
        config=request.model_dump(exclude={'request_id','expected_version'})
        return execute(spatial.configure_grid, actor_id=access.profile_id or 'master',role=access.mode,
            request_id=request.request_id,map_id=map_id,config=config,expected_version=request.expected_version)

    @app.post('/workspace/maps/{map_id}/move')
    def move(map_id: str, request: MoveCommand, access=Depends(require_any)):
        if access.mode != 'gm' and not access.profile_id:
            raise HTTPException(403,'Acesso individual de jogador necessário')
        args=request.model_dump(exclude={'path'})
        return execute(spatial.move_entity, actor_id=access.profile_id or 'master',role=access.mode,
            map_id=map_id,cells=[list(cell) for cell in request.path],load_movement=load_movement,**args)

    @app.get('/workspace/maps/{map_id}/distance')
    def distance(map_id: str, token_a: str, token_b: str, access=Depends(require_any)):
        return execute(spatial.distance_between,map_id=map_id,token_a=token_a,token_b=token_b,role=access.mode)

    @app.on_event('startup')
    def initialize():
        spatial.seed_session7_grids(get_path())
