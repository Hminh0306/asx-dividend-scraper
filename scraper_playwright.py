import asyncio
from datetime import datetime
from app.scraper_functions import scraper
from app.redshift_functions import upload_to_redshift, upload_to_s3
from app.api.trigger import notify_frontend_for_refresh

today_str = datetime.now().isoformat()

async def main():
    # 1. Run Scraper
    data_results = await scraper()
    
    if data_results:
        # 2. Upload data to Redshift
        upload_to_redshift(data_results)

        # 3. Upload data to S3 Bucket
        upload_to_s3(data_results)

        # 4. Send signal through REST API
        # notify_frontend_for_refresh()

if __name__ == "__main__":
    asyncio.run(main())