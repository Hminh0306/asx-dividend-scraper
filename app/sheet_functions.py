import os
from pathlib import Path
import pandas as pd
import gspread
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv(Path(__file__).resolve().parent / ".env")

"""
    Python file for Google Sheet modification functions
"""
SHEET_ID=os.getenv("SHEET_ID")
TAB_NAME=os.getenv("SHEET_TAB", "ASX-DIVIDEND-DAILY-REPORT")
CREDS_PATH=os.getenv("GOOGLE_CREDS", "./service_account.json")

def get_worksheet():
    sheet_id = os.getenv("SHEET_ID")
    tab_name = os.getenv("SHEET_TAB", "Sheet1")
    creds_path = os.getenv("GOOGLE_CREDS", "./service_account.json")

    if not sheet_id:
        raise RuntimeError("Missing SHEET_ID in .env")
    if not os.path.exists(creds_path):
        raise RuntimeError(f"Google creds file not found: {creds_path}")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # Authorize credendials to Google Sheet
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    gc = gspread.authorize(creds)

    # 
    sh = gc.open_by_key(sheet_id)
    try:
        ws = sh.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=1000, cols=30)
    return ws

def update_sheet(data_from_bigquery: list[dict]):
    if not data_from_bigquery:
        print("⚠️ No data provided to update_sheet().")
        return

    ws = get_worksheet()

    # Extract crawl_date before dropping columns
    crawl_date = data_from_bigquery[0].get("crawl_date", "N/A")
    df = pd.DataFrame(data_from_bigquery)

    # Drop unnecessary columns
    drop_cols = ["crawl_date", "last_update"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Sort by Ex Date (Stable sort to maintain order if dates are identical)
    if "ex_date" in df.columns:
        df["ex_date_dt"] = pd.to_datetime(df["ex_date"], errors="coerce")
        df = df.sort_values("ex_date_dt", ascending=True, kind="stable")
        df = df.drop(columns=["ex_date_dt"])
    
    # Matching columns between BigQuery and Google Sheet
    rename_map = {
            "code": "Code",
            "company": "Company",
            "ex_date": "Ex Date",
            "pay_date": "Pay Date",
            "amount": "Amount",
            "franking": "Franking",
            "yield": "Yield",
            "price": "Price",
            "4w_volume": "4W Volume",
            "total_value": "Total Value"
        }


    preferred_order = [
        "Code",
        "Company",
        "Ex Date",
        "Pay Date",
        "Amount",
        "Franking",
        "Yield",
        "Price",
        "4W Volume",
        "Total Value"
    ]

    # Rename and reorder
    df = df.rename(columns=rename_map)
    ordered_cols = [c for c in preferred_order if c in df.columns]
    df = df[ordered_cols]

    # Cleanup NaN/ None
    df = df.where(pd.notnull(df), "")

    # Prepare and write data
    table_values = [df.columns.tolist()] + df.values.tolist()

    # Only change from column A to column J
    ws.batch_clear(["A:J"])

    # Header info
    ws.update("A1", [[f"Crawl Date: {crawl_date}"]], value_input_option="RAW")
    ws.format("A1", {"textFormat": {"bold": True}})

    # Table starts at A3
    # Only clear/ write from A:J, NEVER TOUCH K+
    start_row = 3
    end_row = start_row + len(table_values) - 1

    # Write the table strictly from A:J
    ws.update(f"A{start_row}:J{end_row}", table_values, value_input_option="RAW")
    
    print(f"[GOOGLE SHEET] ✅ Google Sheet updated with {len(df)} rows.")