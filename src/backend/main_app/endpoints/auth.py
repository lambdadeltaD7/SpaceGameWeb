import uuid
from typing import Annotated
import bcrypt

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
            "user_id"  : ""
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

        # mb suggest to clear the cookies?
        if len(result) == 0:
            raise HTTPException(
                status_code = status.HTTP_406_NOT_ACCEPTABLE,
                detail = "something is wrong with your session_id"
                )

    return session_id


@router.get("/online_info")
def online_info():

    cached_online_info = r_sessions.json().get("online_info")
    if cached_online_info:
        return {k : int(v) for k,v in cached_online_info.items()}

    _, keys = r_sessions.scan(0, "ses_*")
    logged_cnt = 0
    online_cnt = 0

    for k in keys:
        user_id = r_sessions.hget(k, "user_id")
        online_cnt += 1
        if user_id != "":
            logged_cnt += 1
            
    return {
        "online_cnt" : online_cnt,
        "logged_cnt" : logged_cnt
    }


@router.get("/session_info")
def session_info(session_id: Annotated[str, Depends(get_or_create_session)]):
    try:        
        user_id = r_sessions.hget(f"ses_{session_id}", "user_id")

        if user_id == "":
            return {
                "msg"       : f"(anonimous session) with {session_id=}",
                "is_logged" : False
            }

        else:
            user_info = r_sessions.json().get(f"user_info:{user_id}")
            return {
                "msg"       : f"hi, {user_info["username"]}! with {session_id=}",
                "is_logged" : True,
                "username"  : user_info["username"],
                "user_id"   : user_id,
                "is_admin"  : user_info["is_admin"],
                "res1"      : int(user_info["res1"]), 
                "res2"      : int(user_info["res2"])
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
        user_db_obj = UsersSchemaDB(**dict(user))
        ses.add(user_db_obj)

        try:
            ses.commit()

        except Exception:
            ses.rollback()
            raise HTTPException(
                status_code = status.HTTP_409_CONFLICT,
                detail = "this username is already taken"
            )

        ses.refresh(user_db_obj)

    r_sessions.delete(f"ses_{old_session_id}")

    new_session_id = create_session()
    r_sessions.hset(f"ses_{new_session_id}", "user_id", user_db_obj.user_id)

    r_sessions.json().set(
        f"user_info:{user_db_obj.user_id}",
        "$",
        {
            "username" :  user_db_obj.user_name,
            "is_admin" :  int(user_db_obj.is_admin),
            "res1"     :  user_db_obj.res1, 
            "res2"     :  user_db_obj.res2,
        }
    )

    r_sessions.sadd(f"user_sessions:{user_db_obj.user_id}", new_session_id)

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
        user_db_obj = ses.scalar(stmt)


    if user_db_obj and bcrypt.checkpw(
                                user.user_password.encode("utf-8"),
                                user_db_obj.pass_salted_hashed.encode("utf-8")
                            ):

        r_sessions.delete(f"ses_{old_session_id}")

        new_session_id = create_session()
        r_sessions.hset(f"ses_{new_session_id}", "user_id", user_db_obj.user_id)

        r_sessions.json().set(
            f"user_info:{user_db_obj.user_id}",
            "$",
            {
                "username" :  user_db_obj.user_name,
                "is_admin" :  int(user_db_obj.is_admin),
                "res1"     :  user_db_obj.res1, 
                "res2"     :  user_db_obj.res2,
            }
        )

        r_sessions.sadd(f"user_sessions:{user_db_obj.user_id}", new_session_id)

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

    user_id = r_sessions.hget(f"ses_{old_session_id}", "user_id")

    r_sessions.srem(f"user_sessions:{user_db_obj.user_id}", old_session_id)

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
