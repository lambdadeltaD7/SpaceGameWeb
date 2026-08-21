from typing import Annotated

from logic import generate_world_dict

from fastapi import (
    APIRouter, Depends,
    HTTPException, status
)
from endpoints.auth import get_or_create_session

from db_connection import r_sessions, sql_engine
from db_models import UsersSchemaDB, WorldsSchemaDB, PlanetsSchemaDB

from sqlalchemy import select
from sqlalchemy.orm import Session

from exceptions import *

router = APIRouter(prefix="/api/v1/admin")


def check_admin(
    session_id: Annotated[str, Depends(get_or_create_session)]
):
    user_id = r_sessions.hget(f"ses_{session_id}", "user_id")

    if user_id != "":

        with Session(sql_engine) as ses:
            stmt = select(
                        UsersSchemaDB
                    ).where(
                        UsersSchemaDB.user_id == int(user_id)
                    )

            user_obj = ses.scalar(stmt)

        if user_obj.is_admin:
            return True

    return False



@router.delete("/kill_session")
def kill_session(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: str
):
    if not is_admin:
        raise OnlyForAdminsException()

    user_id = r_sessions.hget(f"ses_{session_id}", "user_id")
    if user_id != "":
        r_sessions.srem(f"user_sessions:{user_id}", session_id)
        
    cnt_deleted_sess = r_sessions.delete(f"ses_{session_id}")

    return {"log" : f"cancelled {cnt_deleted_sess} sessions"}


@router.get("/sessions")
def get_sessions(is_admin: Annotated[bool, Depends(check_admin)]):

    if not is_admin:
        raise OnlyForAdminsException()

    _, keys = r_sessions.scan(0, "ses_*")
    
    sessions = []

    for k in keys:
        ses_id = k[4:]
        user_id = r_sessions.hget(k, "user_id")
        sessions.append({
            "session_id" : ses_id,
            "user_data"  : r_sessions.json().get(f"user_info:{user_id}") 
        })

    return sessions


def init_world_db(seed: int, user_id: int):
    _world, _planets = generate_world_dict(seed)

    world = WorldsSchemaDB(
        user_id = user_id,
        is_public = True,
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
    
    return _world["seed"], world, planets


@router.post("/generate_world", tags=["worlds"])
def post_generate_world(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    user_id: int,
    seed: int | None = None
):

    requester_uid = r_sessions.hget(f"ses_{session_id}", "user_id")

    if (str(user_id) != requester_uid) and (not is_admin):
        raise NotOwnerException()

    world_seed, world, planets = init_world_db(seed, user_id)

    with Session(sql_engine) as ses:
        ses.add(world)
        ses.commit()
        ses.refresh(world)

        for p in planets:
            p.world_id = world.world_id
            p.user_id = user_id
        
        ses.add_all(planets)
        ses.commit()
    
    return world_seed