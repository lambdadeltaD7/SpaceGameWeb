import redis
from sqlalchemy import create_engine
import os

r = redis.Redis(host="redis_cluster", port="6379", decode_responses=True, db=0)
r_sessions = redis.Redis(host="redis_cluster", port="6379", decode_responses=True, db=1)

POSTGRES_USER=os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD=os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DB=os.environ.get("POSTGRES_DB")

sql_engine = create_engine((f"postgresql+psycopg://"
                            f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
                            f"@postgres_cluster:5432/{POSTGRES_DB}")
                          )

            