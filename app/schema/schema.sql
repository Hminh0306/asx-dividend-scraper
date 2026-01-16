PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS scrape_runs (
    run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    scraped_at  TEXT NOT NULL,
    source_url  TEXT NOT NULL,
    successful  TEXT NOT NULL,
    error_codes TEXT
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