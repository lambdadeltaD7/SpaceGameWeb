import logging
from celery import shared_task
from sqlalchemy import update, select, and_
from sqlalchemy.orm import Session 

from db_connection import sql_engine, r_game, r_sessions
from db_models import PlanetsSchemaDB, WorldsSchemaDB, UsersSchemaDB


logger = logging.getLogger(__name__)

SHIELD_COST = 2

@shared_task
def flush_redis_worlds_state():
    _, keys = r_game.scan(0, "world_*")

    with Session(sql_engine) as ses:

        for k in keys:
            
            
            world_data = r_game.json().get(k)
            r_game.delete(k)
            user_id = None

            # update planets state
            if "planets" in world_data.keys():
                for _, p in world_data["planets"].items():
                    user_id = int(p["user_id"])
                    stmt = update(
                        PlanetsSchemaDB
                    ).where(
                        PlanetsSchemaDB.planet_id == int(p["planet_id"])
                    ).values(
                        res1 = int(p["res1"]),
                        res2 = int(p["res2"]),
                        shield_on = ( p["shield_on"] == "True" )
                    )
                    ses.execute(stmt)

            r_game.delete(k)
            ses.commit()

            # update user stats
            if user_id is not None:
                stmt = select(
                        PlanetsSchemaDB.user_id
                    ).where(
                        and_(
                            PlanetsSchemaDB.user_id == user_id,
                            PlanetsSchemaDB.shield_on == True
                        )
                    )
                cnt_active_shields = len(ses.scalars(stmt).all())
        
                
                r_sessions.json().set(
                    f"user_info:{user_id}",
                    "$.cnt_active_shields",
                    cnt_active_shields
                )

            ses.commit()


@shared_task
def update_online_info():
    _, keys = r_sessions.scan(0, "ses_*")
    logged_cnt = 0
    online_cnt = 0

    for k in keys:
        user_id = r_sessions.hget(k, "user_id")
        online_cnt += 1
        if user_id != "":
            logged_cnt += 1
            
    r_sessions.json().set(
        "online_info",
        "$",
        {
            "online_cnt" : online_cnt,
            "logged_cnt" : logged_cnt
        }
    )


@shared_task
def handle_shield_res_use():
    _, keys = r_sessions.scan(0, "user_info*")

    for k in keys:
        user_info = r_sessions.json().get(k) 
        # k = user_info:{user_id} 
        user_id = int(k[k.index(":") + 1 : ])
        
        # deactivate all shields in db and clear planets cache
        if user_info["res1"] == 0:
            
            logger.info(f"uid:{user_id} out of res1")

            with Session(sql_engine) as ses:
                stmt = update(
                    PlanetsSchemaDB
                ).where(
                    PlanetsSchemaDB.user_id == user_id
                ).values(
                    shield_on = False
                )
                ses.execute(stmt)
                ses.commit()

                stmt = select(
                    WorldsSchemaDB.world_id
                ).where(
                    WorldsSchemaDB.user_id == user_id
                )
                wrld_ids = ses.scalars(stmt).all()
            
            for wid in wrld_ids:
                r_game.delete(f"world_{wid}")

            r_sessions.json().set(
                    f"user_info:{user_id}",
                    "$.cnt_active_shields",
                    0
                )

        else:
            new_res1 = max(
                0,
                user_info["res1"] - SHIELD_COST * user_info["cnt_active_shields"]
            )
            
            logger.info(f"updated res1 for uid:{user_id} from {user_info["res1"]} to {new_res1}")

            r_sessions.json().set(
                f"user_info:{user_id}",
                "$.res1",
                new_res1
            )


@shared_task
def flush_redis_users_state():
    _, keys = r_sessions.scan(0, "user_info*")

    with Session(sql_engine) as ses:
        for k in keys:
            user_info = r_sessions.json().get(k)
            user_id = int(k[k.index(":") + 1 : ])

            stmt = update(
                    UsersSchemaDB
                ).where(
                    UsersSchemaDB.user_id == user_id
                ).values(
                    res1 = user_info["res1"],
                    res2 = user_info["res2"]
                )
            ses.execute(stmt)
            ses.commit()
    