"""PostgreSQL connection helpers."""

from collections.abc import Generator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.config import get_settings


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """
    Yield a database connection with dict rows.

    Yields:
        Open psycopg connection; closed on exit.

    Raises:
        psycopg.OperationalError: If the database is unreachable.
    """
    settings = get_settings()
    conn = psycopg.connect(settings.dsn, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
