import asyncio
from app.scraper_functions import scraper

# Main function for scraping, write to database and display on Google Sheet
async def main():
    results = await scraper()
    print(type(results))
    print(results)

if __name__ == "__main__":
    asyncio.run(main())