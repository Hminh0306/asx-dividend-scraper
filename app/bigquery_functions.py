from __future__ import annotations

import os
from datetime import datetime, date
from typing import Any, Optional, List, Dict

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.getenv("BQ_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID")
MAIN_TABLE = os.getenv("BQ_MAIN_TABLE_ID")
STAGING_TABLE = os.getenv("BQ_STAGING_TABLE_ID")

client = bigquery.Client(project=PROJECT_ID)
main_table_id = f"{PROJECT_ID}.{DATASET_ID}.{MAIN_TABLE}"
staging_table_id = f"{PROJECT_ID}.{DATASET_ID}.{STAGING_TABLE}"


# ---------- Helpers ----------
def _to_date(value: Any) -> Optional[str]:
    if value in (None, "", "N/A"):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date().isoformat()
        except ValueError:
            return None
    return None


def _to_timestamp(value: Any) -> Optional[datetime]:
    """
    Return a timezone-aware datetime (UTC) for BigQuery TIMESTAMP columns.
    """
    if value in (None, "", "N/A"):
        return None

    # Firestore Timestamp often has isoformat()
    if hasattr(value, "to_datetime"):
        try:
            value = value.to_datetime()
        except Exception:
            pass

    if isinstance(value, datetime):
        # Make it UTC-aware if naive
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.now().astimezone().tzinfo).astimezone(
                datetime.timezone.utc  # type: ignore[attr-defined]
            )
        return value.astimezone(datetime.timezone.utc)  # type: ignore[attr-defined]

    if isinstance(value, str):
        s = value.strip()
        # Accept "2026-01-18 19:04:13+00:00" or RFC3339
        try:
            dt = pd.to_datetime(s, utc=True, errors="coerce")
            if pd.isna(dt):
                return None
            return dt.to_pydatetime()
        except Exception:
            return None

    if hasattr(value, "isoformat"):
        try:
            s = value.isoformat()
            dt = pd.to_datetime(s, utc=True, errors="coerce")
            if pd.isna(dt):
                return None
            return dt.to_pydatetime()
        except Exception:
            return None

    return None


def _to_float(value: Any) -> Optional[float]:
    if value in (None, "", "N/A"):
        return None
    try:
        return float(value)
    except Exception:
        if isinstance(value, str):
            s = value.strip()
            # "1,23" -> 1.23 ; "1,234.56" -> 1234.56
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

def _normalize_row(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map scraper keys -> BigQuery table schema keys.

    BigQuery schema:
      crawl_date    DATE        REQUIRED
      code          STRING      REQUIRED
      company       STRING
      ex_date       DATE
      pay_date      DATE
      amount        FLOAT
      franking      FLOAT
      yield         FLOAT
      price         FLOAT
      4w_volume     INTEGER
      total_value   FLOAT
      last_update   TIMESTAMP   REQUIRED
    """
    crawl_date = _to_date(item.get("Crawl Date"))
    code = item.get("Code")

    return {
        "crawl_date": crawl_date,  # python date
        "code": str(code) if code is not None else None,
        "company": item.get("Company"),
        "ex_date": _to_date(item.get("Ex Date")),
        "pay_date": _to_date(item.get("Pay Date")),
        "amount": _to_float(item.get("Amount")),
        "franking": _to_float(item.get("Franking")),
        "yield": _to_float(item.get("Yield")),
        "price": _to_float(item.get("Price")),
        "4w_volume": _to_int(item.get("4W Volume")),     
        "total_value": _to_float(item.get("Total Value")),
        "last_update": _to_timestamp(item.get("last_updated")),  
    }


# ---------- Main ----------
def upload_to_bigquery(data_crawled: List[Dict[str, Any]], today_str: str) -> None:
    """
    Loads data into BigQuery using load_table_from_dataframe (free-tier friendly).
    - Appends rows
    - Uses an explicit schema to avoid dtype inference problems
    """
    if not data_crawled:
        print("⚠️ No data to upload_to_bigquery()")
        return

    rows: List[Dict[str, Any]] = []
    dropped = 0

    for item in data_crawled:
        r = _normalize_row(item)

        # REQUIRED fields
        if not r.get("crawl_date") or not r.get("code"):
            dropped += 1
            continue

        # last_update is REQUIRED in your schema — ensure it exists
        # if missing, use "now" in UTC
        if r.get("last_update") is None:
            r["last_update"] = pd.Timestamp.utcnow().to_pydatetime()

        rows.append(r)

    if not rows:
        print(f"⚠️ After normalization, 0 rows left (dropped {dropped}).")
        return

    df = pd.DataFrame(rows)

    # Ensure pandas dtypes match schema expectations
    # DATE columns: python date objects are fine
    for c in ("crawl_date", "ex_date", "pay_date"):
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.date

    # INTEGER column
    if "4w_volume" in df.columns:
        df["4w_volume"] = pd.to_numeric(df["4w_volume"], errors="coerce").astype("Int64")

    # TIMESTAMP column
    if "last_update" in df.columns:
        df["last_update"] = pd.to_datetime(df["last_update"], utc=True, errors="coerce")

    print(f"📦 BigQuery load: {len(df)} rows → {main_table_id} (dropped {dropped})")

    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("crawl_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("code", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("company", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("ex_date", "DATE", mode="NULLABLE"),
            bigquery.SchemaField("pay_date", "DATE", mode="NULLABLE"),
            bigquery.SchemaField("amount", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("franking", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("yield", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("price", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("4w_volume", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("total_value", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("last_update", "TIMESTAMP", mode="REQUIRED"),
        ],
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    load_job = client.load_table_from_dataframe(df, main_table_id, job_config=job_config)
    load_job.result()  # wait

    print(f"✅ BigQuery load job completed at {datetime.now()}.")

def merge_to_bigquery(data_crawled: list[dict]):
    """
    1) Load current run into STAGING (truncate staging)
    2) MERGE STAGING into MAIN on (crawl_date, code)
       - MATCHED => UPDATE
       - NOT MATCHED => INSERT
    """
    if not data_crawled:
        print("⚠️ No data to merge_to_bigquery()")
        return

    rows = []
    dropped = 0
    for item in data_crawled:
        r = _normalize_row(item)
        if not r["crawl_date"] or not r["code"]:
            dropped += 1
            continue
        rows.append(r)

    if not rows:
        print(f"⚠️ After normalization, 0 rows left (dropped {dropped}).")
        return

    df = pd.DataFrame(rows)

    # Ensure pandas dtypes align for BigQuery load
    df["crawl_date"] = pd.to_datetime(df["crawl_date"]).dt.date
    df["ex_date"] = pd.to_datetime(df["ex_date"]).dt.date
    df["pay_date"] = pd.to_datetime(df["pay_date"]).dt.date
    df["last_update"] = pd.to_datetime(df["last_update"], utc=True, errors="coerce")

    print(f"📦 Loading {len(df)} rows into staging: {staging_table_id} (dropped {dropped})")

    load_cfg = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # staging is "this run only"
    )
    client.load_table_from_dataframe(df, staging_table_id, job_config=load_cfg).result()

    merge_sql = f"""
    MERGE `{main_table_id}` T
    USING `{staging_table_id}` S
    ON T.crawl_date = S.crawl_date AND T.code = S.code
    WHEN MATCHED THEN UPDATE SET
      company = S.company,
      ex_date = S.ex_date,
      pay_date = S.pay_date,
      amount = S.amount,
      franking = S.franking,
      yield = S.yield,
      price = S.price,
      `4w_volume` = S.`4w_volume`,
      total_value = S.total_value,
      last_update = S.last_update
    WHEN NOT MATCHED THEN
      INSERT (crawl_date, code, company, ex_date, pay_date, amount, franking, yield, price, `4w_volume`, total_value, last_update)
      VALUES (S.crawl_date, S.code, S.company, S.ex_date, S.pay_date, S.amount, S.franking, S.yield, S.price, S.`4w_volume`, S.total_value, S.last_update)
    """

    print("🔁 Running MERGE into main table…")
    client.query(merge_sql).result()
    print(f"✅ MERGE complete: staging → {main_table_id}")

# ---------- Connection ----------
def test_bq_connection():
    client = bigquery.Client()
    if client:
        print(f"✅ Successfully connect to BigQuery on project {client.project}")
    