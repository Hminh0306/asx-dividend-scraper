# Database Schema & Migrations

This directory defines and manages the SQLite database schema used by the ASX Dividend Scraper.

The database is designed to:
- store **historical dividend data**
- track **each scraper execution**
- support **daily writes and frequent reads**
- allow **safe schema evolution over time**

---

## Directory Structure
app/schema
- __init__.py: regular package Python enforcer
- schema.sql: source-of-truth schema
- db_functions.py: database helper (init, migrates, queries)
- README.md: this documentation

## Schema Design

The database consists of two core tables.

### `scrape_runs`
Stores metadata for each scraper execution.

Purpose:
- audit scraper runs
- track failures
- link dividend records to the run that produced them

Each row represents **one execution of the scraper**.

---

### `dividends`
Stores the dividend data collected by the scraper.

Purpose:
- historical dividend storage
- querying by code, date, or run
- downstream exports (Google Sheets, analytics)

Each row represents **one dividend record**, linked to a specific scrape run.

- scrapte_at is saved in ISO8601 timestamp
---

## Schema `schema.sql`

This file is the **single source of truth** for the database structure.

- All schema changes must be made here
- Python code never embeds SQL schema directly
- This enables safe reinitialisation and migration

---

## Initialising the Database

To initialise a fresh database:

### Option 1: via Python (recommended)

```python
from app.schema.db_functions import init_db

init_db("database/asx_dividends.db")
```

### Option 2: via SQLite CLI
```
sqlite3 database/asx_dividends.db < app/schema/schema.sql
```

## Schema Migration
*For later migration, only change schema.sql and run migrate function. The limitation is that only adding column is possible due to SQLite limitations in dropping, type changes and renaming columns*

- This project uses a versioned schema migration approach.

- How it works:

+ The database stores the current schema version

+ schema.sql declares the latest version

+ Python compares versions and applies upgrades when needed

### Migration Implementation
How to migrate after a schema change
1. Update schema.sql
2. Increment LATEST_SCHEMA_VERSIOn
3. Add migration logic in migrate_schema
4. Run
```
    init_db("database/asx_dividends.db")
```