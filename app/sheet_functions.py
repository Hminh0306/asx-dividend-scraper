import os
from pathlib import Path
import pandas as pd
import gspread
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

def update_sheet(data_from_firebase):
    if not data_from_firebase:
        print("⚠️ No data provided to update_sheet().")
        return

    ws = get_worksheet()

    crawl_date = data_from_firebase[0].get("Crawl Date", "")

    df = pd.DataFrame(data_from_firebase)

    # Remove Crawl Date from the table
    if "Crawl Date" in df.columns:
        df = df.drop(columns=["Crawl Date"])

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
        "Total Value",
        "last_updated",
    ]

    ordered_cols = (
        [c for c in preferred_order if c in df.columns]
        + [c for c in df.columns if c not in preferred_order]
    )
    df = df[ordered_cols]

    if "Code" in df.columns:
        df = df.sort_values("Code", kind="stable")

    # Keep numbers as numbers; replace NaN/None with ""
    df = df.where(pd.notnull(df), "")

    table_values = [df.columns.tolist()] + df.values.tolist()

    ws.clear()

    # Crawl Date box
    ws.update("A1", [[f"Crawl Date: {crawl_date}"]], value_input_option="RAW")
    ws.format("A1", {"textFormat": {"bold": True}})

    # Table starts at A3
    start_row = 3
    ws.resize(rows=start_row + len(table_values), cols=len(table_values[0]) if table_values else 1)
    ws.update(f"A{start_row}", table_values, value_input_option="RAW")

    print(f"✅ Google Sheet updated with {len(df)} rows.")