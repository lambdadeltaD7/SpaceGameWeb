from typing import Annotated

from logic import generate_world

from fastapi import (
    APIRouter, Depends,
    HTTPException, status
)

from endpoints.auth import get_or_create_session

from db_models import UsersSchemaDB, WorldsSchemaDB, PlanetsSchemaDB
from db_connection import r_sessions, sql_engine
from sqlalchemy.orm import Session
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/admin")


def check_admin(
    session_id: Annotated[str, Depends(get_or_create_session)]
):
    user_id = r_sessions.hget(session_id, "user_id")

    ex = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail = "this is only for admins"
    )

    if user_id != "":
        with Session(sql_engine) as ses:
            stmt = select(UsersSchemaDB).where(UsersSchemaDB.user_id==int(user_id))
            result = ses.scalar(stmt)
        if result.is_admin:
            return True

    return False


@router.get("/sessions")
def get_sessions(is_admin: Annotated[bool, Depends(check_admin)]):

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "only for admins"
        )

    _, keys = r_sessions.scan(0, "*")
    res = []
    for k in keys:
        res.append({"session_id":k, "user_data":r_sessions.hgetall(k)})
    return res


@router.post("/generate_world", tags=["worlds"])
def post_generate_world(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    user_id: int,
    seed: int | None = None
):

    true_uid = r_sessions.hget(session_id, "user_id")

    if (str(user_id) != true_uid) and (not is_admin):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "you must be an owner or admin to do this"
        )

    _world, _planets = generate_world(seed)

    world = WorldsSchemaDB(
        user_id=user_id,
        is_public=True,
        **_world
    )

    planets = []

    for p in _planets:
        planets.append(
            PlanetsSchemaDB(
                world_id = 0,
                shield_on = False,
                **p
            )
        )

    with Session(sql_engine) as ses:
        ses.add(world)
        ses.commit()
        ses.refresh(world)

        for p in planets:
            p.world_id = world.world_id
        
        ses.add_all(planets)
        ses.commit()
    
    return _world["seed"]