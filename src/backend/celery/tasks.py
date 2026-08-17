from celery import Celery
from db_connection import sql_engine, r_game
from sqlalchemy import update 
from sqlalchemy.orm import Session 
from db_models import PlanetsSchemaDB, WorldsSchemaDB


import logging

# Настраиваем логирование
logger = logging.getLogger(__name__)

app = Celery('tasks', broker='redis://redis_cluster:6379/3',)

FLUSH_REDIS_WORLD_STATE_INTERVAL = 30.0

@app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    # sender.add_periodic_task(3.0, test.s('hello1'), name='print every 3')

    sender.add_periodic_task(
        FLUSH_REDIS_WORLD_STATE_INTERVAL,
        flush_redis_worlds_state,
        name='flush_redis_worlds_state'
    )


@app.task
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
                logger.info("we have planets")
                for _, p in world_data["planets"][0].items():
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

            if "is_public" in world_data.keys():
                logger.info("we have is_public")
                stmt = update(
                        WorldsSchemaDB
                    ).where(
                        # k = f"world_{world_id}"
                        WorldsSchemaDB.world_id == int(k[k.index("_") + 1 : ])
                    ).values(
                        is_public = ( world_data["is_public"] == "True" )
                    )
                ses.execute(stmt)

            r_game.delete(k)
            ses.commit()


@app.task
def test(arg):
    print(arg)

