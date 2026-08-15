from fastapi import APIRouter, HTTPException, status, Depends

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, text

from typing import Annotated

from endpoints.admin import check_admin

from pd_models import UsersSchemaPD
from db_models import UsersSchemaDB

from db_connection import sql_engine, r_sessions

router = APIRouter(prefix="/api/v1/users")


@router.get("/")
def get_users():
    with Session(sql_engine) as ses:
        stmt = select(UsersSchemaDB)
        result = ses.scalars(stmt).all()
    return [p for p in result]


@router.get("/{user_id}")
def get_user(user_id: int):
    with Session(sql_engine) as ses:
        stmt = select(UsersSchemaDB).where(UsersSchemaDB.user_id==user_id)
        result = ses.scalar(stmt)
    if result:
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"there is no user with {user_id=}"
        )


@router.post("/")
def create_user(
    is_admin: Annotated[bool, Depends(check_admin)],
    user: UsersSchemaPD
):  
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "only for admins"
        )


    with Session(sql_engine) as ses:
        user_obj = UsersSchemaDB(**dict(user))
        ses.add(user_obj)
        ses.commit()
        ses.refresh(user_obj)
    return user_obj


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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "only for admins"
        )


    with Session(sql_engine) as ses:
        txt = f"""
            UPDATE users
            SET 
            {is_admin=}
            WHERE user_id = {user_id}
        """
        stmt = text(txt)
        ses.execute(stmt)
        ses.commit()
    
    return 201



@router.delete("/{user_id}")
def delete_user(
    is_admin: Annotated[bool, Depends(check_admin)],
    user_id: int
):  
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "only for admins"
        )

    with Session(sql_engine) as ses:
        stmt = delete(UsersSchemaDB).where(UsersSchemaDB.user_id==user_id)
        result = ses.execute(stmt)
        ses.commit()
    return {"log": f"deleted {result.rowcount} rows"}


