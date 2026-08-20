from celery import Celery

from tasks import *

app = Celery('celery_app_title', broker='redis://redis_cluster:6379/3',)


FLUSH_REDIS_WORLDS_STATE_INTERVAL = 10.0
FLUSH_REDIS_USERS_STATE_INTERVAL = 10.0
UPDATE_ONLINE_INFO_INTERVAL = 5.0
HANDLE_SHIELD_RES_USE_INTERVAL = 5.0
HANDLE_MINER_RES_EXTRACTION_INTERVAL = 5.0

@app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):

    sender.add_periodic_task(
        FLUSH_REDIS_WORLDS_STATE_INTERVAL,
        flush_redis_worlds_state,
        name='flush_redis_worlds_state'
    )

    sender.add_periodic_task(
        FLUSH_REDIS_USERS_STATE_INTERVAL,
        flush_redis_users_state,
        name='flush_redis_users_state'
    )

    sender.add_periodic_task(
        UPDATE_ONLINE_INFO_INTERVAL,
        update_online_info,
        name='update_online_info'
    )

    sender.add_periodic_task(
        HANDLE_SHIELD_RES_USE_INTERVAL,
        handle_shield_res_use,
        name='handle_shield_res_use'
    )

    sender.add_periodic_task(
        HANDLE_MINER_RES_EXTRACTION_INTERVAL,
        handle_miner_res_extraction,
        name='handle_miner_res_extraction'
    )


    





