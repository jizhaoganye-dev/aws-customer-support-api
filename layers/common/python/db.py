"""
Database connection pool for AWS Lambda + RDS PostgreSQL.
Uses connection reuse across warm Lambda invocations.
"""
import os
import json
import logging
from contextlib import contextmanager
from typing import Any, Generator, Optional

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Connection pool (reused across warm invocations)
_connection_pool: Optional[pool.SimpleConnectionPool] = None


def _get_db_config() -> dict:
    """Extract DB configuration from environment variables."""
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "dbname": os.environ.get("DB_NAME", "customer_support"),
        "user": os.environ.get("DB_USER", "csadmin"),
        "password": os.environ.get("DB_PASSWORD", ""),
    }


def get_pool() -> pool.SimpleConnectionPool:
    """Get or create the connection pool (singleton per Lambda container)."""
    global _connection_pool
    if _connection_pool is None or _connection_pool.closed:
        config = _get_db_config()
        logger.info("Creating new connection pool to %s:%s/%s", config["host"], config["port"], config["dbname"])
        _connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            **config,
        )
    return _connection_pool


@contextmanager
def get_connection() -> Generator:
    """Context manager that provides a DB connection from the pool."""
    conn = None
    try:
        conn = get_pool().getconn()
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            get_pool().putconn(conn)


@contextmanager
def get_cursor(cursor_factory=RealDictCursor) -> Generator:
    """Context manager that provides a cursor from a pooled connection."""
    with get_connection() as conn:
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
        finally:
            cursor.close()


def execute_query(query: str, params: tuple = None) -> list[dict]:
    """Execute a SELECT query and return results as list of dicts."""
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def execute_insert(query: str, params: tuple = None) -> Optional[dict]:
    """Execute an INSERT/UPDATE query with RETURNING clause."""
    with get_cursor() as cur:
        cur.execute(query, params)
        try:
            return cur.fetchone()
        except psycopg2.ProgrammingError:
            return None


def check_health() -> dict:
    """Check database connectivity and return status."""
    try:
        result = execute_query("SELECT 1 AS ok, NOW() AS server_time")
        return {
            "status": "healthy",
            "server_time": str(result[0]["server_time"]) if result else None,
        }
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return {
            "status": "unhealthy",
            "error": str(e),
        }
