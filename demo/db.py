import time
import psycopg2
import psycopg2.pool
import psycopg2.extras
from config import DB_CONFIG

pool = None


def init_pool(minconn=1, maxconn=5, retries=3, delay=2):
    """Initialize the connection pool with retry logic."""
    global pool
    for attempt in range(1, retries + 1):
        try:
            pool = psycopg2.pool.SimpleConnectionPool(minconn, maxconn, **DB_CONFIG)
            print(f"DB pool initialized (attempt {attempt})")
            return
        except psycopg2.OperationalError as e:
            print(f"DB connection attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
    print("WARNING: Could not initialize DB pool — app will retry on first request")


def _ensure_pool():
    """Lazy-initialize pool if it wasn't ready at startup."""
    if pool is None:
        init_pool()
    if pool is None:
        raise RuntimeError("Database unavailable")


def query(sql, params=None, fetchone=False):
    _ensure_pool()
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
    _ensure_pool()
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
