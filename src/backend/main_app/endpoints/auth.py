from typing import Annotated
import uuid

from fastapi import (
    APIRouter, Request, Response,
    HTTPException, status, Depends
)
from fastapi.responses import RedirectResponse

from db_models import UsersSchemaDB
from pd_models import *

from db_connection import r_sessions, sql_engine
from sqlalchemy.orm import Session
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/auth")

COOKIE_SESSION_ID_KEY = "my_session_id"

def create_session():
    session_id = uuid.uuid4().hex
    r_sessions.hset(
        session_id,
        mapping={
            "user_id": "",
            "username" : "",
            "is_admin" : "",
        }
    )
    return session_id


def get_or_create_session(request: Request, response: Response):
    session_id = request.cookies.get(COOKIE_SESSION_ID_KEY)

    if session_id is None:
        session_id = create_session()
        response.set_cookie(
            key=COOKIE_SESSION_ID_KEY,
            value=session_id,
            httponly=True,
            samesite="lax",
            path="/",
            secure=True
        )

    else:
        _, result = r_sessions.scan(cursor=0, match=session_id)
        if len(result) == 0:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="something is wrong with your session_id"
                )

    return session_id


@router.get("/online_info")
def online_info():
    _, keys = r_sessions.scan(0, "*")
    logged_cnt = 0
    online_cnt = 0
    for k in keys:
        user_data = r_sessions.hgetall(k)
        online_cnt += 1
        if user_data["user_id"] != "":
            logged_cnt +=1
            
    return {"online_cnt":online_cnt, "logged_cnt":logged_cnt}


@router.get("/session_info")
def session_info(session_id: Annotated[str, Depends(get_or_create_session)]):
    try:
        uname = r_sessions.hget(session_id, "username")
        uid = r_sessions.hget(session_id, "user_id")
        is_admin = r_sessions.hget(session_id, "is_admin")
        if uname == "":
            return {
                "msg":f"(anonimous session) with {session_id=}",
                "is_logged":False
            }
        else:
            return {
                "msg":f"hi, {uname}! with {session_id=})",
                "is_logged":True,
                "username": uname,
                "user_id": uid,
                "is_admin": is_admin
            } 
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=repr(ex)
        )


@router.post("/registration")
def registration(
        response: Response,
        user: UsersSchemaReg,
        old_session_id: Annotated[str, Depends(get_or_create_session)]
):

    with Session(sql_engine) as ses:
        user_obj = UsersSchemaDB(**dict(user))
        user_obj.is_admin = False
        user_obj.res1 = 100
        user_obj.res2 = 100
        ses.add(user_obj)

        try:
            ses.commit()

        except Exception:
            ses.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="this username is already taken"
            )

        ses.refresh(user_obj)


    r_sessions.delete(old_session_id)

    new_session_id = create_session()
    r_sessions.hset(new_session_id, "username", user_obj.user_name)
    r_sessions.hset(new_session_id, "user_id", user_obj.user_id)

    response.set_cookie(
        key=COOKIE_SESSION_ID_KEY,
        value=new_session_id,
        httponly=True,
        samesite="lax",
        path="/",
        secure=True
    )

    return 200


@router.post("/login")
def login(
    response: Response,
    user: UsersSchemaLog,
    old_session_id: Annotated[str, Depends(get_or_create_session)]
):
    with Session(sql_engine) as ses:
        stmt = select(UsersSchemaDB).where(UsersSchemaDB.user_name==user.user_name)
        result = ses.scalar(stmt)

    if result and (result.user_password == user.user_password):

        r_sessions.delete(old_session_id)

        new_session_id = create_session()
        r_sessions.hset(new_session_id, "username", user.user_name)
        r_sessions.hset(new_session_id, "user_id", result.user_id)
        r_sessions.hset(new_session_id, "is_admin", int(result.is_admin))

        response.set_cookie(
            key=COOKIE_SESSION_ID_KEY,
            value=new_session_id,
            httponly=True,
            samesite="lax",
            path="/",
            secure=True
        )

        return 200

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bad credentials"
        )


    
@router.get("/logout")
def logout(
    response: Response,
    old_session_id: Annotated[str, Depends(get_or_create_session)],
):
    r_sessions.delete(old_session_id)
    new_session_id = create_session()

    response.set_cookie(
        key=COOKIE_SESSION_ID_KEY,
        value=new_session_id,
        httponly=True,
        samesite="lax",
        path="/",
        secure=True
    )

    return 200
