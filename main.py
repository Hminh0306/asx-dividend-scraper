import asyncio
# Import both functions from your module
from app.scraper_functions import scraper
from app.export_functions import save_to_db

async def main():
    print("Scraping started...")
    results = await scraper()
    
    print(f"Data type: {type(results)}")
    
    if results:
        # Now Python knows where to find save_to_db
        save_to_db(results)
    else:
        print("Scraper returned no data.")

if __name__ == "__main__":
    asyncio.run(main())