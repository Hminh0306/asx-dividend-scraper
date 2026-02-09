import asyncio
from datetime import datetime
from app.scraper_functions import scraper
from app.redshift_functions import upload_to_redshift, upload_to_s3
from app.export_functions import export_to_downloads

today_str = datetime.now().isoformat()

async def main():
    # 1. Run Scraper
    data_results = await scraper()
    
    if data_results:
        # export_to_downloads(data_results)

        upload_to_s3(data_results)

        
if __name__ == "__main__":
    asyncio.run(main())