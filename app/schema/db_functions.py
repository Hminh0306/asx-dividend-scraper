import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def migrate_db(db_path: str):
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.executescript(SCHEMA_PATH.read_text())

def init_db(db_path: str) -> Path:
    """
    Initialize SQLite database schema.
    Safe to run multiple times.
    Returns the resolved database path.
    """
    db_file = Path(db_path).expanduser().resolve()
    db_file.parent.mkdir(parents=True, exist_ok=True)

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    with sqlite3.connect(db_file) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")

        schema_sql = SCHEMA_PATH.read_text()
        conn.executescript(schema_sql)

    print(f"Database initialized at {db_file}")
    return db_file
