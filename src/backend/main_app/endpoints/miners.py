from typing import Annotated

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, text

from endpoints.admin import check_admin
from endpoints.auth import get_or_create_session
from fastapi import APIRouter, HTTPException, status, Depends, Query

from pd_models import MinersSchemaPD
from db_models import MinersSchemaDB

from db_connection import sql_engine, r_sessions, r_game


router = APIRouter(prefix="/api/v1/miners")

def log_msg(txt):
    print('#'*64)
    print('#'*64)
    print(txt)
    print('#'*64)
    print('#'*64)


def miner_from_str(m):
    return {
        "miner_id": int(m["miner_id"]),
        "world_id": int(m["world_id"]),
        "user_id": int(m["user_id"]),
        "x": int(m["x"]),
        "y": int(m["y"]),
    }

@router.get("/")
def get_miners(
    world_id: int | None = None,
    limit:   int | None = Query(default=67, ge=0, le=67),
    offset:  int | None = Query(default=0,  ge=0)
):
    # try to get from cache
    if world_id is not None:
        cached_miners = r_game.json().get(f"world_{world_id}", "$.miners")
        if cached_miners:
            log_msg("get_miners cache hit")
            return [miner_from_str(m) for m_id,m in cached_miners[0].items()]
        else:
            log_msg("get_miners cache miss")

    with Session(sql_engine) as ses:
        stmt = select(MinersSchemaDB)
        if world_id is not None:
            stmt = stmt.where(MinersSchemaDB.world_id == world_id)

        stmt = stmt.limit(limit).offset(offset)
        
        miners = ses.scalars(stmt).all()

    # write to cache
    if world_id is not None:
        if r_game.json().get(f"world_{world_id}"):
            r_game.json().set(
                f"world_{world_id}",
                "$.miners",
                {}
            )
        else:
            r_game.json().set(
                f"world_{world_id}",
                "$",
                {"miners":{}}
            )

        for m in miners:
            r_game.json().set(
                    f"world_{world_id}",
                    f"$.miners.{m.miner_id}",
                    m.to_dict()
                )


    return [m for m in miners]


@router.get("/{miner_id}")
def get_miner(miner_id: int):

    with Session(sql_engine) as ses:
        stmt = select(
                    MinersSchemaDB
                ).where(
                    MinersSchemaDB.miner_id == miner_id
                )
        miner = ses.scalar(stmt)

    if miner:
        return miner

    else:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"there is no miner with {miner_id=}"
        )


@router.post("/")
def create_miner(
    is_admin: Annotated[bool, Depends(check_admin)],
    miner: MinersSchemaPD
):

    if not is_admin:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "only for admins"
        )

    with Session(sql_engine) as ses:
        miner_obj = MinersSchemaDB(**dict(miner))
        ses.add(miner_obj)
        ses.commit()
        ses.refresh(miner_obj)

    return miner_obj


def check_miner_ownership(
    miner_id: int,
    session_id: str,
    is_admin: bool
):
    requester_uid = r_sessions.hget(f"ses_{session_id}", "user_id")

    with Session(sql_engine) as ses:
        stmt = select(
                    MinersSchemaDB
                ).where(
                    MinersSchemaDB.miner_id == miner_id
                )
        miner = ses.scalar(stmt)
    
        if miner:
            if (str(miner.user_id) != requester_uid) and (not is_admin):
                raise HTTPException(
                    status_code = status.HTTP_401_UNAUTHORIZED,
                    detail = "you must be an owner or admin to do this"
                )
        else:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = f"there is no miner with {miner_id=}" 
            )


@router.delete("/{miner_id}")
def delete_miner(
    is_admin: Annotated[bool, Depends(check_admin)],
    session_id: Annotated[str, Depends(get_or_create_session)],
    miner_id: int
):

    check_miner_ownership(miner_id, session_id, is_admin)

    with Session(sql_engine) as ses:
        m_stmt = delete(
                    MinersSchemaDB
                ).where(
                    MinersSchemaDB.miner_id == miner_id
                )
        m_result = ses.execute(m_stmt)

        ses.commit()
        
    return {"log": f"deleted {m_result.rowcount} miners"}


