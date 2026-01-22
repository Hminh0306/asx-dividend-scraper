from __future__ import annotations

import os
from datetime import datetime, date
from typing import Any, Iterable, Optional
from dotenv import load_dotenv
import pandas as pd

from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.getenv("BQ_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID")
TABLE_NAME = os.getenv("BQ_TABLE_ID")

client = bigquery.Client(project=PROJECT_ID)

table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_NAME}"

# ---------- Helpers ----------

def _to_date(value: Any) -> Optional[date]:
    """
    Accepts:
      - "YYYY-MM-DD" string
      - datetime/date
      - "N/A"/None/"" -> None
    Returns: datetime.date or None
    """
    if value in (None, "", "N/A"):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _to_timestamp(value: Any) -> Optional[str]:
    """
    BigQuery JSON insert accepts RFC3339 string.
    Accepts:
      - datetime -> isoformat (UTC if naive)
      - string already iso-ish -> return as-is
      - None -> None
    """
    if value in (None, "", "N/A"):
        return None
    if isinstance(value, datetime):
        # If naive, assume UTC
        if value.tzinfo is None:
            return value.replace(tzinfo=None).isoformat() + "Z"
        return value.isoformat()
    if isinstance(value, str):
        return value
    # Firestore Timestamp has .isoformat often
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    return str(value)


def _to_float(value: Any) -> Optional[float]:
    if value in (None, "", "N/A"):
        return None
    try:
        return float(value)
    except Exception:
        # handle comma decimals "1,23" and thousands "1,234.56"
        if isinstance(value, str):
            s = value.strip()
            # if looks like European "1,23" and not "1,234.56"
            if s.count(",") == 1 and s.count(".") == 0:
                s = s.replace(",", ".")
            else:
                s = s.replace(",", "")
            try:
                return float(s)
            except Exception:
                return None
        return None


def _to_int(value: Any) -> Optional[int]:
    if value in (None, "", "N/A"):
        return None
    try:
        return int(float(value))
    except Exception:
        if isinstance(value, str):
            s = value.strip().replace(",", "")
            try:
                return int(float(s))
            except Exception:
                return None
        return None


def _normalize_row(item: dict) -> dict:
    crawl_date = _to_date(item.get("Crawl Date"))
    ex_date = _to_date(item.get("Ex Date"))
    pay_date = _to_date(item.get("Pay Date"))
    code = item.get("Code")

    return {
        "crawl_date": crawl_date.isoformat() if crawl_date else None,
        "code": str(code) if code is not None else None,
        "company": item.get("Company"),
        "ex_date": ex_date.isoformat() if ex_date else None,
        "pay_date": pay_date.isoformat() if pay_date else None,
        "amount": _to_float(item.get("Amount")),
        "franking": _to_float(item.get("Franking")),
        "yield": _to_float(item.get("Yield")),
        "price": _to_float(item.get("Price")),
        "volume_4w": _to_int(item.get("4W Volume")),
        "total_value": _to_float(item.get("Total Value")),
        "last_updated": _to_timestamp(item.get("last_updated")),
    }


# ---------- Main writer ----------
def write_to_big_query(
        data_from_scraper,
        *,
        batch_size: int=500,
    ):
    """
    Inserts rows into BigQuery using insert_rows_json.
    - items: list of scraper/firestore dicts
    - batch_size: BigQuery recommends batching
    """
    if not data_from_scraper:
        print("No item to write to BigQuery")
        return

    # Normalize + drop rows missing required keys (usually code + crawl_date)
    normalized: list[dict] = []
    dropped = 0
    for item in data_from_scraper:
        row = _normalize_row(item)
        if not row.get("code") or not row.get("crawl_date"):
            dropped += 1
            continue
        normalized.append(row)

    if not normalized:
        print(f"⚠️ After normalization, 0 rows left (dropped {dropped}).")
        return

    total = len(normalized)
    print(f"🧾 BigQuery insert: {total} rows → {table_id} (dropped {dropped})")

    # Batch insert
    inserted = 0
    for start in range(0, total, batch_size):
        batch = normalized[start : start + batch_size]
        errors = client.insert_rows_json(table_id, batch)

        if errors:
            print(f"❌ BigQuery insert errors in batch {start}-{start+len(batch)-1}:")
            for e in errors[:10]:
                print(e)

            # Error raiser
            raise RuntimeError(f"BigQuery insert failed with {len(errors)} errors")
        inserted += len(batch)

    print(f"✅ BigQuery inserted {inserted}/{total} rows.")

def write_to_big_query_df(
        df,
        *,
        batch_size: int = 500,  
    ):
    """
    Takes a pandas DataFrame (from scraper) and inserts into BigQuery.
    Expected DF columns (can be a superset):
      "Crawl Date", "Code", "Company", "Ex Date", "Pay Date",
      "Amount", "Franking", "Yield", "Price", "4W Volume", "Total Value", "last_updated"
    """
    if df is None or df.empty:
        print("⚠️ DataFrame is empty. Nothing to write to BigQuery.")
        return

    # Replace NaN with None so your converters behave properly
    df = df.where(pd.notnull(df), None)

    # Convert DF to list[dict]
    records: list[dict] = df.to_dict(orient="records")

    # Reuse your existing list[dict] writer
    write_to_big_query(records, batch_size=batch_size)
