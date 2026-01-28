from app.scraper_functions import scraper

def test_scraper_function():
    results = scraper()

    if results:
        print("Successfully scrape data from asx-upcoming-dividends")
        return True
    else:
        print("Error ")