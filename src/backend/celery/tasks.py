import logging
from celery import shared_task
from sqlalchemy import update, select, and_
from sqlalchemy.orm import Session 

from db_connection import sql_engine, r_game, r_sessions
from db_models import PlanetsSchemaDB, WorldsSchemaDB, UsersSchemaDB


logger = logging.getLogger(__name__)

constants = {
    "SHIELD_COST" : 2,
    "MINER_RADIUS" : 3,
    "MINER_RES1_EXTRACTION_SPEED" : 3,
    "MINER_RES2_EXTRACTION_SPEED" : 4
}
for k,v in constants.items():
    r_game.hset("CONSTANTS", k, v)



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
                user_info["res1"] - constants["SHIELD_COST"] * user_info["cnt_active_shields"]
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


def get_neighb(x, y, r, w, h):
    res = []
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if (0 <= x + dx < w) and (0 <= y + dy < h):
                res.append( (x + dx, y + dy) )
    return res

@shared_task
def handle_miner_res_extraction():
    # exctracting only when world is in cache

    _, world_keys = r_game.scan(0, "world_*")

    users_updates = dict()

    for wk in world_keys:
        
        world_id = int(wk[ wk.index("_") + 1 : ])

        logger.warn(f"processing {world_id=}...\n")

        planets = r_game.json().get(f"world_{world_id}", "$.planets")
        miners = r_game.json().get(f"world_{world_id}", "$.miners")
        size = r_game.json().get(f"world_{world_id}", "$.size")

        if (not planets) or (not miners) or (not size):
            logger.warn(f"don't have enough info for {world_id=}")
            continue
        
        planets = planets[0]
        miners = miners[0]
        size = size[0]
    
        planets_map = dict()
        for p in planets.values():
            planets_map[ (p["x"], p["y"]) ] = p
        
        for m in miners.values():
            logger.warn(f"processing miner_id={m["miner_id"]}...\n")
            neighb = get_neighb(m["x"], m["y"], constants["MINER_RADIUS"], size["w"], size["h"])
            for (x,y) in neighb:
                if (x,y) in planets_map:
                    p = planets_map[(x,y)]

                    old_r1, old_r2 = p["res1"], p["res2"]
                    new_r1 = max(0, old_r1 - constants["MINER_RES1_EXTRACTION_SPEED"])
                    new_r2 = max(0, old_r2 - constants["MINER_RES2_EXTRACTION_SPEED"])
                    got_r1 = old_r1 - new_r1 
                    got_r2 = old_r2 - new_r2 

                    r_game.json().set(
                        f"world_{world_id}",
                        f"$.planets.{p["planet_id"]}.res1",
                        new_r1
                    )
                    r_game.json().set(
                        f"world_{world_id}",
                        f"$.planets.{p["planet_id"]}.res2",
                        new_r2
                    )

                    if p["user_id"] not in users_updates:
                        users_updates[p["user_id"]] = {"res1" : 0, "res2" : 0}
                    users_updates[p["user_id"]]["res1"] += got_r1
                    users_updates[p["user_id"]]["res2"] += got_r2
                    
                    logger.warn(
                        (f"for miner_id={m["miner_id"]}({m["x"]},{m["y"]})\n"
                        f"found planet_id={p["planet_id"]}({p["x"]},{p["y"]})\n"
                        f"res1: ({old_r1}) -> ({new_r1})\n"
                        f"res2: ({old_r2}) -> ({new_r2})\n\n")
                    )

                    if new_r1 == 0:
                        logger.warn(f"planet_id={p["planet_id"]} out of res1")
                    if new_r2 == 0:
                        logger.warn(f"planet_id={p["planet_id"]} out of res2")


    for uid in users_updates:
        user_info = r_sessions.json().get(
            f"user_info:{uid}"
        )       

        if user_info:
            r_sessions.json().set(
                f"user_info:{uid}",
                "$.res1",
                user_info["res1"] + users_updates[uid]["res1"]
            )

            r_sessions.json().set(
                f"user_info:{uid}",
                "$.res2",
                user_info["res2"] + users_updates[uid]["res2"]
            )

            logger.warn(
                (f"incremented in cache for {uid=}\n"
                f"res1 += {users_updates[uid]["res1"]}\n"
                f"res2 += {users_updates[uid]["res2"]}\n\n")
            )

        else:
            with Session(sql_engine) as ses:
                stmt = update(
                    UsersSchemaDB
                ).where(
                    UsersSchemaDB.user_id == uid
                ).values(
                    res1 = UsersSchemaDB.res1 + users_updates[uid]["res1"],
                    res2 = UsersSchemaDB.res2 + users_updates[uid]["res2"]
                )
                ses.execute(stmt)
                ses.commit()

            logger.warn(
                (f"incremented in db for {uid=}\n"
                f"res1 += {users_updates[uid]["res1"]}\n"
                f"res2 += {users_updates[uid]["res2"]}\n\n")
            )