from typing import Annotated

import logging

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, text

from endpoints.miners import miner_from_str
from endpoints.planets import planet_from_str
from endpoints.admin import check_admin
from endpoints.auth import get_or_create_session
from fastapi import APIRouter, HTTPException, status, Depends, Query

from pd_models import WorldsSchemaPD
from db_models import WorldsSchemaDB, PlanetsSchemaDB, MinersSchemaDB

from db_connection import sql_engine, r_sessions, r_game

from exceptions import *

router = APIRouter(prefix="/api/v1/worlds")

logger = logging.getLogger(__name__)

def log_msg(txt):
    print('#'*64)
    print('#'*64)
    print(txt)
    print('#'*64)
    print('#'*64)


@router.get("/")
def get_worlds(
    user_id: int | None = None,
    limit:   int | None = Query(default=67, ge=0, le=67),
    offset:  int | None = Query(default=0,  ge=0)
):

    with Session(sql_engine) as ses:
        stmt = select(WorldsSchemaDB)
        if user_id is not None:
            stmt = stmt.where(WorldsSchemaDB.user_id == user_id)

        stmt = stmt.limit(limit).offset(offset)
        
        worlds = ses.scalars(stmt).all()

    return [w for w in worlds]




@router.get("/{world_id}/miners")
def get_world_miners(
    world_id: int | None = None,
    limit:   int | None = Query(default=67, ge=0, le=67),
    offset:  int | None = Query(default=0,  ge=0)
):
    # try to get from cache
    cached_miners = r_game.json().get(f"world_{world_id}", "$.miners")
    if cached_miners:
        log_msg("get_miners cache hit")
        return [miner_from_str(m) for m_id,m in cached_miners[0].items()]
    else:
        log_msg("get_miners cache miss")

    with Session(sql_engine) as ses:
        stmt = select(MinersSchemaDB)
        stmt = stmt.where(MinersSchemaDB.world_id == world_id)

        stmt = stmt.limit(limit).offset(offset)
        
        miners = ses.scalars(stmt).all()

    # write to cache
    if r_game.json().get(f"world_{world_id}"):
        r_game.json().set(
            f"world_{world_id}",
            "$.miners",
            {}
        )
    else:
        r_game.json().set(
            f"world_{world_id}",
            "$",
            {"miners":{}}
        )

    for m in miners:
        r_game.json().set(
                f"world_{world_id}",
                f"$.miners.{m.miner_id}",
                m.to_dict()
            )


    return [m for m in miners]

@router.get("/{world_id}/planets")
def get_world_planets(
    world_id: int | None = None,
    limit:    int | None = Query(default=67, ge=0, le=67),
    offset:   int | None = Query(default=0,  ge=0)
):

    # try to get from cache
    cached_planets = r_game.json().get(f"world_{world_id}", "$.planets")
    if cached_planets:
        log_msg("get_planets cache hit")
        return [planet_from_str(p) for p_id,p in cached_planets[0].items()]
    else:
        log_msg("get_planets cache miss")


    with Session(sql_engine) as ses:
        stmt = select(PlanetsSchemaDB)
        
        res = ses.execute(
            select(
                WorldsSchemaDB.w, WorldsSchemaDB.h
            ).where(
                WorldsSchemaDB.world_id == world_id
            )
        ).all()
        if res:
            w,h = res[0]
            logger.warn(f"wid={world_id} w,h={w},{h}")
        else:
            logger.warn(f"no {world_id=} found")
        stmt = stmt.where(PlanetsSchemaDB.world_id == world_id)
            
        stmt = stmt.limit(limit).offset(offset)

        planets = ses.scalars(stmt).all()

    # write to cache
    if res:
        if r_game.json().get(f"world_{world_id}"):
            r_game.json().set(
                f"world_{world_id}",
                "$.planets",
                {}
            )
        else:
            r_game.json().set(
                f"world_{world_id}",
                "$",
                {"planets":{}}
            )

        r_game.json().set(
            f"world_{world_id}",
            "$.size",
            {"w" : w, "h" : h}
        )

        for p in planets:
            r_game.json().set(
                    f"world_{world_id}",
                    f"$.planets.{p.planet_id}",
                    p.to_dict(to_str=True)
                )

    return [p for p in planets]






@router.get("/{world_id}")
def get_world(world_id: int):

    with Session(sql_engine) as ses:
        stmt = select(
                    WorldsSchemaDB
                ).where(
                    WorldsSchemaDB.world_id == world_id
                )
        world = ses.scalar(stmt)

    if world:
        return world

    else:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"there is no world with {world_id=}"
        )





@router.post("/")
def create_world(
    is_admin: Annotated[bool, Depends(check_admin)],
    world: WorldsSchemaPD
):

    if not is_admin:
        raise OnlyForAdminsException()

    with Session(sql_engine) as ses:
        world_obj = WorldsSchemaDB(**dict(world))
        ses.add(world_obj)
        ses.commit()
        ses.refresh(world_obj)

    return world_obj


def check_world_ownership(
    world_id: int,
    session_id: str,
    is_admin: bool
):
    requester_uid = r_sessions.hget(f"ses_{session_id}", "user_id")

    with Session(sql_engine) as ses:
        stmt = select(
                    WorldsSchemaDB
                ).where(
                    WorldsSchemaDB.world_id == world_id
                )
        world = ses.scalar(stmt)
    
        if world:
            if (str(world.user_id) != requester_uid) and (not is_admin):
                raise NotOwnerException()
        else:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = f"there is no world with {world_id=}" 
            )


@router.patch("/{world_id}")
def edit_world(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    world_id: int,
    is_public: bool | None = None
):
    if is_public is None:
        return 200

    check_world_ownership(world_id, session_id, is_admin)


    with Session(sql_engine) as ses:
        stmt = text(f"""
            UPDATE worlds
            SET 
            {is_public=}
            WHERE world_id = {world_id}
        """)
        ses.execute(stmt)
        ses.commit()
    
    return 201



@router.delete("/{world_id}")
def delete_world(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    world_id: int
):

    check_world_ownership(world_id, session_id, is_admin)

    with Session(sql_engine) as ses:

        p_stmt = delete(
                    PlanetsSchemaDB
                ).where(
                    PlanetsSchemaDB.world_id == world_id
                )
        p_result = ses.execute(p_stmt)

        w_stmt = delete(
                    WorldsSchemaDB
                ).where(
                    WorldsSchemaDB.world_id == world_id
                )
        w_result = ses.execute(w_stmt)

        ses.commit()
        
    return {"log": f"deleted {w_result.rowcount} worlds and {p_result.rowcount} planets"}


