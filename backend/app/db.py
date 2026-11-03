import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import settings


def connect(path: str | None = None) -> sqlite3.Connection:
    # Per-request connection; FastAPI may run setup/teardown of sync deps on different threads.
    conn = sqlite3.connect(path or settings.db_path, timeout=5, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection):
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def migrate(conn: sqlite3.Connection, migrations_dir: Path | None = None) -> list[str]:
    """Apply NNNN_*.sql files once each, in order. Repeatable."""
    mdir = migrations_dir or settings.migrations_dir
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
    applied = []
    for f in sorted(mdir.glob("[0-9][0-9][0-9][0-9]_*.sql")):
        if f.stem in done:
            continue
        sql = f.read_text(encoding="utf-8")
        conn.executescript("BEGIN;\n" + sql + f"\nINSERT INTO schema_migrations(version) VALUES ('{f.stem}');\nCOMMIT;")
        applied.append(f.stem)
    return applied


def get_db():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
