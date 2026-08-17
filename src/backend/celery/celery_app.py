from celery import Celery

from tasks import flush_redis_worlds_state, update_online_info

app = Celery('celery_app_title', broker='redis://redis_cluster:6379/3',)


FLUSH_REDIS_WORLD_STATE_INTERVAL = 10.0
UPDATE_ONLINE_INFO_INTERVAL = 5.0

@app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):

    sender.add_periodic_task(
        FLUSH_REDIS_WORLD_STATE_INTERVAL,
        flush_redis_worlds_state,
        name='flush_redis_worlds_state'
    )

    sender.add_periodic_task(
        UPDATE_ONLINE_INFO_INTERVAL,
        update_online_info,
        name='update_online_info'
    )




