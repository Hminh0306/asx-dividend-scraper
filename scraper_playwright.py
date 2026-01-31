import asyncio
from datetime import datetime
from pathlib import Path
from datetime import datetime
from app.scraper_functions import scraper
from app.redshift_functions import update_to_redshift, fetch_latest_data_from_redshift
from app.sheet_functions import update_sheet

today_str = datetime.now().isoformat()

async def main():
    # 1. Run Scraper
    data_results = await scraper()
    
    if data_results:
        # 2. Update data on redshift
        update_to_redshift(data_results)

        # 3. Get data from redshift and update to Google Sheet
        fetched_data = fetch_latest_data_from_redshift(datetime.now())

        # 4. Update on some visualisation
        update_sheet(fetched_data)

if __name__ == "__main__":
    asyncio.run(main())