import os

from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

load_dotenv()

database_url = os.getenv("DATABASE_URL")

pool = SimpleConnectionPool(1, 10, database_url, cursor_factory=RealDictCursor)


def get_conn():
    return pool.getconn()


def put_conn(conn):
    pool.putconn(conn)
