import sqlite3
from pathlib import Path


def init_db(db_path: str) -> Path:
    """
    Initialize SQLite database schema.
    Safe to run multiple times.
    Returns the resolved database path.
    """
    db_file = Path(db_path).expanduser().resolve()
    db_file.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_file) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")

        conn.executescript("""
        CREATE TABLE IF NOT EXISTS scrape_runs (
            run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            scraped_at  TEXT NOT NULL,
            source_url  TEXT NOT NULL,
            notes       TEXT
        );

        CREATE TABLE IF NOT EXISTS dividends (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id        INTEGER NOT NULL,

            code          TEXT NOT NULL,
            company       TEXT,

            ex_date       TEXT,
            pay_date      TEXT,

            amount        REAL,
            franking      REAL,
            yield         REAL,

            price         REAL,
            volume_4w     REAL,
            total_value   REAL,

            scraped_at    TEXT NOT NULL,

            FOREIGN KEY (run_id) REFERENCES scrape_runs(run_id)
        );

        CREATE INDEX IF NOT EXISTS idx_div_code        ON dividends(code);
        CREATE INDEX IF NOT EXISTS idx_div_ex_date     ON dividends(ex_date);
        CREATE INDEX IF NOT EXISTS idx_div_scraped_at  ON dividends(scraped_at);
        CREATE INDEX IF NOT EXISTS idx_div_run_id      ON dividends(run_id);
        """)

    print(f"Database initialized at {db_file}")
    return db_file