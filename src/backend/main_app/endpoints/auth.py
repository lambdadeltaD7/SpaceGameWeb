import uuid
from typing import Annotated

from fastapi import (
    APIRouter, Request, Response,
    HTTPException, status, Depends
)
from fastapi.responses import RedirectResponse

from pd_models import *
from db_models import UsersSchemaDB

from sqlalchemy import select
from sqlalchemy.orm import Session
from db_connection import r_sessions, sql_engine



router = APIRouter(prefix="/api/v1/auth")


COOKIE_SESSION_ID_KEY = "my_session_id"



def create_session():
    session_id = uuid.uuid4().hex

    r_sessions.hset(
        f"ses_{session_id}",
        mapping = {
            "user_id"  : "",
            "username" : "",
            "is_admin" : "",
        }
    )

    return session_id


def get_or_create_session(
    request: Request,
    response: Response
):
    session_id = request.cookies.get(COOKIE_SESSION_ID_KEY)

    if session_id is None:
        session_id = create_session()

        response.set_cookie(
            key = COOKIE_SESSION_ID_KEY,
            value = session_id,
            httponly = True,
            samesite = "lax",
            path = "/",
            secure = True
        )

    else:
        _, result = r_sessions.scan(cursor=0, match=f"ses_{session_id}")

        if len(result) == 0:
            raise HTTPException(
                status_code = status.HTTP_406_NOT_ACCEPTABLE,
                detail = "something is wrong with your session_id"
                )

    return session_id


@router.get("/online_info")
def online_info():
    _, keys = r_sessions.scan(0, "ses_*")
    logged_cnt = 0
    online_cnt = 0

    for k in keys:
        user_data = r_sessions.hgetall(k)
        online_cnt += 1
        if user_data["user_id"] != "":
            logged_cnt += 1
            
    return {
        "online_cnt" : online_cnt,
        "logged_cnt" : logged_cnt
    }


@router.get("/session_info")
def session_info(session_id: Annotated[str, Depends(get_or_create_session)]):
    try:
        user_name = r_sessions.hget(f"ses_{session_id}", "username")
        user_id = r_sessions.hget(f"ses_{session_id}", "user_id")
        is_admin = r_sessions.hget(f"ses_{session_id}", "is_admin")

        if user_name == "":
            return {
                "msg"       : f"(anonimous session) with {session_id=}",
                "is_logged" : False
            }

        else:
            return {
                "msg"       : f"hi, {user_name}! with {session_id=}",
                "is_logged" : True,
                "username"  : user_name,
                "user_id"   : user_id,
                "is_admin"  : is_admin
            } 

    except Exception as ex:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = repr(ex)
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
                status_code = status.HTTP_409_CONFLICT,
                detail = "this username is already taken"
            )

        ses.refresh(user_obj)


    r_sessions.delete(f"ses_{old_session_id}")

    new_session_id = create_session()
    r_sessions.hset(f"ses_{new_session_id}", "username", user_obj.user_name)
    r_sessions.hset(f"ses_{new_session_id}", "user_id", user_obj.user_id)

    r_sessions.rpush(f"user_{user_obj.user_id}", new_session_id)

    response.set_cookie(
        key = COOKIE_SESSION_ID_KEY,
        value = new_session_id,
        httponly = True,
        samesite = "lax",
        path = "/",
        secure = True
    )

    return 200


@router.post("/login")
def login(
    response: Response,
    user: UsersSchemaLog,
    old_session_id: Annotated[str, Depends(get_or_create_session)]
):
    with Session(sql_engine) as ses:
        stmt = select(
                    UsersSchemaDB
                ).where(
                    UsersSchemaDB.user_name == user.user_name
                )
        user_obj = ses.scalar(stmt)

    if user_obj and (user_obj.user_password == user.user_password):

        r_sessions.delete(f"ses_{old_session_id}")

        new_session_id = create_session()
        r_sessions.hset(f"ses_{new_session_id}", "username", user.user_name)
        r_sessions.hset(f"ses_{new_session_id}", "user_id", user_obj.user_id)
        r_sessions.hset(f"ses_{new_session_id}", "is_admin", int(user_obj.is_admin))

        r_sessions.rpush(f"user_{user_obj.user_id}", new_session_id)

        response.set_cookie(
            key = COOKIE_SESSION_ID_KEY,
            value = new_session_id,
            httponly = True,
            samesite = "lax",
            path = "/",
            secure = True
        )

        return 200

    else:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "bad credentials"
        )


@router.get("/logout")
def logout(
    response: Response,
    old_session_id: Annotated[str, Depends(get_or_create_session)],
):

    user_info = r_sessions.hgetall(f"ses_{old_session_id}")

    r_sessions.lrem(f"user_{user_info["user_id"]}", 0, old_session_id)
    r_sessions.delete(f"ses_{old_session_id}")
    
    new_session_id = create_session()

    response.set_cookie(
        key = COOKIE_SESSION_ID_KEY,
        value = new_session_id,
        httponly = True,
        samesite = "lax",
        path = "/",
        secure = True
    )

    return 200
