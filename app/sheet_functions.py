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
TAB_NAME=os.getenv("SHEET_TAB", "Sheet1")
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

def overwrite_sheet_with_df(df: pd.DataFrame):
    ws = get_worksheet()
    values = [df.columns.tolist()] + df.astype(object).where(pd.notnull(df), "").values.tolist()
    ws.clear()
    ws.update(values, value_input_option="RAW")
