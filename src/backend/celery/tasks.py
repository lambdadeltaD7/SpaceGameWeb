import logging
from celery import shared_task
from sqlalchemy import update 
from sqlalchemy.orm import Session 

from db_connection import sql_engine, r_game, r_sessions
from db_models import PlanetsSchemaDB, WorldsSchemaDB


logger = logging.getLogger(__name__)


@shared_task
def flush_redis_worlds_state():
    _, keys = r_game.scan(0, "world_*")
    
    logger.info(f"{keys=}")

    with Session(sql_engine) as ses:

        for k in keys:

            logger.info(f"for key {k}")
            world_data = r_game.json().get(k)
            r_game.delete(k)
            logger.info(f"{world_data=}")

            if "planets" in world_data.keys():
                logger.info("we have some planets")
                for _, p in world_data["planets"].items():
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


@shared_task
def update_online_info():
    _, keys = r_sessions.scan(0, "ses_*")
    logged_cnt = 0
    online_cnt = 0

    for k in keys:
        user_data = r_sessions.hgetall(k)
        online_cnt += 1
        if user_data["user_id"] != "":
            logged_cnt += 1
            
    r_sessions.json().set(
        "online_info",
        "$",
        {
            "online_cnt" : online_cnt,
            "logged_cnt" : logged_cnt
        }
    )