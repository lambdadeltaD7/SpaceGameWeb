from typing import Annotated

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, text

from endpoints.admin import check_admin
from endpoints.auth import get_or_create_session
from fastapi import APIRouter, HTTPException, status, Depends

from pd_models import PlanetsSchemaPD
from db_models import PlanetsSchemaDB, WorldsSchemaDB

from db_connection import sql_engine, r_sessions


router = APIRouter(prefix="/api/v1/planets")


@router.get("/")
def get_planets(world_id: int | None = None):

    with Session(sql_engine) as ses:

        stmt = select(PlanetsSchemaDB)
        
        if world_id is not None:
            stmt = stmt.where(PlanetsSchemaDB.world_id == world_id)

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
    
    check_planet_ownership(planet_id, session_id, is_admin)

    changes = []

    if res1 is not None:
        changes.append(f"{res1=}\n")
    if res2 is not None:
        changes.append(f"{res2=}\n")
    if shield_on is not None:
        changes.append(f"{shield_on=}\n")

    with Session(sql_engine) as ses:
        for ch in changes:
            stmt = text(f"""
                UPDATE planets
                SET 
                {ch}
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


