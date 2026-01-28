import asyncio
import pandas as pd
import sys
import io
import os
import random
from pathlib import Path
from datetime import datetime
from app.scraper_functions import scraper
from app.sheet_functions import update_sheet
from app.bigquery_functions import upload_to_bigquery, fetch_latest_data_from_bq

today_str = datetime.now().isoformat()

async def main():
    # 1. Run Scraper
    data_results = await scraper()
    
    if data_results:
        today_data = datetime.now()

        upload_to_bigquery(data_results, today_str)
        
        # 3. Fetch data from Firebase and push to Google Sheet
        latest_data_from_bq = fetch_latest_data_from_bq(today_data)

        # 4. Update sheet with latest data
        update_sheet(latest_data_from_bq)
    else:
        print("Scraper returned no results.")

if __name__ == "__main__":
    asyncio.run(main())