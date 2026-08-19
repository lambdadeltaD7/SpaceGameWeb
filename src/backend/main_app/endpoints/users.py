from typing import Annotated

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, text

from endpoints.admin import check_admin
from endpoints.auth import get_or_create_session
from fastapi import APIRouter, HTTPException, status, Depends, Query

from pd_models import UsersSchemaPD
from db_models import UsersSchemaDB, WorldsSchemaDB, PlanetsSchemaDB

from db_connection import sql_engine, r_sessions


router = APIRouter(prefix="/api/v1/users")


@router.get("/")
def get_users(
    is_admin: Annotated[bool, Depends(check_admin)],
    limit:  int | None = Query(default=67, ge=0, le=67),
    offset: int | None = Query(default=0,  ge=0)
):  
    if not is_admin:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "only for admins"
        )

    with Session(sql_engine) as ses:
        stmt = select(UsersSchemaDB).limit(limit).offset(offset)
        users = ses.scalars(stmt).all()
    return [u for u in users]


@router.get("/{user_id}")
def get_user(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    user_id: int
):
    requester_uid = r_sessions.hget(f"ses_{session_id}", "user_id")

    if (not is_admin) and (requester_uid != str(user_id)):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "you can view only your own transactions"
        )

    with Session(sql_engine) as ses:
        stmt = select(
                    UsersSchemaDB
                ).where(
                    UsersSchemaDB.user_id == user_id
                )
        user = ses.scalar(stmt)

    if user:
        return user

    else:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"there is no user with {user_id=}"
        )


@router.post("/")
def create_user(
    is_admin: Annotated[bool, Depends(check_admin)],
    user: UsersSchemaPD
):  
    if not is_admin:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "only for admins"
        )

    with Session(sql_engine) as ses:
        user_obj = UsersSchemaDB(**dict(user))
        ses.add(user_obj)
        ses.commit()
        ses.refresh(user_obj)

    return user_obj


def kill_user_sessions(user_id: int) -> int:    
    sessions = r_sessions.smembers(f"user_sessions:{user_id}")

    for ses_id in sessions:
        r_sessions.delete(f"ses_{ses_id}")

    r_sessions.delete(f"user_sessions:{user_id}")

    return len(sessions)


@router.patch("/{user_id}")
def edit_user(
    check: Annotated[bool, Depends(check_admin)],
    user_id: int,
    is_admin: bool | None = None
):
    if is_admin is None:
        return 200

    if not check:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "only for admins"
        )

    with Session(sql_engine) as ses:
        stmt = text(f"""
            UPDATE users
            SET 
            {is_admin=}
            WHERE user_id = {user_id}
        """)
        ses.execute(stmt)
        ses.commit()
    
    kill_user_sessions(user_id)

    return 201


@router.delete("/{user_id}")
def delete_user(
    is_admin: Annotated[bool, Depends(check_admin)],
    user_id: int
):  
    if not is_admin:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "only for admins"
        )

    with Session(sql_engine) as ses:
        
        stmt = delete(
                    PlanetsSchemaDB
                ).where(
                    PlanetsSchemaDB.user_id == user_id
                )
        plnt_res = ses.execute(stmt)

        stmt = delete(
                    WorldsSchemaDB
                ).where(
                    WorldsSchemaDB.user_id == user_id
                )
        wrld_res = ses.execute(stmt)

        stmt = delete(
                    UsersSchemaDB
                ).where(
                    UsersSchemaDB.user_id == user_id
                )
        usr_res = ses.execute(stmt)

        ses.commit()

    cnt_ses = kill_user_sessions(user_id)

    r_sessions.remove(f"user_info:{user_id}")

    return {
        "killed sessions" : cnt_ses,
        "deleted users"   : usr_res.rowcount,
        "deleted planets" : plnt_res.rowcount,
        "deleted worlds"  : wrld_res.rowcount,
    }


