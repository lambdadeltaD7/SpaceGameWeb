from fastapi import APIRouter, HTTPException, status, Depends

from typing import Annotated

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, text

from endpoints.admin import check_admin

from pd_models import PlanetsSchemaPD
from db_models import PlanetsSchemaDB

from db_connection import sql_engine

router = APIRouter(prefix="/api/v1/planets")


@router.get("/")
def get_planets(world_id: int | None = None):
    with Session(sql_engine) as ses:
        stmt = select(PlanetsSchemaDB)
        if world_id is not None:
            stmt = stmt.where(PlanetsSchemaDB.world_id==world_id)
        result = ses.scalars(stmt).all()
    return [p for p in result]


@router.get("/{planet_id}")
def get_planet(planet_id: int):
    with Session(sql_engine) as ses:
        stmt = select(PlanetsSchemaDB).where(PlanetsSchemaDB.planet_id==planet_id)
        result = ses.scalar(stmt)
    if result:
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"there is no planet with {planet_id=}"
        )


@router.post("/")
def create_planet(
    check: Annotated[bool, Depends(check_admin)],
    planet: PlanetsSchemaPD
):
    with Session(sql_engine) as ses:
        planet_obj = PlanetsSchemaDB(**dict(planet))
        ses.add(planet_obj)
        ses.commit()
        ses.refresh(planet_obj)
    return planet_obj


@router.patch("/{planet_id}")
def edit_planet(
    check: Annotated[bool, Depends(check_admin)],
    planet_id: int,
    res1: int | None = None,
    res2: int | None = None,
    shield_on: bool | None = None
):
    if (res1 is None) and (res2 is None) and (shield_on is None):
        return 200
    
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
    check: Annotated[bool, Depends(check_admin)],
    planet_id: int
):
    with Session(sql_engine) as ses:
        stmt = delete(PlanetsSchemaDB).where(PlanetsSchemaDB.planet_id==planet_id)
        result = ses.execute(stmt)
        ses.commit()
    return {"log": f"deleted {result.rowcount} rows"}


