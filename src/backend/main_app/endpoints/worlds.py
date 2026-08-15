from typing import Annotated

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, text

from endpoints.admin import check_admin
from endpoints.auth import get_or_create_session
from fastapi import APIRouter, HTTPException, status, Depends

from pd_models import WorldsSchemaPD
from db_models import WorldsSchemaDB, PlanetsSchemaDB

from db_connection import sql_engine, r_sessions


router = APIRouter(prefix="/api/v1/worlds")


@router.get("/")
def get_worlds(user_id: int | None = None):

    with Session(sql_engine) as ses:
        stmt = select(WorldsSchemaDB)
        if user_id is not None:
            stmt = stmt.where(WorldsSchemaDB.user_id == user_id)
        worlds = ses.scalars(stmt).all()

    return [w for w in worlds]


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
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "only for admins"
        )

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
                raise HTTPException(
                    status_code = status.HTTP_401_UNAUTHORIZED,
                    detail = "you must ba an owner or admin to do this"
                )
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


