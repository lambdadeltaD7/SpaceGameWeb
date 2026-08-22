import logging

from typing import Annotated

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, text, update

from endpoints.transactions import update_user_balance
from endpoints.admin import check_admin
from endpoints.auth import get_or_create_session
from fastapi import APIRouter, HTTPException, status, Depends, Query

from pd_models import PlanetsSchemaPD
from db_models import PlanetsSchemaDB, WorldsSchemaDB

from db_connection import sql_engine, r_sessions, r_game

from exceptions import *

constants = {
    "PLANET_ATTACK_COST" : 30
}
for k,v in constants.items():
    r_game.hset("CONSTANTS", k, v)

router = APIRouter(prefix="/api/v1/planets")

logger = logging.getLogger(__name__)

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
        "user_id": int(p["user_id"]),
        "res1": int(p["res1"]),
        "res2": int(p["res2"]),
        "x": int(p["x"]),
        "y": int(p["y"]),
        "shield_on": p["shield_on"] == "True"
    }

@router.get("/")
def get_planets(
    limit:    int | None = Query(default=67, ge=0, le=67),
    offset:   int | None = Query(default=0,  ge=0)
):

    with Session(sql_engine) as ses:
        stmt = select(PlanetsSchemaDB)    
        stmt = stmt.limit(limit).offset(offset)
        planets = ses.scalars(stmt).all()

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
        raise OnlyForAdminsException()

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

        planet: PlanetsSchemaDB = ses.scalar(stmt)
    
        if planet:
            if (str(planet.user_id) != requester_uid) and (not is_admin):
                raise NotOwnerException()
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





@router.delete("/{planet_id}/attack")
def attack_planet(
    session_id: Annotated[str, Depends(get_or_create_session)],
    planet_id: int,
    world_id: int
):
    requester_uid = r_sessions.hget(f"ses_{session_id}", "user_id")

    if requester_uid == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="you must be logged in to do this"
        )

    with Session(sql_engine) as ses:
        update_user_balance(
            user_id = int(requester_uid),
            db_session = ses,
            delta_res1 = 0,
            delta_res2 = (-1) * constants["PLANET_ATTACK_COST"]
        )
        ses.commit()

    
    try:
        planet = r_game.json().get(
            f"world_{world_id}",
            f"$.planets.{planet_id}"
        )
        if planet:
            planet = planet[0]
            if planet["shield_on"]=="True":
                r_game.json().set(
                    f"world_{world_id}",
                    f"$.planets.{planet_id}.shield_on",
                    "False"
                )
                logger.warn(f"destroyed shield on pid={planet_id} in cache")
            else:
                r_game.json().delete(
                    f"world_{world_id}",
                    f"$.planets.{planet_id}"
                )
                with Session(sql_engine) as ses:
                    stmt = delete(
                                PlanetsSchemaDB
                            ).where(
                                PlanetsSchemaDB.planet_id == planet_id
                            )
                    result = ses.execute(stmt)
                    ses.commit()
                logger.warn(f"destroyed pid={planet_id} in cache")
        else:
            with Session(sql_engine) as ses:
                stmt = select(
                        PlanetsSchemaDB 
                    ).where(
                        PlanetsSchemaDB.planet_id == planet_id
                    )
                planet = ses.scalar(stmt)
                
                if planet.shield_on:
                    stmt = update(
                                PlanetsSchemaDB
                            ).where(
                                PlanetsSchemaDB.planet_id == planet_id
                            ).values(
                                shield_on = False
                            )
                    result = ses.execute(stmt)
                    ses.commit()
                else:
                    stmt = delete(
                                PlanetsSchemaDB
                            ).where(
                                PlanetsSchemaDB.planet_id == planet_id
                            )
                    result = ses.execute(stmt)
                    ses.commit()

    except Exception as ex:
        logger.error(f"err while attacking planet_id={planet.planet_id} in cache: {ex}")

    

    return {"log": "done"}


@router.delete("/{planet_id}")
def delete_planet(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    planet_id: int
):

    planet = check_planet_ownership(planet_id, session_id, is_admin)

    try:
        r_game.json().delete(
            f"world_{planet.world_id}",
            f"$.planets.{planet.planet_id}"
        )
    except Exception as ex:
        logger.error(f"err while del planet_id={planet.planet_id} from cache: {ex}")

    with Session(sql_engine) as ses:
        stmt = delete(
                    PlanetsSchemaDB
                ).where(
                    PlanetsSchemaDB.planet_id == planet_id
                )
        result = ses.execute(stmt)
        ses.commit()


    return {"log": f"deleted {result.rowcount} rows"}


