# app/

This directory contains the core application logic for the ASX dividend data pipeline.
The modules are organised by responsibility: scraping, exporting, and external integrations.

---

## `scraper_functions.py`

Responsible for **collecting and parsing dividend data** from the MarketIndex website.

### `scraper()`
- Crawls the upcoming dividends page
- Visits individual stock pages for additional details
- Cleans and normalises the data
- Returns all results as structured records (one per dividend)

This function **does not save data**. It only returns results for downstream consumers.

---

## `sheet_functions.py`

Handles **Google Sheets integration** using a service account.

### `get_worksheet()`
- Authenticates with Google
- Opens the configured spreadsheet
- Ensures the target worksheet exists

### `overwrite_sheet_with_df(df)`
- Clears existing worksheet content
- Writes the provided dataset to the sheet

### `test_sheet_access()`
- Verifies credentials and sheet access
- Confirms the worksheet is reachable and writable

---

## `export_functions.py`

Defines **output destinations** for scraped data.
This module centralises all side effects (I/O).

### `export_to_downloads(results)`
- Saves scraped data to the local filesystem

### `update_to_google_sheets(db_query)`
- Publishes data to Google Sheets

### `save_to_db(results)`
- Persists data to the database (SQLite/MySQL)

---

## `config.py`

Central configuration module.

- Loads environment variables
- Defines default paths and runtime settings
- Provides shared constants used across modules

---

## Design intent

- Scraping, exporting, and integrations are **decoupled**
- Data flows in one direction: scrape → transform → export
- Each module has a single responsibility
- Storage targets can be swapped without touching scraper logic