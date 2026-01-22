import asyncio
import pandas as pd
import sys
import io
import os
import random
from pathlib import Path
from datetime import datetime
from app.scraper_functions import scraper
from app.firebase_functions import upload_to_firebase, fetch_data_from_firebase
from app.sheet_functions import update_sheet
from app.bigquery_functions import upload_to_bigquery

today_str = datetime.now().isoformat()

async def main():
    # 1. Run Scraper
    data_results = await scraper()
    
    if data_results:
        today_str = datetime.now().strftime("%Y-%m-%d")

        # 2. Upload data crawled to Firebase
        upload_to_firebase(data_results, today_str)

        # 3. Upload data crawled to BigQuery
        upload_to_bigquery(data_results, today_str)
        
        # 4. Fetch data from Firebase and push to Google Sheet
        data_from_firebase = fetch_data_from_firebase(today_str)
        update_sheet(data_from_firebase)
    else:
        print("Scraper returned no results.")

if __name__ == "__main__":
    asyncio.run(main())