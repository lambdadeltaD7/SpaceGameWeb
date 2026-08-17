from typing import Annotated

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, text

from endpoints.admin import check_admin
from endpoints.auth import get_or_create_session
from fastapi import APIRouter, HTTPException, status, Depends, Query

from pd_models import PlanetsSchemaPD
from db_models import PlanetsSchemaDB, WorldsSchemaDB

from db_connection import sql_engine, r_sessions, r_game


router = APIRouter(prefix="/api/v1/planets")

def log_msg(txt):
    print('#'*64)
    print('#'*64)
    print(txt)
    print('#'*64)
    print('#'*64)


def planet_from_str(p):
    return {
        "planet_id": int(p["planet_id"]),
        "world_id": int(p["world_id"]),
        "res1": int(p["res1"]),
        "res2": int(p["res2"]),
        "x": int(p["x"]),
        "y": int(p["y"]),
        "shield_on": p["shield_on"] == "True"
    }

@router.get("/")
def get_planets(
    world_id: int | None = None,
    limit:    int | None = Query(default=67, ge=0, le=67),
    offset:   int | None = Query(default=0,  ge=0)
):

    # try to get from cache
    if world_id is not None:
        cached_planets = r_game.json().get(f"world_{world_id}", "$.planets")
        if cached_planets:
            log_msg("get_planets cache hit")
            return [planet_from_str(p) for p_id,p in cached_planets[0].items()]
        else:
            log_msg("get_planets cache miss")

    with Session(sql_engine) as ses:
        stmt = select(PlanetsSchemaDB)
        
        if world_id is not None:
            stmt = stmt.where(PlanetsSchemaDB.world_id == world_id)

        stmt = stmt.limit(limit).offset(offset)

        planets = ses.scalars(stmt).all()

    # write to cache
    if world_id is not None:
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

        for p in planets:
            r_game.json().set(
                    f"world_{world_id}",
                    f"$.planets.{p.planet_id}",
                    p.to_dict(to_str=True)
                )

    return [p for p in planets]


@router.get("/{planet_id}")
def get_planet(planet_id: int):

    with Session(sql_engine) as ses:
        stmt = select(
                    PlanetsSchemaDB
                ).where(
                    PlanetsSchemaDB.planet_id == planet_id
                )

        planet = ses.scalar(stmt)

    if planet:
        return planet

    else:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"there is no planet with {planet_id=}"
        )


@router.post("/")
def create_planet(
    is_admin: Annotated[bool, Depends(check_admin)],
    planet: PlanetsSchemaPD
):

    if not is_admin:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "only for admins"
        )

    with Session(sql_engine) as ses:
        planet_obj = PlanetsSchemaDB(**dict(planet))
        ses.add(planet_obj)
        ses.commit()
        ses.refresh(planet_obj)

    return planet_obj


def check_planet_ownership(
    planet_id: int,
    session_id: str,
    is_admin: bool
):
    requester_uid = r_sessions.hget(f"ses_{session_id}", "user_id")

    with Session(sql_engine) as ses:
        stmt = select(
                    PlanetsSchemaDB
                ).where(
                    PlanetsSchemaDB.planet_id == planet_id
                )

        planet = ses.scalar(stmt)
    
        if planet:
            world_id = planet.world_id
            stmt = select(
                        WorldsSchemaDB
                    ).where(
                        WorldsSchemaDB.world_id == world_id
                    )
            world = ses.scalar(stmt)

            if (str(world.user_id) != requester_uid) and (not is_admin):
                raise HTTPException(
                    status_code = status.HTTP_401_UNAUTHORIZED,
                    detail = "you must ba an owner or admin to do this"
                )
        else:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = f"there is no planet with {planet_id=}" 
            )

    return planet


@router.patch("/{planet_id}")
def edit_planet(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    planet_id: int,
    res1: int | None = None,
    res2: int | None = None,
    shield_on: bool | None = None
):
    if (res1 is None) and (res2 is None) and (shield_on is None):
        return 200
    
    planet = check_planet_ownership(planet_id, session_id, is_admin)

    pairs = [("shield_on",shield_on), ("res1",res1), ("res2",res2)]

    # cache hit
    if r_game.json().get(f"world_{planet.world_id}", "$.planets"):
        for k,v in pairs:
            if v is not None:
                r_game.json().set(
                    f"world_{planet.world_id}",
                    f"$.planets.{planet.planet_id}.{k}",
                    str(v)
                )

        return {"log": "updated in cache"}

    # cache miss
    with Session(sql_engine) as ses:
        for k,v in pairs:
            if v is not None:
                stmt = text(f"""
                    UPDATE planets
                    SET k={v}
                    WHERE planet_id = {planet_id}
                """)
                ses.execute(stmt)
        ses.commit()
    
    return 201


@router.delete("/{planet_id}")
def delete_planet(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    planet_id: int
):

    check_planet_ownership(planet_id, session_id, is_admin)

    with Session(sql_engine) as ses:
        stmt = delete(
                    PlanetsSchemaDB
                ).where(
                    PlanetsSchemaDB.planet_id == planet_id
                )
        result = ses.execute(stmt)
        ses.commit()

    return {"log": f"deleted {result.rowcount} rows"}


