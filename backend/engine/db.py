import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Any, Dict, List, Optional

# PostgreSQL database connection
_conn: Optional[psycopg2.extensions.connection] = None

# Database configuration from environment variables
_DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
_DB_PORT = os.getenv("POSTGRES_PORT", "5432")
_DB_NAME = os.getenv("POSTGRES_DB", "flowart")
_DB_USER = os.getenv("POSTGRES_USER", "postgres")
_DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")


def _get_conn() -> psycopg2.extensions.connection:
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(
            host=_DB_HOST,
            port=_DB_PORT,
            dbname=_DB_NAME,
            user=_DB_USER,
            password=_DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        _conn.autocommit = False
    return _conn


def init_db() -> None:
    """Initialize database schema if it does not exist."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS flows (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT,
            workflow TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_flows_user ON flows(user_id)
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.close()
    _ensure_default_user(conn)
    conn.commit()


def db_save_flow(user_id: str, name: Optional[str], workflow: Dict[str, Any]) -> int:
    """Insert a new flow and return its integer ID."""
    conn = _get_conn()
    cur = conn.cursor()
    wf_text = json.dumps(workflow, ensure_ascii=False)
    cur.execute(
        "INSERT INTO flows (user_id, name, workflow) VALUES (%s, %s, %s) RETURNING id",
        (user_id, name, wf_text),
    )
    flow_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    return int(flow_id)


def db_list_flows(user_id: str) -> List[Dict[str, Any]]:
    """List flows for a given user_id (without heavy workflow payload)."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, name, created_at, updated_at FROM flows WHERE user_id = %s ORDER BY id DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def db_get_flow(flow_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a flow by its ID. Returns None if not found."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, name, workflow, created_at, updated_at FROM flows WHERE id = %s",
        (flow_id,),
    )
    row = cur.fetchone()
    cur.close()
    if row is None:
        return None
    out = dict(row)
    try:
        out["workflow"] = json.loads(out.get("workflow") or "{}")
    except Exception:
        out["workflow"] = {}
    return out


def _ensure_default_user(conn: psycopg2.extensions.connection) -> None:
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", ("test@gmail.com",))
    row = cur.fetchone()
    if row is None:
        cur.execute(
            "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)",
            ("test@gmail.com", "123456789", "user"),
        )
        conn.commit()
    cur.close()


def db_get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, password, role, created_at FROM users WHERE email = %s",
        (email,),
    )
    row = cur.fetchone()
    cur.close()
    if row is None:
        return None
    return dict(row)


def db_create_user(email: str, password: str, role: str = "user") -> int:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password, role) VALUES (%s, %s, %s) RETURNING id",
        (email, password, role),
    )
    user_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    return int(user_id)
