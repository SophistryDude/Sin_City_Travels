import psycopg2
import psycopg2.pool
import psycopg2.extras
from config import DB_CONFIG

pool = None


def init_pool(minconn=1, maxconn=5):
    global pool
    pool = psycopg2.pool.SimpleConnectionPool(minconn, maxconn, **DB_CONFIG)


def query(sql, params=None, fetchone=False):
    conn = pool.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        result = cur.fetchone() if fetchone else cur.fetchall()
        cur.close()
        return result
    finally:
        pool.putconn(conn)


def query_all(queries):
    """Execute multiple queries in a single connection, return list of results."""
    conn = pool.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        results = []
        for sql, params, fetchone in queries:
            cur.execute(sql, params)
            results.append(cur.fetchone() if fetchone else cur.fetchall())
        cur.close()
        return results
    finally:
        pool.putconn(conn)
