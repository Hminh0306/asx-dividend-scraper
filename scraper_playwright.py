import asyncio
from datetime import datetime
from app.scraper_functions import scraper
from app.redshift_functions import update_to_redshift

today_str = datetime.now().isoformat()

async def main():
    # 1. Run Scraper
    data_results = await scraper()
    
    if data_results:
        # 2. Update data on redshift
        update_to_redshift(data_results)

if __name__ == "__main__":
    asyncio.run(main())